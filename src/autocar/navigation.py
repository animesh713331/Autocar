"""Drive loop: move forward, avoid obstacles, and pause for photo commands."""
from __future__ import annotations

import logging
import os
import time

from . import config
from .camera import Camera
from .control_state import ControlState
from .detector import Detector
from .motor_control import Drivetrain
from .ultrasonic import Ultrasonic

log = logging.getLogger(__name__)


def run_forever(
    drivetrain: Drivetrain,
    sensor: Ultrasonic,
    state: ControlState,
    camera: Camera,
    detector: Detector,
) -> None:
    period = 1.0 / config.SENSOR_POLL_HZ

    while True:
        # 1. Highest priority: has anyone (terminal or web) asked for a photo?
        if state.photo_requested.is_set():
            handle_stop_and_photo(drivetrain, camera, detector, state)
            state.photo_requested.clear()
            continue

        if state.left_requested.is_set():
            drivetrain.turn_left()
            time.sleep(0.5)
            drivetrain.stop()
            state.left_requested.clear()
            continue

        if state.right_requested.is_set():
            drivetrain.turn_right()
            time.sleep(0.5)
            drivetrain.stop()
            state.right_requested.clear()
            continue

        # 2. Paused? (Stop button/command pressed - hold still, keep polling.)
        if not state.running.is_set():
            drivetrain.stop()
            time.sleep(period)
            continue

        # 3. Otherwise, drive and avoid obstacles.
        distance = sensor.distance_m()

        if distance < config.STOP_DISTANCE_M:
            log.info("Obstacle at %.2fm - stopping and turning away.", distance)
            drivetrain.stop()
            drivetrain.turn_right(config.SLOW_SPEED)
            time.sleep(config.AVOID_TURN_SECONDS)
            drivetrain.stop()
        elif distance < config.SLOW_DISTANCE_M:
            drivetrain.forward(config.SLOW_SPEED)
        else:
            drivetrain.forward(config.DRIVE_SPEED)

        time.sleep(period)


def handle_stop_and_photo(
    drivetrain: Drivetrain, camera: Camera, detector: Detector, state: ControlState
) -> None:
    log.info("STOP AND TAKE A PHOTO received.")
    drivetrain.stop()

    print("Stopped. Capturing photo...")
    image_path = camera.capture()
    state.set_photo_path(image_path)
    print(f"Photo saved to {image_path}. Running detection...")
    labels = detector.detect(image_path)
    description = detector.describe(labels)

    print(description)  # this is the car "speaking" its answer back
    log.info(description)

    photo_url = f"/captures/{os.path.basename(image_path)}"
    state.set_photo_result(photo_url, description)