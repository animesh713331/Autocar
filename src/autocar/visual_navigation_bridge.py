
"""Hardware-independent bridge to visual navigation.

This module accepts captured image paths and provides advisory routes.
It never controls motors, sensors, or camera hardware.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .navigation_orchestrator import NavigationOrchestrator
from .navigation_controller import NavigationController

class VisualNavigationBridge:
    """Expose visual navigation to other modules without hardware access."""

    def __init__(
        self,
        orchestrator: NavigationOrchestrator,
    ) -> None:
        self.orchestrator = orchestrator

    def process_capture(self, image_path: str | Path) -> dict[str, Any]:
        """Process an existing image and return its observation result."""
        return self.orchestrator.observe(image_path)

    def localize_capture(self, image_path: str | Path) -> dict[str, Any]:
        """Recognize a captured location without mutating the map."""
        return self.orchestrator.localize(image_path)

    def get_advisory_route(
        self,
        start: str,
        destination: str,
    ) -> dict[str, Any]:
        """Return a planned route without issuing movement commands."""
        route = self.orchestrator.plan_route(start, destination)

        return {
            "start": start,
            "destination": destination,
            "route": route,
            "reachable": bool(route),
            "execution": "advisory_only",
        }

    
    def get_navigation_decision(
        self,
        current_place: str | None,
        destination: str,
        *,
        obstacle_detected: bool = False,
    ) -> dict[str, Any]:
        """Return a navigation decision without executing movement."""
        graph = self.orchestrator.map_builder.get_graph()
        controller = NavigationController(graph)

        decision = controller.decide(
            current_place,
            destination,
            obstacle_detected=obstacle_detected,
        )

        return {
            "action": decision.action,
            "current_place": decision.current_place,
            "destination": decision.destination,
            "next_place": decision.next_place,
            "route": list(decision.route),
            "reason": decision.reason,
            "execution": "advisory_only",
        }

