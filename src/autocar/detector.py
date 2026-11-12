"""YOLO object detection over a captured still image."""
from __future__ import annotations

import logging
from collections import Counter

from ultralytics import YOLO

from . import config

log = logging.getLogger(__name__)


class Detector:
    def __init__(self) -> None:
        log.info("Loading YOLO model (%s)...", config.YOLO_MODEL_PATH)
        self._model = YOLO(config.YOLO_MODEL_PATH)
        log.info("Warming up model with a dummy inference (this can take a while on Pi CPU)...")
        import numpy as np
        dummy = np.zeros((640, 640, 3), dtype="uint8")
        self._model.predict(source=dummy, conf=config.YOLO_CONFIDENCE_THRESHOLD, verbose=False)
        log.info("Model ready.")

    def detect(self, image_path: str) -> list[str]:
        """Runs detection and returns a list of detected class names (with duplicates)."""
        results = self._model.predict(
            source=image_path,
            conf=config.YOLO_CONFIDENCE_THRESHOLD,
            verbose=False,
        )
        names = results[0].names
        labels = [names[int(box.cls)] for box in results[0].boxes]
        log.info("Detected: %s", labels)
        return labels
    
    def detect_objects(self, image_path: str) -> list[dict[str, str | float]]:
        """Return detected objects with confidence and normalized image positions."""
        results = self._model.predict(
            source=image_path,
            conf=config.YOLO_CONFIDENCE_THRESHOLD,
            verbose=False,
        )

        result = results[0]
        image_height, image_width = result.orig_shape
        objects: list[dict[str, str | float]] = []

        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            class_id = int(box.cls.item())

            objects.append({
                "label": result.names[class_id],
                "confidence": float(box.conf.item()),
                "center_x": ((x1 + x2) / 2) / image_width,
                "center_y": ((y1 + y2) / 2) / image_height,
                "x1": float(x1),
                "y1": float(y1),
                "x2": float(x2),
                "y2": float(y2),
            })

        log.info("Detected objects with positions: %s", objects)
        return objects

    @staticmethod
    def describe(labels: list[str]) -> str:
        """Turns ['person', 'chair', 'chair'] into 'I found one person and two chairs.'"""
        if not labels:
            return "I don't see anything I recognize in front of me."

        counts = Counter(labels)
        words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}

        def phrase(name: str, n: int) -> str:
            count_word = words.get(n, str(n))
            noun = name if n == 1 else name + "s"
            return f"{count_word} {noun}"

        parts = [phrase(name, n) for name, n in counts.items()]
        if len(parts) == 1:
            joined = parts[0]
        else:
            joined = ", ".join(parts[:-1]) + " and " + parts[-1]

        return f"I found {joined}."
