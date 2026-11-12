
from itertools import combinations
from pathlib import Path

from autocar.visual_place_matcher import VisualPlaceMatcher


def main():
    image_dir = Path("data/visual_test")
    images = sorted(
        path
        for path in image_dir.iterdir()
        if path.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )

    if len(images) < 2:
        raise SystemExit("Add at least two images to data/visual_test.")

    matcher = VisualPlaceMatcher()

    print(f"Evaluating {len(images)} images\n")

    for first, second in combinations(images, 2):
        result = matcher.compare(first, second)

        print(f"{first.name} vs {second.name}")
        print(f"  Good matches: {result.good_matches}")
        print(f"  Score       : {result.score:.4f}")
        print(f"  Geometric inliers: {result.geometric_inliers}")
        print(f"  Inlier ratio     : {result.inlier_ratio:.4f}")
        print(f"  Decision    : {'MATCH' if result.is_same_place else 'NO MATCH'}")
        print()


if __name__ == "__main__":
    main()
