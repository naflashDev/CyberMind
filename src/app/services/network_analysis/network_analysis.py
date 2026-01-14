import socket
import ipaddress
from typing import List, Dict, Optional
import shutil
import subprocess
import xml.etree.ElementTree as ET
from typing import Tuple
from loguru import logger

# Common ports and heuristic service names
COMMON_PORTS = {
    21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp', 53: 'dns', 69: 'tftp',
    80: 'http', 110: 'pop3', 143: 'imap', 443: 'https', 3306: 'mysql',
    3389: 'rdp', 8080: 'http-alt', 5900: 'vnc'
}

# Detailed metadata for common ports: service name and common connection methods/protocols
COMMON_PORTS_DETAILS = {
    21: {"service": "ftp", "methods": ["FTP"]},
    22: {"service": "ssh", "methods": ["SSH", "SFTP"]},
    23: {"service": "telnet", "methods": ["Telnet"]},
    25: {"service": "smtp", "methods": ["SMTP"]},
    53: {"service": "dns", "methods": ["DNS"]},
    69: {"service": "tftp", "methods": ["TFTP"]},
    80: {"service": "http", "methods": ["HTTP"]},
    110: {"service": "pop3", "methods": ["POP3"]},
    143: {"service": "imap", "methods": ["IMAP"]},
    443: {"service": "https", "methods": ["HTTPS"]},
    3306: {"service": "mysql", "methods": ["MySQL"]},
    3389: {"service": "rdp", "methods": ["RDP"]},
    8080: {"service": "http-alt", "methods": ["HTTP"]},
    5900: {"service": "vnc", "methods": ["VNC"]},
}


def _is_valid_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except Exception:
        return False


def scan_ports(host: str, ports: Optional[List[int]] = None, timeout: float = 0.5) -> List[Dict]:
    """Scan a list of ports on a host and return friendly results.

    This function performs TCP connect attempts with a short timeout.
    It is intentionally simple (no raw sockets, no OS-specific features).
    """
    logger.info("scan_ports called: host={}, ports={}, timeout={}", host, ports, timeout)
    if not host:
        logger.error("scan_ports: missing host")
        raise ValueError("Host is required")

    # allow hostnames as well; validation best-effort
    if not _is_valid_ip(host):
        # allow DNS names (we won't raise for non-IP); socket will resolve
        pass

    if ports is None:
        ports = list(COMMON_PORTS.keys())

    results = []
    for p in ports:
        try:
            with socket.create_connection((host, p), timeout=timeout):
                # connected
                results.append({
                    'port': p,
                    'open': True,
                    'service': COMMON_PORTS.get(p, 'unknown')
                })
                logger.debug("scan_ports: host={} port={} open=True", host, p)
        except Exception:
            results.append({
                'port': p,
                'open': False,
                'service': COMMON_PORTS.get(p, 'unknown')
            })
            logger.debug("scan_ports: host={} port={} open=False", host, p)

    open_count = sum(1 for r in results if r.get('open'))
    logger.info("scan_ports finished: host={} scanned_ports={} open_ports={}", host, len(results), open_count)
    return results


def run_nmap_scan(host: str, ports: Optional[List[int]] = None, timeout: int = 120) -> Tuple[List[Dict], str]:
    """Run nmap -sV against the host and parse results.

    Returns a tuple (results_list, raw_xml) where results_list contains dicts with
    port, open (bool), service, product, version, methods (from COMMON_PORTS_DETAILS), vulnerabilities (empty list).
    Raises FileNotFoundError if `nmap` binary not found.
    """
    logger.info("run_nmap_scan called: host={} ports={} timeout={}", host, ports, timeout)
    nmap_path = shutil.which("nmap")
    if not nmap_path:
        logger.warning("run_nmap_scan: nmap not found in PATH; cannot run nmap")
        raise FileNotFoundError("nmap not found in PATH")

    args = [nmap_path, "-sV", "-oX", "-", host]
    # if specific ports provided, pass -p
    if ports:
        args = [nmap_path, "-sV", "-oX", "-", "-p", ",".join(str(p) for p in ports), host]

    logger.debug("run_nmap_scan: executing: {}", args)
    proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    raw = proc.stdout or proc.stderr or ""
    logger.debug("run_nmap_scan: nmap returncode={} output_len={}", proc.returncode, len(raw))

    results = []
    try:
        root = ET.fromstring(raw)
        for host_el in root.findall('host'):
            ports_el = host_el.find('ports')
            if ports_el is None:
                continue
            for port_el in ports_el.findall('port'):
                portid = int(port_el.get('portid'))
                protocol = port_el.get('protocol')
                state_el = port_el.find('state')
                state = state_el.get('state') if state_el is not None else 'unknown'
                service_el = port_el.find('service')
                service = service_el.get('name') if service_el is not None else None
                product = service_el.get('product') if service_el is not None else None
                version = service_el.get('version') if service_el is not None else None
                methods = COMMON_PORTS_DETAILS.get(portid, {}).get('methods', [])
                results.append({
                    'port': portid,
                    'protocol': protocol,
                    'open': state == 'open',
                    'state': state,
                    'service': service or COMMON_PORTS.get(portid, 'unknown'),
                    'product': product,
                    'version': version,
                    'methods': methods,
                    'vulnerabilities': []
                })
                logger.debug("run_nmap_scan: parsed port={} open={} service={} product={} version={}", portid, state, service, product, version)
    except ET.ParseError:
        # if XML parsing fails, fall back to empty results and include raw output
        logger.warning("run_nmap_scan: failed to parse nmap XML output")
        pass

    # If no ports parsed (old nmap output format), attempt simple parsing (best-effort)
    if not results and raw:
        # naive fallback: look for lines like 'PORT   STATE SERVICE'
        lines = raw.splitlines()
        started = False
        for ln in lines:
            if ln.strip().startswith('PORT'):
                started = True
                continue
            if not started:
                continue
            parts = ln.split()
            if len(parts) >= 3:
                try:
                    port_part = parts[0]
                    portnum = int(port_part.split('/')[0])
                    state = parts[1]
                    service = parts[2]
                    methods = COMMON_PORTS_DETAILS.get(portnum, {}).get('methods', [])
                    results.append({
                        'port': portnum,
                        'protocol': port_part.split('/')[1] if '/' in port_part else 'tcp',
                        'open': state == 'open',
                        'state': state,
                        'service': service,
                        'product': None,
                        'version': None,
                        'methods': methods,
                        'vulnerabilities': []
                    })
                    logger.debug("run_nmap_scan: fallback parsed port={} open={} service={}", portnum, state, service)
                except Exception:
                    continue

    logger.info("run_nmap_scan finished: host={} parsed_ports={}", host, len(results))
    return results, raw
