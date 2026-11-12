
"""Persistent visual place database.

This module stores reference images and uses VisualPlaceMatcher to recognize
previously observed places. It does not control hardware.
"""

import json
import shutil
from pathlib import Path

from .visual_place_matcher import VisualPlaceMatcher


class VisualPlaceDatabase:
    def __init__(self, database_dir, matcher=None):
        self.database_dir = Path(database_dir)
        self.images_dir = self.database_dir / "images"
        self.metadata_path = self.database_dir / "places.json"
        self.matcher = matcher or VisualPlaceMatcher()

        self.images_dir.mkdir(parents=True, exist_ok=True)

        if self.metadata_path.exists():
            with self.metadata_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            self.places = data.get("places", [])
        else:
            self.places = []

        self._validate_records()

    def _record_images(self, place):
        """Return image filenames from legacy or multiple-reference records."""
        if "images" in place:
            return place["images"]
        return [place["image"]]

    def _validate_records(self):
        """Validate place IDs and all referenced image files."""
        seen_ids = set()
        seen_images = set()

        for place in self.places:
            if not isinstance(place, dict):
                raise ValueError("Every place must be a dictionary")

            place_id = place.get("id")
            if not isinstance(place_id, str) or not place_id:
                raise ValueError("Every place must have a non-empty ID")

            if place_id in seen_ids:
                raise ValueError(f"Duplicate place ID: {place_id}")
            seen_ids.add(place_id)

            image_names = self._record_images(place)

            if not isinstance(image_names, list) or not image_names:
                raise ValueError(f"Missing reference images for {place_id}")

            for image_name in image_names:
                if not isinstance(image_name, str) or not image_name:
                    raise ValueError(f"Invalid image filename for {place_id}")

                if Path(image_name).name != image_name:
                    raise ValueError(f"Invalid image filename for {place_id}")

                if image_name in seen_images:
                    raise ValueError(f"Duplicate reference image: {image_name}")
                seen_images.add(image_name)

                if not (self.images_dir / image_name).is_file():
                    raise ValueError(
                        f"Reference image missing for {place_id}: {image_name}"
                    )

    def _save(self):
        """Persist the current place records."""
        temporary_path = self.metadata_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(
                {"version": 1, "places": self.places},
                file,
                indent=2,
            )
        temporary_path.replace(self.metadata_path)

    def list_places(self):
        """Return independent copies of all place records."""
        return [
            {
                **place,
                **(
                    {"images": list(place["images"])}
                    if "images" in place else {}
                ),
            }
            for place in self.places
        ]

    
    def observe(self, image_path, min_score=None):
        """Recognize a known place using all its reference images."""
        image_path = Path(image_path)
        if not image_path.is_file():
            raise ValueError(f"Observation image not found: {image_path}")

        self.matcher._load_grayscale(image_path)

        best_place = None
        best_result = None
        best_reference = None

        for place in self.places:
            place_best_result = None
            place_best_reference = None

            for image_name in self._record_images(place):
                reference_path = self.images_dir / image_name
                result = self.matcher.compare(reference_path, image_path)

                accepted = result.is_same_place
                if min_score is not None:
                    accepted = accepted and result.score >= min_score

                if accepted and (
                    place_best_result is None
                    or result.score > place_best_result.score
                ):
                    place_best_result = result
                    place_best_reference = image_name

            if place_best_result is not None and (
                best_result is None
                or place_best_result.score > best_result.score
            ):
                best_place = place
                best_result = place_best_result
                best_reference = place_best_reference

        if best_place is not None:
            return {
                "place_id": best_place["id"],
                "status": "recognized",
                "good_matches": best_result.good_matches,
                "score": best_result.score,
                "geometric_inliers": best_result.geometric_inliers,
                "matched_reference": best_reference,
            }

        return {
            "place_id": None,
            "status": "candidate",
            "image_path": str(image_path),
            "good_matches": 0,
            "score": 0.0,
            "geometric_inliers": 0,
        }

    def register_place(self, place_id, image_paths):
        """Register a named place with one or more reference images."""
        import re

        if (
            not isinstance(place_id, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", place_id)
        ):
            raise ValueError("Invalid place ID")

        if any(place["id"] == place_id for place in self.places):
            raise ValueError(f"Place already exists: {place_id}")

        if isinstance(image_paths, (str, Path)):
            image_paths = [image_paths]

        image_paths = [Path(item) for item in image_paths]

        if not image_paths:
            raise ValueError("At least one reference image is required")

        for image_path in image_paths:
            if not image_path.is_file():
                raise ValueError(f"Reference image not found: {image_path}")
            self.matcher._load_grayscale(image_path)

        existing_names = {
            name
            for place in self.places
            for name in self._record_images(place)
        }

        copied_names = []
        record = None

        try:
            for index, image_path in enumerate(image_paths, start=1):
                suffix = image_path.suffix.lower() or ".jpg"
                image_name = f"{place_id}_{index:02d}{suffix}"
                destination = self.images_dir / image_name

                if image_name in existing_names or destination.exists():
                    raise FileExistsError(
                        f"Reference image already exists: {image_name}"
                    )

                shutil.copy2(image_path, destination)
                copied_names.append(image_name)

            record = {"id": place_id, "images": copied_names}
            self.places.append(record)
            self._save()

        except Exception:
            if record is not None and record in self.places:
                self.places.remove(record)

            for image_name in copied_names:
                (self.images_dir / image_name).unlink(missing_ok=True)
            raise

        return {
            "place_id": place_id,
            "status": "new_place",
            "image_count": len(copied_names),
            "images": list(copied_names),
            "good_matches": 0,
            "score": 0.0,
            "geometric_inliers": 0,
        }

    def register_candidate(self, image_path):
        """Explicitly approve and store an unmatched image as a new place."""
        image_path = Path(image_path)

        if not image_path.is_file():
            raise ValueError(f"Observation image not found: {image_path}")

        self.matcher._load_grayscale(image_path)

        result = self.observe(image_path)
        if result["status"] == "recognized":
            return result

        existing_numbers = [
            int(place["id"].removeprefix("place_"))
            for place in self.places
            if place["id"].startswith("place_")
            and place["id"].removeprefix("place_").isdigit()
        ]

        next_number = max(existing_numbers, default=0) + 1
        place_id = f"place_{next_number:04d}"

        registered = self.register_place(place_id, [image_path])

        return {
            "place_id": registered["place_id"],
            "status": "new_place",
            "good_matches": 0,
            "score": 0.0,
            "geometric_inliers": 0,
        }

    def remove_place(self, place_id):
        """Remove a place and all its reference images safely."""
        index = next(
            (
                i for i, place in enumerate(self.places)
                if place["id"] == place_id
            ),
            None,
        )

        if index is None:
            return False

        record = self.places.pop(index)
        image_names = list(self._record_images(record))

        try:
            self._save()
        except Exception:
            self.places.insert(index, record)
            raise

        for image_name in image_names:
            (self.images_dir / image_name).unlink(missing_ok=True)

        return True
