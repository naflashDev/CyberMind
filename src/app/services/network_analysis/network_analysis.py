import socket
import errno
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
                    'state': 'open',
                    'service': COMMON_PORTS.get(p, 'unknown')
                })
                logger.debug("scan_ports: host={} port={} open=True", host, p)
        except Exception as e:
            # Distinguish connection refused (closed) vs timeout/no-response (filtered)
            state = 'filtered'
            try:
                if isinstance(e, socket.timeout):
                    state = 'filtered'
                elif isinstance(e, ConnectionRefusedError):
                    state = 'closed'
                elif isinstance(e, OSError) and getattr(e, 'errno', None) == errno.ECONNREFUSED:
                    state = 'closed'
            except Exception:
                state = 'unknown'

            results.append({
                'port': p,
                'open': False,
                'state': state,
                'service': COMMON_PORTS.get(p, 'unknown')
            })
            logger.debug("scan_ports: host={} port={} open=False state={}", host, p, state)

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


async def scan_range(cidr: Optional[str] = None,
                     start: Optional[str] = None,
                     end: Optional[str] = None,
                     ports: Optional[List[int]] = None,
                     timeout: Optional[float] = 0.5,
                     use_nmap: bool = True,
                     concurrency: int = 20,
                     max_allowed: int = 1024) -> Dict:
    """Scan a range of hosts defined by CIDR or start/end IPs.

    This function is async and will run blocking scans in threads.
    Returns a dict with keys: `scanned`, `hosts` (list of per-host dicts), `duration_seconds`.
    Raises ValueError on invalid inputs (caller should translate to HTTP errors).
    """
    import asyncio
    import time
    import subprocess

    # build list of hosts
    hosts = []
    if not cidr and not start:
        raise ValueError("Provide `cidr` or `start` (and optional `end`) for range scan")

    try:
        # Prefer explicit start/end when provided by the caller. If `start` is
        # present we build the range from `start` to `end` (inclusive). Only
        # when `start` is not provided do we fall back to interpreting `cidr`.
        if start:
            start_ip = ipaddress.ip_address(start)
            if end:
                end_ip = ipaddress.ip_address(end)
            else:
                end_ip = start_ip
            if int(end_ip) < int(start_ip):
                raise ValueError("`end` must be >= `start`")
            hosts = [str(ipaddress.ip_address(i)) for i in range(int(start_ip), int(end_ip) + 1)]
        elif cidr:
            net = ipaddress.ip_network(cidr, strict=False)
            hosts = [str(h) for h in net.hosts()]
    except ValueError as e:
        raise ValueError(f"invalid IP/CIDR: {e}")

    if len(hosts) > max_allowed:
        raise ValueError(f"range too large ({len(hosts)} hosts). Max allowed is {max_allowed}")

    # prepare timeouts and concurrency
    try:
        if timeout is None:
            timeout_sec = 120
        else:
            tval = float(timeout)
            timeout_sec = int(tval) if tval >= 1 else 120
    except Exception:
        timeout_sec = 120

    conc = int(concurrency) if concurrency and int(concurrency) > 0 else 10
    semaphore = asyncio.Semaphore(conc)

    start_all = time.monotonic()

    async def _scan_host(host: str):
        async with semaphore:
            start = time.monotonic()
            try:
                if use_nmap:
                    try:
                        results, raw = await asyncio.to_thread(run_nmap_scan, host, ports, timeout_sec)
                    except FileNotFoundError:
                        logger.warning("nmap not found; fallback TCP scan for host={}", host)
                        results = await asyncio.to_thread(scan_ports, host, ports, timeout or 0.5)
                        raw = None
                    except subprocess.TimeoutExpired:
                        logger.error("nmap timed out for host={}", host)
                        return {"host": host, "error": f"nmap timeout after {timeout_sec}s"}
                else:
                    results = await asyncio.to_thread(scan_ports, host, ports, timeout or 0.5)
                    raw = None
            except Exception as e:
                logger.exception("scan_host failed for {}: {}", host, e)
                return {"host": host, "error": str(e)}
            duration = time.monotonic() - start
            return {"host": host, "results": results, "raw": raw, "duration_seconds": round(duration, 2)}

    tasks = [asyncio.create_task(_scan_host(h)) for h in hosts]
    gathered = await asyncio.gather(*tasks)

    total_duration = time.monotonic() - start_all
    return {"scanned": len(hosts), "hosts": gathered, "duration_seconds": round(total_duration, 2)}
