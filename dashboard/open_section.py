"""Open a dashboard section in the browser, starting a local server if needed."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = {
    "overview": "overview",
    "indicators": "indicators",
    "history": "history",
    "seasonality": "seasonality",
    "anomalies": "anomalies",
    "ml-evaluation": "models",
    "methods": "methodology",
}
PAGE_TITLE = b"<title>for_ecast | Brazil rainfall observatory</title>"


def is_dashboard_available(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=0.5) as response:
            return response.status == 200 and PAGE_TITLE in response.read(8192)
    except (OSError, urllib.error.URLError):
        return False


def start_server(port: int, url: str) -> None:
    creation_flags = 0
    process_options = {}
    if sys.platform == "win32":
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        process_options["start_new_session"] = True

    process = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        **process_options,
    )
    for _ in range(25):
        if is_dashboard_available(url):
            print(f"Started dashboard server on port {port} (PID {process.pid}).")
            return
        if process.poll() is not None:
            raise RuntimeError(
                f"Could not start the dashboard server on port {port}. "
                f"Choose another port with --port."
            )
        time.sleep(0.2)
    raise RuntimeError(
        f"Dashboard server did not respond on port {port}. "
        f"Choose another port with --port."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("section", choices=SECTIONS, help="Dashboard section to open")
    parser.add_argument("--port", type=int, default=8000, help="Local server port (default: 8000)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    url = f"http://127.0.0.1:{args.port}/dashboard/"
    if not is_dashboard_available(url):
        start_server(args.port, url)
    section_url = f"{url}#{SECTIONS[args.section]}"
    print(f"Opening {args.section}: {section_url}")
    if not webbrowser.open(section_url):
        print("No browser opened automatically; copy the URL above into your browser.")


if __name__ == "__main__":
    main()
