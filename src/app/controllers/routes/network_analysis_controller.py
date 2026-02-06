"""
@file network_analysis_controller.py
@author naflashDev
@brief FastAPI router for network analysis endpoints.
@details Provides endpoints for network scanning, port analysis, and integration with the network_analysis service. Handles requests for scanning ranges, running nmap, and returning port/service metadata.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from pydantic import model_validator
from typing import List, Optional, Any, Dict
import subprocess
import time
import asyncio
import ipaddress
from loguru import logger

from app.services.network_analysis.network_analysis import (
    scan_ports,
    run_nmap_scan,
    COMMON_PORTS_DETAILS,
    scan_range as service_scan_range,
)

router = APIRouter(prefix="/network", tags=["network"])


class ScanRequest(BaseModel):
    host: str
    ports: Optional[List[int]] = None
    timeout: Optional[float] = 0.5
    use_nmap: Optional[bool] = True

    @model_validator(mode="before")
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

    @model_validator(mode="before")
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

    @model_validator(mode="before")
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
        # Generic error message for UI, no internal details
        raise HTTPException(status_code=500, detail="Ha ocurrido un error interno. Por favor, contacte con el administrador.")

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

    try:
        result = await service_scan_range(
            cidr=req.cidr,
            start=req.start,
            end=req.end,
            ports=req.ports,
            timeout=req.timeout,
            use_nmap=req.use_nmap,
            concurrency=req.concurrency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("scan_range failed: {}", e)
        # Generic error message for UI, no internal details
        raise HTTPException(status_code=500, detail="Ha ocurrido un error interno. Por favor, contacte con el administrador.")

    return result


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
