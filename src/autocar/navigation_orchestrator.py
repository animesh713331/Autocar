
"""Hardware-independent orchestration for visual navigation."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from .path_planner import PathPlanner


class NavigationOrchestrator:
    """Coordinate place observations, candidate approval, and route planning.

    This class does not control motors, camera hardware, or sensors.
    """

    def __init__(
        self,
        place_database: Any,
        map_builder: Any,
        pending_dir: str | Path = "data/pending_places",
    ) -> None:
        self.place_database = place_database
        self.map_builder = map_builder
        self.pending_dir = Path(pending_dir)
        self.pending_dir.mkdir(parents=True, exist_ok=True)

    def observe(self, image_path: str | Path) -> dict[str, Any]:
        """Recognize a place or save an unknown image for later review."""
        image_path = Path(image_path)
        result = self.place_database.observe(image_path)

        if result["status"] == "recognized":
            place_id = result["place_id"]
            self.map_builder.add_place(place_id)
            self.map_builder.save()
            return result

        if result["status"] != "candidate":
            raise ValueError(
                f"Unexpected observation status: {result['status']}"
            )

        candidate_id = f"{uuid.uuid4().hex}{image_path.suffix.lower()}"
        candidate_path = self.pending_dir / candidate_id
        shutil.copy2(image_path, candidate_path)

        return {
            **result,
            "candidate_id": candidate_id,
            "candidate_path": str(candidate_path),
            "status": "pending_review",
        }

    def localize(self, image_path: str | Path) -> dict[str, Any]:
        """Observe an image without changing the navigation map.

        Unknown images are copied to the pending-review directory.
        Registering places and changing map topology require explicit approval.
        """
        image_path = Path(image_path)
        result = self.place_database.observe(image_path)

        if result["status"] == "recognized":
            return result

        if result["status"] != "candidate":
            raise ValueError(
                f"Unexpected observation status: {result['status']}"
            )

        candidate_id = f"{uuid.uuid4().hex}{image_path.suffix.lower()}"
        candidate_path = self.pending_dir / candidate_id
        shutil.copy2(image_path, candidate_path)

        return {
            **result,
            "candidate_id": candidate_id,
            "candidate_path": str(candidate_path),
            "status": "pending_review",
        }

    def list_pending_candidates(self) -> list[str]:
        """List images waiting for operator approval."""
        return sorted(
            path.name
            for path in self.pending_dir.iterdir()
            if path.is_file()
        )

    
    def approve_candidate(self, candidate_id: str) -> dict[str, Any]:
        """Register an approved candidate, rolling back if map saving fails."""
        if Path(candidate_id).name != candidate_id:
            raise ValueError("Invalid candidate ID")

        candidate_path = self.pending_dir / candidate_id
        if not candidate_path.is_file():
            raise ValueError(f"Pending candidate not found: {candidate_id}")

        # Keep a snapshot before modifying the database or graph.
        previous_graph = self.map_builder.get_graph()
        result = self.place_database.register_candidate(candidate_path)

        if result["status"] == "recognized":
            candidate_path.unlink()
            return result

        if result["status"] != "new_place":
            raise ValueError(
                f"Unexpected registration status: {result['status']}"
            )

        place_id = result["place_id"]

        try:
            self.map_builder.add_place(place_id)
            self.map_builder.save()
        except Exception as original_error:
            rollback_errors = []

            try:
                self.map_builder.restore_graph(previous_graph)
            except Exception as error:
                rollback_errors.append(f"map memory rollback: {error}")

            try:
                self.place_database.remove_place(place_id)
            except Exception as error:
                rollback_errors.append(f"database rollback: {error}")

            if rollback_errors:
                raise RuntimeError(
                    "Map save failed and rollback was incomplete: "
                    + "; ".join(rollback_errors)
                ) from original_error

            # Keep the pending image so approval can be retried.
            raise

        candidate_path.unlink()
        return result


    
    def confirm_transition(
        self,
        source: str,
        target: str,
        *,
        bidirectional: bool = True,
        direction: str | None = None,
        distance_m: float | None = None,
        reverse_direction: str | None = None,
    ) -> bool:
        """Record an externally verified transition and optional metadata."""
        previous_graph = self.map_builder.get_graph()

        try:
            added = self.map_builder.connect_places(
                source,
                target,
                bidirectional=bidirectional,
            )

            has_metadata = any(
                value is not None
                for value in (direction, distance_m, reverse_direction)
            )

            if not added and not has_metadata:
                return False

            if reverse_direction is not None and not bidirectional:
                raise ValueError(
                    "reverse_direction requires a bidirectional transition"
                )

            if has_metadata:
                self.map_builder.set_transition_metadata(
                    source,
                    target,
                    direction=direction,
                    distance_m=distance_m,
                    reverse_direction=reverse_direction,
                )

            self.map_builder.save()
            return added

        except Exception:
            self.map_builder.restore_graph(previous_graph)
            raise


    def plan_route(self, start: str, destination: str) -> list[str]:
        """Calculate a route using the currently stored graph."""
        planner = PathPlanner(self.map_builder.get_graph())
        return planner.shortest_path(start, destination)

    
