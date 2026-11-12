"""
Camera capture using picamera2 (the official libcamera-based API on
Raspberry Pi OS / Debian Trixie — the old 'picamera' package does not
work on this OS version).

picamera2 must be installed via apt (python3-picamera2), NOT pip — see
scripts/setup_pi.sh and README.md. The uv venv is created with
--system-site-packages so it can see the apt-installed picamera2.
"""
from __future__ import annotations

import logging
import os
import time

from . import config

log = logging.getLogger(__name__)


class Camera:
    def __init__(self) -> None:
        from picamera2 import Picamera2  # imported lazily so this module

        self._picam2 = Picamera2()
        cfg = self._picam2.create_still_configuration(
            main={"size": config.CAPTURE_RESOLUTION}
        )
        self._picam2.configure(cfg)
        self._picam2.start()
        time.sleep(1)  # let auto-exposure/white-balance settle

    def capture(self) -> str:
        """Capture a still image, save it, and return the file path."""
        os.makedirs(config.CAPTURE_DIR, exist_ok=True)
        filename = os.path.join(
            config.CAPTURE_DIR, f"capture_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        )
        self._picam2.capture_file(filename)
        log.info("Captured image: %s", filename)
        return filename

    def close(self) -> None:
        self._picam2.stop()
