
"""Shortest-path planning over the visual navigation graph."""

from __future__ import annotations

import heapq
from typing import Any


class PathPlanner:
    """Find a minimum-cost route between two known places."""

    def __init__(self, graph: dict[str, Any]) -> None:
        self._validate_graph(graph)
        self.graph = {
            "version": graph["version"],
            "nodes": [dict(node) for node in graph["nodes"]],
            "edges": [dict(edge) for edge in graph["edges"]],
        }

    @staticmethod
    def _validate_graph(graph: dict[str, Any]) -> None:
        if not isinstance(graph, dict):
            raise ValueError("Graph must be a dictionary")

        if not isinstance(graph.get("nodes"), list):
            raise ValueError("'nodes' must be a list")

        if not isinstance(graph.get("edges"), list):
            raise ValueError("'edges' must be a list")

        node_ids = set()

        for node in graph["nodes"]:
            if not isinstance(node, dict):
                raise ValueError("Each node must be a dictionary")

            node_id = node.get("id")
            if not isinstance(node_id, str) or not node_id:
                raise ValueError("Each node needs a non-empty string ID")

            if node_id in node_ids:
                raise ValueError(f"Duplicate node ID: {node_id}")

            node_ids.add(node_id)

        for edge in graph["edges"]:
            if not isinstance(edge, dict):
                raise ValueError("Each edge must be a dictionary")

            source = edge.get("source")
            target = edge.get("target")
            weight = edge.get("weight", 1.0)
            bidirectional = edge.get("bidirectional", True)

            if source not in node_ids or target not in node_ids:
                raise ValueError("Edge references an unknown place")

            if source == target:
                raise ValueError("Self-edges are not allowed")

            if (
                isinstance(weight, bool)
                or not isinstance(weight, (int, float))
                or weight <= 0
            ):
                raise ValueError("Edge weight must be a positive number")

            if not isinstance(bidirectional, bool):
                raise ValueError("bidirectional must be a boolean")

    def shortest_path(self, start: str, destination: str) -> list[str]:
        """Return place IDs for the minimum-cost route.

        Returns an empty list if the destination is unreachable.
        Raises ValueError when either endpoint is unknown.
        """
        adjacency: dict[str, list[tuple[str, float]]] = {
            node["id"]: [] for node in self.graph["nodes"]
        }

        for edge in self.graph["edges"]:
            source = edge["source"]
            target = edge["target"]
            weight = float(edge.get("weight", 1.0))

            adjacency[source].append((target, weight))

            if edge.get("bidirectional", True):
                adjacency[target].append((source, weight))

        if start not in adjacency:
            raise ValueError(f"Unknown start place: {start}")

        if destination not in adjacency:
            raise ValueError(f"Unknown destination place: {destination}")

        distances = {place_id: float("inf") for place_id in adjacency}
        previous: dict[str, str] = {}
        distances[start] = 0.0

        queue = [(0.0, start)]

        while queue:
            current_distance, current = heapq.heappop(queue)

            if current_distance > distances[current]:
                continue

            if current == destination:
                break

            for neighbor, weight in adjacency[current]:
                candidate = current_distance + weight

                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    previous[neighbor] = current
                    heapq.heappush(queue, (candidate, neighbor))

        if distances[destination] == float("inf"):
            return []

        path = []
        current = destination

        while current != start:
            path.append(current)
            current = previous[current]

        path.append(start)
        path.reverse()

        return path
