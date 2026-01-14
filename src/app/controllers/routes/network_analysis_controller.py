from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, root_validator
from typing import List, Optional, Any, Dict
import subprocess
import time
import asyncio
import ipaddress
from loguru import logger

from app.services.network_analysis.network_analysis import scan_ports, run_nmap_scan, COMMON_PORTS_DETAILS

router = APIRouter(prefix="/network", tags=["network"])


class ScanRequest(BaseModel):
    host: str
    ports: Optional[List[int]] = None
    timeout: Optional[float] = 0.5
    use_nmap: Optional[bool] = True

    @root_validator(pre=True)
    def normalize_ports(cls, values: Dict[str, Any]):
        # Accept ports as comma-separated string or empty string from clients
        ports = values.get('ports', None)
        if isinstance(ports, str):
            raw = ports.strip()
            if raw == '':
                # treat empty string as omitted
                values.pop('ports', None)
            else:
                try:
                    parsed = [int(p.strip()) for p in raw.split(',') if p.strip()]
                    values['ports'] = parsed
                except Exception:
                    # leave to pydantic to validate types later
                    pass
        return values


class RangeScanRequest(BaseModel):
    # Accept either `cidr` (e.g. 192.168.1.0/28) or `start` and optional `end` (e.g. 192.168.1.1, 192.168.1.10)
    cidr: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    ports: Optional[List[int]] = None
    timeout: Optional[float] = 0.5
    use_nmap: Optional[bool] = True
    concurrency: Optional[int] = 20

    @root_validator(pre=True)
    def normalize_ports(cls, values: Dict[str, Any]):
        ports = values.get('ports', None)
        if isinstance(ports, str):
            raw = ports.strip()
            if raw == '':
                values.pop('ports', None)
            else:
                try:
                    parsed = [int(p.strip()) for p in raw.split(',') if p.strip()]
                    values['ports'] = parsed
                except Exception:
                    pass
        return values

    @root_validator(pre=True)
    def normalize_fields(cls, values: Dict[str, Any]):
        # Normalize empty strings to None for cidr/start/end and trim whitespace
        for k in ('cidr', 'start', 'end'):
            v = values.get(k, None)
            if isinstance(v, str):
                vv = v.strip()
                if vv == '':
                    values[k] = None
                else:
                    values[k] = vv

        # Concurrency may come as string from form; coerce to int when possible
        conc = values.get('concurrency', None)
        if isinstance(conc, str):
            try:
                values['concurrency'] = int(conc)
            except Exception:
                # leave as-is; later code will apply default
                pass

        return values


@router.post("/scan")
async def scan(req: ScanRequest):
    # Safety: simple validation
    if not req.host:
        raise HTTPException(status_code=400, detail="host is required")

    try:
        if getattr(req, 'use_nmap', True):
            # sanitize timeout: require a positive number >=1, otherwise use 120s default
            try:
                if req.timeout is None:
                    timeout_sec = 120
                else:
                    tval = float(req.timeout)
                    timeout_sec = int(tval) if tval >= 1 else 120
            except Exception:
                timeout_sec = 120
            start = time.monotonic()
            try:
                results, raw = run_nmap_scan(req.host, ports=req.ports, timeout=timeout_sec)
            except FileNotFoundError:
                logger.warning("nmap not available; falling back to TCP connect scan for host={}", req.host)
                results = scan_ports(req.host, ports=req.ports, timeout=req.timeout or 0.5)
                raw = None
                duration = time.monotonic() - start
                logger.info("scan fallback finished: host={} duration={}s results={}", req.host, round(duration,2), len(results))
            except subprocess.TimeoutExpired:
                logger.error("nmap scan timed out for host={} after {}s", req.host, timeout_sec)
                raise HTTPException(status_code=504, detail=f"nmap scan timed out after {timeout_sec} seconds")
            else:
                duration = time.monotonic() - start
                logger.info("nmap scan finished: host={} duration={}s parsed_ports={}", req.host, round(duration,2), len(results))
        else:
            start = time.monotonic()
            results = scan_ports(req.host, ports=req.ports, timeout=req.timeout)
            raw = None
            duration = time.monotonic() - start
            logger.info("tcp scan finished: host={} duration={}s results={}", req.host, round(duration,2), len(results))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("scan failed for host={}: {}", req.host, e)
        raise HTTPException(status_code=500, detail=f"scan failed: {e}")

    resp = {"host": req.host, "results": results, "raw": raw}
    try:
        resp["duration_seconds"] = round(duration, 2)
    except Exception:
        pass
    return resp


@router.post("/scan_range")
async def scan_range(req: RangeScanRequest, request: Request):
    # log incoming raw payload to aid debugging of 400 responses
    try:
        raw_body = await request.json()
        logger.debug("scan_range payload: {}", raw_body)
    except Exception:
        try:
            raw_text = await request.body()
            logger.debug("scan_range raw body (bytes): {}", raw_text)
        except Exception:
            logger.debug("scan_range: could not read raw request body")
    # validate input: require cidr or start
    if not req.cidr and not req.start:
        raise HTTPException(status_code=400, detail="Provide `cidr` or `start` (and optional `end`) for range scan")

    # build list of hosts
    hosts = []
    try:
        if req.cidr:
            net = ipaddress.ip_network(req.cidr, strict=False)
            hosts = [str(h) for h in net.hosts()]
        else:
            start_ip = ipaddress.ip_address(req.start)
            if req.end:
                end_ip = ipaddress.ip_address(req.end)
            else:
                end_ip = start_ip
            if int(end_ip) < int(start_ip):
                raise HTTPException(status_code=400, detail="`end` must be >= `start`")
            # create inclusive range
            hosts = [str(ipaddress.ip_address(i)) for i in range(int(start_ip), int(end_ip) + 1)]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid IP/CIDR: {e}")

    max_allowed = 1024
    if len(hosts) > max_allowed:
        raise HTTPException(status_code=400, detail=f"range too large ({len(hosts)} hosts). Max allowed is {max_allowed}")

    # prepare timeouts and concurrency
    try:
        if req.timeout is None:
            timeout_sec = 120
        else:
            tval = float(req.timeout)
            timeout_sec = int(tval) if tval >= 1 else 120
    except Exception:
        timeout_sec = 120

    concurrency = int(req.concurrency) if req.concurrency and req.concurrency > 0 else 10
    semaphore = asyncio.Semaphore(concurrency)

    start_all = time.monotonic()

    async def scan_host(host: str):
        async with semaphore:
            start = time.monotonic()
            try:
                if getattr(req, 'use_nmap', True):
                    try:
                        results, raw = await asyncio.to_thread(run_nmap_scan, host, req.ports, timeout_sec)
                    except FileNotFoundError:
                        logger.warning("nmap not found; fallback TCP scan for host={}", host)
                        results = await asyncio.to_thread(scan_ports, host, req.ports, req.timeout or 0.5)
                        raw = None
                    except subprocess.TimeoutExpired:
                        logger.error("nmap timed out for host={}", host)
                        return {"host": host, "error": f"nmap timeout after {timeout_sec}s"}
                else:
                    results = await asyncio.to_thread(scan_ports, host, req.ports, req.timeout or 0.5)
                    raw = None
            except Exception as e:
                logger.exception("scan_host failed for {}: {}", host, e)
                return {"host": host, "error": str(e)}
            duration = time.monotonic() - start
            return {"host": host, "results": results, "raw": raw, "duration_seconds": round(duration, 2)}

    tasks = [asyncio.create_task(scan_host(h)) for h in hosts]
    gathered = await asyncio.gather(*tasks)

    total_duration = time.monotonic() - start_all
    return {"scanned": len(hosts), "hosts": gathered, "duration_seconds": round(total_duration, 2)}


@router.get("/ports")
async def list_common_ports():
    # return detailed list of common ports with service and common methods
    items = []
    for port, info in COMMON_PORTS_DETAILS.items():
        items.append({
            "port": port,
            "service": info.get("service"),
            "methods": info.get("methods", [])
        })
    # sort by port number
    items = sorted(items, key=lambda x: x["port"])
    return {"common_ports": items}
