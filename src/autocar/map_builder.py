
"""Build a navigation graph from confirmed visual place observations.

This module does not control robot hardware.
"""

from __future__ import annotations

from typing import Any

from .map_storage import MapStorage


class MapBuilder:
    """Maintain place nodes and observed connections between them."""

    def __init__(
        self,
        storage: MapStorage | None = None,
        graph: dict[str, Any] | None = None,
    ) -> None:
        self.storage = storage or MapStorage("data/navigation_map.json")
        self.graph = graph if graph is not None else self.storage.load()
        self.storage.validate(self.graph)

        # Tracks the last place seen during a continuous observation sequence.
        self._last_place_id: str | None = None

    def add_place(self, place_id: str) -> bool:
        """Add a place node. Return False if it already exists."""
        if not isinstance(place_id, str) or not place_id.strip():
            raise ValueError("place_id must be a non-empty string")

        if any(node["id"] == place_id for node in self.graph["nodes"]):
            return False

        self.graph["nodes"].append({"id": place_id})
        return True

    def connect_places(
        self,
        source: str,
        target: str,
        *,
        bidirectional: bool = True,
    ) -> bool:
        """Record an observed connection between existing places.

        Returns False if the connection already exists.
        """
        node_ids = {node["id"] for node in self.graph["nodes"]}

        if source not in node_ids or target not in node_ids:
            raise ValueError("Both places must exist before connecting them")

        if source == target:
            raise ValueError("A place cannot connect to itself")

        if not isinstance(bidirectional, bool):
            raise ValueError("bidirectional must be a boolean")

        existing = any(
            edge["source"] == source and edge["target"] == target
            for edge in self.graph["edges"]
        )

        if bidirectional:
            existing = existing or any(
                edge["source"] == target and edge["target"] == source
                for edge in self.graph["edges"]
            )

        if existing:
            return False

        self.graph["edges"].append(
            {
                "source": source,
                "target": target,
                "bidirectional": bidirectional,
            }
        )
        return True

    
    def set_transition_metadata(
        self,
        source: str,
        target: str,
        *,
        direction: str | None = None,
        distance_m: float | None = None,
        reverse_direction: str | None = None,
    ) -> bool:
        """Attach verified metadata to an existing directed edge."""
        allowed_directions = {"left", "right", "straight", "uturn"}

        for name, value in (
            ("direction", direction),
            ("reverse_direction", reverse_direction),
        ):
            if value is not None and value not in allowed_directions:
                raise ValueError(
                    f"{name} must be left, right, straight, uturn, or None"
                )

        if distance_m is not None:
            if (
                isinstance(distance_m, bool)
                or not isinstance(distance_m, (int, float))
                or distance_m <= 0
            ):
                raise ValueError("distance_m must be a positive number")

        edge = next(
            (
                item
                for item in self.graph["edges"]
                if item["source"] == source and item["target"] == target
            ),
            None,
        )

        if edge is None:
            raise ValueError("Transition does not exist in this direction")

        if reverse_direction is not None and not edge.get(
            "bidirectional", False
        ):
            raise ValueError(
                "reverse_direction requires a bidirectional transition"
            )

        if direction is not None:
            edge["direction"] = direction

        if reverse_direction is not None:
            edge["reverse_direction"] = reverse_direction

        if distance_m is not None:
            edge["distance_m"] = float(distance_m)

        return True


    def observe_transition(
        self,
        place_id: str,
        *,
        confirmed: bool = False,
    ) -> bool:
        """Process a place observation.

        Only confirmed observations update the graph. The first confirmed
        place becomes the starting node; later confirmed places are connected
        to the previous confirmed place.

        Returns True when a new node or edge was added.
        """
        if not confirmed:
            return False

        changed = self.add_place(place_id)

        if self._last_place_id is not None:
            if self._last_place_id != place_id:
                changed = (
                    self.connect_places(self._last_place_id, place_id)
                    or changed
                )

        self._last_place_id = place_id
        return changed

    def save(self) -> None:
        """Persist the current graph."""
        self.storage.save(self.graph)

    def get_graph(self) -> dict[str, Any]:
        """Return a copy of the graph data."""
        return {
            "version": self.graph["version"],
            "nodes": [dict(node) for node in self.graph["nodes"]],
            "edges": [dict(edge) for edge in self.graph["edges"]],
        }

    def restore_graph(self, graph: dict[str, Any]) -> None:
        """Restore an earlier graph snapshot in memory."""
        self.storage.validate(graph)
        self.graph = {
            "version": graph["version"],
            "nodes": [dict(node) for node in graph["nodes"]],
            "edges": [dict(edge) for edge in graph["edges"]],
        }

    def reset_tracking(self) -> None:
        """Forget the previous observation without deleting the map."""
        self._last_place_id = None
