"""Entry point: `uv run autocar` or `python -m autocar.main`."""
from __future__ import annotations

import logging

from .camera import Camera
from .command_listener import CommandListener
from .control_state import ControlState
from .detector import Detector
from .motor_control import Drivetrain
from .navigation import run_forever
from .ultrasonic import Ultrasonic
from .web_control import start_web_server

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger(__name__)


def run() -> None:
    log.info(
        "Starting autocar. Type 'STOP AND TAKE A PHOTO', 'start', or 'stop' any time, "
        "or use the web dashboard (see URL below)."
    )

    state = ControlState()
    drivetrain = Drivetrain()
    sensor = Ultrasonic()
    listener = CommandListener(state)
    camera = Camera()
    detector = Detector()

    listener.start()
    start_web_server(state)

    try:
        run_forever(drivetrain, sensor, state, camera, detector)
    except KeyboardInterrupt:
        log.info("Shutting down (Ctrl+C).")
    finally:
        drivetrain.close()
        sensor.close()
        camera.close()
        listener.stop()


if __name__ == "__main__":
    run()
