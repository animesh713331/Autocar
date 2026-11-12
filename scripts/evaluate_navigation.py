
"""Evaluate real images through the visual place database.

This script does not control hardware or modify the robot navigation loop.
It uses a temporary database for repeatable experiments.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from autocar.visual_place_database import VisualPlaceDatabase


def main():
    project_root = Path(__file__).resolve().parents[1]
    image_dir = project_root / "data" / "visual_test"

    image_paths = [
        image_dir / "place_a1.jpeg",
        image_dir / "place_a2.jpeg",
        image_dir / "place_b1.jpeg",
    ]

    for path in image_paths:
        if not path.is_file():
            raise FileNotFoundError(f"Test image not found: {path}")

    with TemporaryDirectory(prefix="autocar_eval_") as temporary_dir:
        database = VisualPlaceDatabase(temporary_dir)

        print("\n=== Visual Place Recognition Evaluation ===")

        for image_path in image_paths:
            result = database.observe(image_path)

            print(f"\nImage: {image_path.name}")
            print(f"Status: {result['status']}")
            print(f"Place ID: {result['place_id']}")
            print(f"Good matches: {result['good_matches']}")
            print(f"Score: {result['score']:.4f}")

            if result["status"] == "candidate":
                print("Candidate awaiting explicit approval.")
                approval = input(
                    f"Register {image_path.name} as a new place? [y/N]: "
                ).strip().lower()

                if approval == "y":
                    registered = database.register_candidate(image_path)
                    print(f"Registration result: {registered['status']}")
                    print(f"Registered ID: {registered['place_id']}")

        print("\n=== Registered Places ===")
        for place in database.list_places():
            print(f"{place['id']}: {place['image']}")


if __name__ == "__main__":
    main()
