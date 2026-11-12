"""Resolve human-readable destination names to registered map node IDs."""
from __future__ import annotations

import re
from collections.abc import Mapping


def normalize_name(name: str) -> str:
    """Normalize names for case-insensitive matching."""
    return re.sub(r"\s+", " ", name.strip()).casefold()


class DestinationResolver:
    """Resolve direct map IDs and aliases to registered map nodes."""

    def __init__(
        self,
        graph: dict,
        aliases: Mapping[str, str] | None = None,
    ) -> None:
        self._node_ids = {
            node["id"]
            for node in graph.get("nodes", [])
            if isinstance(node, dict) and isinstance(node.get("id"), str)
        }

        self._aliases: dict[str, str] = {}

        for alias, place_id in (aliases or {}).items():
            self.add_alias(alias, place_id)

    def add_alias(self, alias: str, place_id: str) -> None:
        key = normalize_name(alias)

        if not key:
            raise ValueError("Destination alias cannot be empty.")

        if place_id not in self._node_ids:
            raise ValueError(f"Unknown map place ID: {place_id}")

        existing = self._aliases.get(key)
        if existing is not None and existing != place_id:
            raise ValueError(f"Ambiguous destination alias: {alias}")

        self._aliases[key] = place_id

    def resolve(self, destination: str) -> str:
        key = normalize_name(destination)

        if not key:
            raise ValueError("Destination cannot be empty.")

        for node_id in self._node_ids:
            if normalize_name(node_id) == key:
                return node_id

        try:
            return self._aliases[key]
        except KeyError as exc:
            raise ValueError(
                f"Unknown destination: {destination}. "
                "No matching map node or registered alias found."
            ) from exc

    def list_aliases(self) -> dict[str, str]:
        return dict(self._aliases)
