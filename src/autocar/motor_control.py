"""
Motor control for a differential-drive (skid-steer) 4WD chassis
driven by two L298N channels (left side, right side).

Uses gpiozero.Motor, which handles direction pins + PWM enable pin for you.
"""
from __future__ import annotations

import logging
from gpiozero import Motor

from . import config

log = logging.getLogger(__name__)


class Drivetrain:
    def __init__(self) -> None:
        self.left = Motor(
            forward=config.LEFT_MOTOR_FORWARD,
            backward=config.LEFT_MOTOR_BACKWARD,
            enable=config.LEFT_MOTOR_ENABLE,
            pwm=True,
        )
        self.right = Motor(
            forward=config.RIGHT_MOTOR_FORWARD,
            backward=config.RIGHT_MOTOR_BACKWARD,
            enable=config.RIGHT_MOTOR_ENABLE,
            pwm=True,
        )

    def forward(self, speed: float = config.DRIVE_SPEED) -> None:
        speed = max(0.0, min(1.0, speed))
        self.left.forward(speed)
        self.right.forward(speed)

    def stop(self) -> None:
        self.left.stop()
        self.right.stop()

    def turn_left(self, speed: float = config.SLOW_SPEED) -> None:
        """Pivot left: right side forward, left side backward (in-place turn)."""
        self.left.backward(speed)
        self.right.forward(speed)

    def turn_right(self, speed: float = config.SLOW_SPEED) -> None:
        """Pivot right: left side forward, right side backward (in-place turn)."""
        self.left.forward(speed)
        self.right.backward(speed)

    def backward(self, speed: float = config.SLOW_SPEED) -> None:
        self.left.backward(speed)
        self.right.backward(speed)

    def close(self) -> None:
        self.stop()
        self.left.close()
        self.right.close()
