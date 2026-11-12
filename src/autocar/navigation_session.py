"""Hardware-independent navigation session state and decisions."""
from __future__ import annotations

from typing import Any

from .navigation_controller import NavigationController


class NavigationSession:
    """Track a navigation request without executing physical movement."""

    def __init__(self, controller: NavigationController) -> None:
        self.controller = controller
        self.destination: str | None = None
        self.current_place: str | None = None
        self.status = "stopped"
        self.last_decision: dict[str, Any] | None = None
        self._blocked = False

    def submit_destination(self, destination: str) -> dict[str, Any]:
        destination = destination.strip()
        if not destination:
            raise ValueError("Destination cannot be empty.")

        self.destination = destination
        self._blocked = False
        self.status = (
            "awaiting_localization"
            if self.current_place is None
            else "navigating"
        )
        self.last_decision = None
        return self.get_status()

    def update_location(
        self, place_id: str | None, *, obstacle_detected: bool = False
    ) -> dict[str, Any]:
        self.current_place = place_id or None
        return self.evaluate(obstacle_detected=obstacle_detected)

    def evaluate(self, *, obstacle_detected: bool = False) -> dict[str, Any]:
        if obstacle_detected:
            self._blocked = True

        if self._blocked:
            self.status = "blocked"
            self.last_decision = {
                "action": "stop",
                "reason": "Navigation is blocked; submit a new destination to retry.",
                "current_place": self.current_place,
                "destination": self.destination,
                "next_place": None,
                "route": [],
            }
            return self.get_status()

        if self.destination is None:
            self.status = "stopped"
            self.last_decision = {
                "action": "stop",
                "reason": "No destination has been submitted.",
                "current_place": self.current_place,
                "destination": None,
                "next_place": None,
                "route": [],
            }
            return self.get_status()

        decision = self.controller.decide(
            self.current_place,
            self.destination,
            obstacle_detected=obstacle_detected,
        )

        self.status = {
            "localize": "awaiting_localization",
            "verify_transition": "needs_transition_verification",
            "stop": "blocked",
            "arrived": "arrived",
        }.get(decision.action, "navigating")

        self.last_decision = {
            "action": decision.action,
            "reason": decision.reason,
            "current_place": decision.current_place,
            "destination": decision.destination,
            "next_place": decision.next_place,
            "route": list(decision.route),
        }
        return self.get_status()

    def stop(self) -> dict[str, Any]:
        self.destination = None
        self.status = "stopped"
        self.last_decision = {
            "action": "stop",
            "reason": "Navigation cancelled by the operator.",
            "current_place": self.current_place,
            "destination": None,
            "next_place": None,
            "route": [],
        }
        return self.get_status()

    def get_status(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "current_place": self.current_place,
            "destination": self.destination,
            "decision": self.last_decision,
            "execution": "advisory_only",
        }
