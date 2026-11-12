
"""End-to-end software demo using the real visual test images.

No camera, motors, GPIO, or robot entry point is started.
Temporary databases are removed automatically after the demo.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from autocar.map_builder import MapBuilder
from autocar.map_storage import MapStorage
from autocar.path_planner import PathPlanner
from autocar.visual_place_database import VisualPlaceDatabase


def ask_yes_no(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() == "y"


def main():
    root = Path(__file__).resolve().parents[1]
    image_dir = root / "data" / "visual_test"

    image_paths = [
        image_dir / "place_a1.jpeg",
        image_dir / "place_a2.jpeg",
        image_dir / "place_b1.jpeg",
    ]

    for path in image_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Missing test image: {path}")

    with TemporaryDirectory(prefix="autocar_e2e_") as temp:
        temp_path = Path(temp)
        database = VisualPlaceDatabase(temp_path / "visual_places")
        storage = MapStorage(temp_path / "navigation_map.json")
        builder = MapBuilder(storage=storage)

        print("\n=== Phase 1: Visual place recognition ===")
        observed_place_ids = []

        for image_path in image_paths:
            result = database.observe(image_path)

            print(f"\nImage: {image_path.name}")
            print(f"Status: {result['status']}")
            print(f"Place ID: {result['place_id']}")
            print(f"Good matches: {result['good_matches']}")
            print(f"Score: {result['score']:.4f}")

            if result["status"] == "candidate":
                if ask_yes_no(
                    f"Approve {image_path.name} as a new reference place?"
                ):
                    result = database.register_candidate(image_path)
                    print(f"Registration: {result['status']}")
                else:
                    print("Candidate skipped.")
                    continue

            place_id = result["place_id"]
            if place_id and place_id not in observed_place_ids:
                observed_place_ids.append(place_id)
                builder.add_place(place_id)

        print("\n=== Phase 2: Confirm actual connectivity ===")
        print("Registered/recognized places:", observed_place_ids)

        if len(observed_place_ids) >= 2:
            source = observed_place_ids[0]
            target = observed_place_ids[1]

            print(
                f"\nPotential connection: {source} <-> {target}"
            )
            print(
                "Only confirm if the robot actually traversed this "
                "connection and both endpoints were verified."
            )

            if ask_yes_no("Was this physical transition verified?"):
                builder.connect_places(source, target)
                print("Connection added.")
            else:
                print("Connection not added.")
        else:
            print(
                "Fewer than two distinct places were accepted; "
                "no connection can be tested."
            )

        builder.save()
        graph = storage.load()

        print("\n=== Phase 3: Saved navigation graph ===")
        print(graph)

        if len(observed_place_ids) >= 2:
            start = input(
                f"Start place ID {observed_place_ids}: "
            ).strip()
            destination = input(
                f"Destination place ID {observed_place_ids}: "
            ).strip()

            planner = PathPlanner(graph)

            try:
                route = planner.shortest_path(start, destination)
                print("\nRoute:")
                print(" -> ".join(route) if route else "No verified route")
            except ValueError as exc:
                print(f"Invalid endpoint: {exc}")

        print("\nEnd-to-end software demo completed.")
        print("Temporary data will now be cleaned up.")


if __name__ == "__main__":
    main()
