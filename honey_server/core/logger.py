"""
Attack Logger for the Honeypot Server.
Logs to local file AND to the Monitor Server via HTTP POST.
"""
import logging
import httpx
import asyncio
import os
from datetime import datetime

# ─── Local file logging ───────────────────────────────────────────────────────
_logger = logging.getLogger("honeypot")
_logger.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

_fh = logging.FileHandler("honey_attack.log", encoding="utf-8")
_fh.setFormatter(_fmt)
_logger.addHandler(_fh)

_ch = logging.StreamHandler()
_ch.setFormatter(_fmt)
_logger.addHandler(_ch)

# ─── Monitor Server endpoint ──────────────────────────────────────────────────
MONITOR_URL = os.environ.get("MONITOR_URL", "http://monitor-server:9000")
LOG_SECRET  = os.environ.get("LOG_SECRET",  "honey_internal_secret")

def log_attack(ip: str, endpoint: str, attack_type: str, payload: str):
    """
    Logs an attack locally and forwards it to the Monitor Server.
    """
    msg = f"[ATTACK DETECTED] IP: {ip} | Endpoint: {endpoint} | Type: {attack_type} | Payload: {payload}"
    _logger.warning(msg)

    # Fire-and-forget to monitor server
    asyncio.ensure_future(_forward_log(ip, endpoint, attack_type, payload))

async def _forward_log(ip: str, endpoint: str, attack_type: str, payload: str):
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            await client.post(
                f"{MONITOR_URL}/api/ingest",
                headers={"X-Log-Secret": LOG_SECRET},
                json={
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3],
                    "ip": ip,
                    "endpoint": endpoint,
                    "type": attack_type,
                    "payload": payload
                }
            )
    except Exception:
        pass  # Silent fail - local log is the fallback

def log_info(msg: str):
    _logger.info(msg)
