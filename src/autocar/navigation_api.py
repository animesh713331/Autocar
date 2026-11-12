"""Hardware-independent Flask navigation API."""
from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from .destination_resolver import DestinationResolver
from .navigation_session import NavigationSession


def create_navigation_blueprint(
    session: NavigationSession,
    resolver: DestinationResolver,
) -> Blueprint:
    """Create advisory-only navigation endpoints."""
    blueprint = Blueprint("navigation_api", __name__)

    @blueprint.post("/api/navigation/destination")
    def submit_destination():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(error="Expected a JSON object."), 400

        destination = body.get("destination")
        if not isinstance(destination, str) or not destination.strip():
            return jsonify(error="Destination must be a non-empty string."), 400

        try:
            place_id = resolver.resolve(destination)
            result = session.submit_destination(place_id)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

        return jsonify({
            **result,
            "destination_name": destination.strip(),
            "execution": "advisory_only",
        }), 200

    @blueprint.get("/api/navigation/status")
    def navigation_status():
        return jsonify(session.get_status())

    @blueprint.post("/api/navigation/stop")
    def stop_navigation():
        return jsonify(session.stop())

    return blueprint
