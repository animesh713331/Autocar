
"""Software-only demo: recognized places, graph persistence and routing."""

from pathlib import Path
from tempfile import TemporaryDirectory

from autocar.map_builder import MapBuilder
from autocar.map_storage import MapStorage
from autocar.path_planner import PathPlanner


def main():
    with TemporaryDirectory(prefix="autocar_graph_demo_") as temp_dir:
        map_path = Path(temp_dir) / "navigation_map.json"
        storage = MapStorage(map_path)
        builder = MapBuilder(storage=storage)

        # These are example nodes, not claims that a real route was traversed.
        builder.add_place("place_0001")
        builder.add_place("place_0002")
        builder.add_place("place_0003")

        # Example topology for testing route calculation only.
        builder.connect_places("place_0001", "place_0002")
        builder.connect_places("place_0002", "place_0003")
        builder.save()

        loaded_graph = storage.load()

        print("Saved and reloaded graph:")
        print(loaded_graph)

        planner = PathPlanner(loaded_graph)
        route = planner.shortest_path("place_0001", "place_0003")

        print("\nExample route:")
        print(" -> ".join(route) if route else "No route found")

        assert route == ["place_0001", "place_0002", "place_0003"]
        print("\nGraph persistence and route calculation passed.")


if __name__ == "__main__":
    main()
