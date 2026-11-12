
"""Hardware-independent, goal-directed navigation decisions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .path_planner import PathPlanner


@dataclass(frozen=True)
class NavigationDecision:
    action: str
    current_place: str | None
    destination: str
    next_place: str | None
    route: tuple[str, ...]
    reason: str


class NavigationController:
    """Plan route progress without directly controlling robot hardware."""

    def __init__(self, graph: dict[str, Any]) -> None:
        self._graph = graph
        self._planner = PathPlanner(graph)

    def _get_transition_direction(
        self, source: str, target: str
    ) -> str | None:
        """Return a verified steering direction for a map transition."""
        for edge in self._graph.get("edges", []):
            if edge.get("source") == source and edge.get("target") == target:
                return edge.get("direction")

            if (
                edge.get("source") == target
                and edge.get("target") == source
                and edge.get("bidirectional", False)
            ):
                # Reverse travel needs its own verified direction.
                return edge.get("reverse_direction")

        return None

    def decide(
        self,
        current_place: str | None,
        destination: str,
        *,
        obstacle_detected: bool = False,
    ) -> NavigationDecision:
        if obstacle_detected:
            return NavigationDecision(
                action="stop",
                current_place=current_place,
                destination=destination,
                next_place=None,
                route=(),
                reason="Obstacle detected; movement must stop.",
            )

        if current_place is None:
            return NavigationDecision(
                action="localize",
                current_place=None,
                destination=destination,
                next_place=None,
                route=(),
                reason="Current place is unknown; localization is required.",
            )

        route = self._planner.shortest_path(current_place, destination)

        if not route:
            return NavigationDecision(
                action="stop",
                current_place=current_place,
                destination=destination,
                next_place=None,
                route=(),
                reason="Destination is unreachable on the current map.",
            )

        if len(route) == 1:
            return NavigationDecision(
                action="arrived",
                current_place=current_place,
                destination=destination,
                next_place=None,
                route=tuple(route),
                reason="Current place is the destination.",
            )

        next_place = route[1]
        direction = self._get_transition_direction(
            current_place, next_place
        )

        if direction not in {"left", "right", "straight", "uturn"}:
            return NavigationDecision(
                action="verify_transition",
                current_place=current_place,
                destination=destination,
                next_place=next_place,
                route=tuple(route),
                reason=(
                    f"Transition {current_place}->{next_place} has no "
                    "verified steering direction."
                ),
            )

        action = {
            "left": "turn_left",
            "right": "turn_right",
            "straight": "straight",
            "uturn": "turn_around",
        }[direction]

        return NavigationDecision(
            action=action,
            current_place=current_place,
            destination=destination,
            next_place=next_place,
            route=tuple(route),
            reason=(
                f"Follow the verified {direction} transition "
                f"from {current_place} to {next_place}."
            ),
        )
