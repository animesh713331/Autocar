"""
Listens for typed commands over the terminal (works great over SSH - just
type the command and press Enter): STOP AND TAKE A PHOTO, start, stop.

This runs in its own thread so it never blocks the driving loop. It only
sets flags on the shared ControlState - it never touches hardware directly.
"""
from __future__ import annotations

import logging
import threading

from . import config
from .control_state import ControlState

log = logging.getLogger(__name__)


class CommandListener:
    def __init__(self, state: ControlState) -> None:
        self.state = state
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)

    def start(self) -> None:
        self._thread.start()
        log.info(
            "Command listener started. Type: 'STOP AND TAKE A PHOTO', 'start', or 'stop'"
        )

    def _read_loop(self) -> None:
        while not self._stop.is_set():
            try:
                line = input().strip().lower()
            except EOFError:
                break

            if line in config.STOP_AND_PHOTO_PHRASES:
                log.info("Command received: %s", line)
                self.state.photo_requested.set()
            elif line in config.START_PHRASES:
                log.info("Command received: %s", line)
                self.state.running.set()
            elif line in config.STOP_PHRASES:
                log.info("Command received: %s", line)
                self.state.running.clear()

    def stop(self) -> None:
        self._stop.set()
