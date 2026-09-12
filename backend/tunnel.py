import asyncio
import logging
import os
import re
import shutil
from typing import Optional

logger = logging.getLogger("botdz.tunnel")

_tunnel_proc: Optional[asyncio.subprocess.Process] = None
_tunnel_url: Optional[str] = None
_stream_tasks = []


def find_cloudflared() -> Optional[str]:
    """Finds the cloudflared executable in PATH or standard installation directories."""
    path = shutil.which("cloudflared")
    if path:
        return path

    standard_paths = [
        r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
        r"C:\Program Files\cloudflared\cloudflared.exe",
        os.path.expanduser(r"~\cloudflared.exe"),
        os.path.expanduser(r"~\scoop\apps\cloudflared\current\cloudflared.exe"),
    ]
    for sp in standard_paths:
        if os.path.isfile(sp):
            return sp

    return None


async def start_tunnel(port: int, timeout: float = 20.0) -> Optional[str]:
    """
    Launches an HTTPS tunnel pointing to localhost:{port}.
    Falls back to Cloudflare Tunnel.
    """
    global _tunnel_proc, _tunnel_url, _stream_tasks

    binary = find_cloudflared()
    if not binary:
        logger.info("Cloudflared not available. Running without public HTTPS tunnel.")
        return None

    logger.info(f"Starting Cloudflare Quick Tunnel for port {port} via {binary}...")
    try:
        proc = await asyncio.create_subprocess_exec(
            binary, "tunnel",
            "--protocol", "http2",
            "--edge-ip-version", "4",
            "--retries", "10",
            "--url", f"http://127.0.0.1:{port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _tunnel_proc = proc
    except Exception as e:
        logger.warning(f"Failed to spawn cloudflared process: {e}")
        return None

    url_event = asyncio.Event()
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    async def drain_stream(stream):
        global _tunnel_url
        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                text = line.decode("utf-8", errors="replace")
                if not _tunnel_url:
                    match = url_pattern.search(text)
                    if match:
                        _tunnel_url = match.group(0)
                if _tunnel_url and not url_event.is_set():
                    if "precheck complete" in text or "metrics server" in text:
                        await asyncio.sleep(2)
                        url_event.set()
        except Exception:
            pass

    t1 = asyncio.create_task(drain_stream(proc.stdout))
    t2 = asyncio.create_task(drain_stream(proc.stderr))
    _stream_tasks = [t1, t2]

    try:
        await asyncio.wait_for(url_event.wait(), timeout=timeout)
        logger.info(f"🌐 Cloudflare Tunnel online: {_tunnel_url}")
        return _tunnel_url
    except asyncio.TimeoutError:
        if _tunnel_url:
            logger.info(f"🌐 Cloudflare Tunnel online (post-timeout): {_tunnel_url}")
            return _tunnel_url
        logger.warning("Timed out waiting for Cloudflare Tunnel URL to appear.")
        return None


async def stop_tunnel():
    """Terminates the cloudflared subprocess cleanly."""
    global _tunnel_proc, _tunnel_url, _stream_tasks
    if _tunnel_proc:
        try:
            _tunnel_proc.terminate()
            await _tunnel_proc.wait()
            logger.info("Cloudflare Tunnel terminated.")
        except Exception as e:
            logger.debug(f"Note on terminating tunnel: {e}")
        finally:
            _tunnel_proc = None
            _tunnel_url = None

    for t in _stream_tasks:
        if not t.done():
            t.cancel()
    _stream_tasks.clear()


def get_tunnel_url() -> Optional[str]:
    """Returns the current active tunnel URL, if any."""
    return _tunnel_url
