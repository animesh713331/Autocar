"""HC-SR04 ultrasonic distance sensor wrapper."""
from __future__ import annotations

from gpiozero import DistanceSensor

from . import config


class Ultrasonic:
    def __init__(self) -> None:
        self._sensor = DistanceSensor(
            echo=config.ULTRASONIC_ECHO,
            trigger=config.ULTRASONIC_TRIGGER,
            max_distance=config.ULTRASONIC_MAX_DISTANCE_M,
        )

    def distance_m(self) -> float:
        """Returns distance to nearest obstacle in meters."""
        return self._sensor.distance

    def close(self) -> None:
        self._sensor.close()
