"""Starts the local server and the app window. Run with run.bat or `python -m tutor`."""

import socket
import threading
import time

import uvicorn

from .paths import APP_NAME, cache_folder, data_folder
from .server import create_app
from .window import open_window

HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def _port_in_use() -> bool:
    with socket.socket() as s:
        return s.connect_ex((HOST, PORT)) == 0


def main():
    profile = cache_folder() / "browser-profile"
    if _port_in_use():
        # Already running: just bring up another window.
        open_window(URL, profile)
        return
    app = create_app(data_folder())
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PORT, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started and thread.is_alive():
        time.sleep(0.05)
    print(f"{APP_NAME} is running at {URL}")
    window = open_window(URL, profile)
    try:
        if window is not None:
            window.wait()
        else:
            print("Close this window to stop.")
            thread.join()
    except KeyboardInterrupt:
        pass
    server.should_exit = True
    thread.join(timeout=5)


if __name__ == "__main__":
    main()
