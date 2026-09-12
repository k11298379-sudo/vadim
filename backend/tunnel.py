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


def find_ngrok() -> Optional[str]:
    """Finds the ngrok executable in PATH or standard installation directories."""
    path = shutil.which("ngrok")
    if path:
        return path
    local_path = os.path.abspath("ngrok.exe")
    if os.path.isfile(local_path):
        return local_path
    winget_paths = [
        os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"),
        r"C:\Program Files\ngrok\ngrok.exe",
    ]
    for p in winget_paths:
        if os.path.isfile(p):
            return p
    return None


async def start_ngrok(port: int, timeout: float = 12.0) -> Optional[str]:
    """
    Launches ngrok HTTP tunnel pointing to localhost:{port}.
    Queries ngrok local API at http://127.0.0.1:4040/api/tunnels to get the public HTTPS URL.
    """
    global _tunnel_proc, _tunnel_url
    binary = find_ngrok()
    if not binary:
        return None

    logger.info(f"Checking ngrok tunnel for port {port} via {binary}...")
    try:
        proc = await asyncio.create_subprocess_exec(
            binary, "http", str(port), "--log=stdout", "--log-format=json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except Exception as e:
        logger.debug(f"Could not launch ngrok: {e}")
        return None

    import httpx
    async with httpx.AsyncClient(timeout=2.0) as client:
        for _ in range(int(timeout * 2)):
            if proc.returncode is not None:
                return None
            try:
                resp = await client.get("http://127.0.0.1:4040/api/tunnels")
                if resp.status_code == 200:
                    data = resp.json()
                    tunnels = data.get("tunnels", [])
                    for t in tunnels:
                        public_url = t.get("public_url", "")
                        if public_url.startswith("https://"):
                            _tunnel_proc = proc
                            _tunnel_url = public_url
                            logger.info(f"🚀 ngrok tunnel online: {_tunnel_url}")
                            return _tunnel_url
            except Exception:
                pass
            await asyncio.sleep(0.5)

    try:
        proc.terminate()
    except Exception:
        pass
    return None


async def start_tunnel(port: int, timeout: float = 20.0) -> Optional[str]:
    """
    Launches an HTTPS tunnel pointing to localhost:{port}.
    Tries ngrok first for rock-solid stability; falls back to Cloudflare Tunnel.
    """
    global _tunnel_proc, _tunnel_url, _stream_tasks

    # 1. Try ngrok first
    ngrok_url = await start_ngrok(port)
    if ngrok_url:
        return ngrok_url

    # 2. Fallback to Cloudflare Quick Tunnel
    binary = find_cloudflared()
    if not binary:
        logger.info("Neither ngrok nor cloudflared available. Running without public HTTPS tunnel.")
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
