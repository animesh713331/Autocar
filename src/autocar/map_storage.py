
"""JSON persistence for the visual navigation graph.

This module is software-only and does not access robot hardware.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MapStorage:
    """Save and load a graph containing place nodes and observed edges."""

    VERSION = 1

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)

    @staticmethod
    def empty_map() -> dict[str, Any]:
        return {"version": MapStorage.VERSION, "nodes": [], "edges": []}

    @staticmethod
    def validate(graph: dict[str, Any]) -> None:
        if not isinstance(graph, dict):
            raise ValueError("Map must be a dictionary")

        if graph.get("version") != MapStorage.VERSION:
            raise ValueError("Unsupported or missing map version")

        nodes = graph.get("nodes")
        edges = graph.get("edges")

        if not isinstance(nodes, list) or not isinstance(edges, list):
            raise ValueError("'nodes' and 'edges' must be lists")

        node_ids: set[str] = set()

        for node in nodes:
            if not isinstance(node, dict):
                raise ValueError("Each node must be a dictionary")

            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                raise ValueError("Every node needs a non-empty string ID")

            if node_id in node_ids:
                raise ValueError(f"Duplicate node ID: {node_id}")

            node_ids.add(node_id)

        edge_keys: set[tuple[str, str]] = set()

        for edge in edges:
            if not isinstance(edge, dict):
                raise ValueError("Each edge must be a dictionary")

            source = edge.get("source")
            target = edge.get("target")

            if source not in node_ids or target not in node_ids:
                raise ValueError("Every edge must reference existing nodes")

            if source == target:
                raise ValueError("Self-edges are not allowed")

            key = tuple(sorted((source, target)))
            if key in edge_keys:
                raise ValueError(f"Duplicate edge: {source} - {target}")

            edge_keys.add(key)

    def save(self, graph: dict[str, Any]) -> None:
        """Validate and atomically save the graph as JSON."""
        self.validate(graph)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = self.file_path.with_suffix(
            self.file_path.suffix + ".tmp"
        )

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(graph, file, indent=2)
                file.write("\n")

            temporary_path.replace(self.file_path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def load(self) -> dict[str, Any]:
        """Load a saved graph, or return an empty graph if none exists."""
        if not self.file_path.exists():
            return self.empty_map()

        with self.file_path.open("r", encoding="utf-8") as file:
            graph = json.load(file)

        self.validate(graph)
        return graph
