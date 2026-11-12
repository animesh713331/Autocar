
import argparse

from autocar.visual_place_matcher import VisualPlaceMatcher


def main():
    parser = argparse.ArgumentParser(
        description="Compare two images for visual place recognition."
    )
    parser.add_argument("reference", help="Path to the stored reference image")
    parser.add_argument("query", help="Path to the newly captured image")
    args = parser.parse_args()

    matcher = VisualPlaceMatcher()
    result = matcher.compare(args.reference, args.query)

    print(f"Reference keypoints : {result.reference_keypoints}")
    print(f"Query keypoints     : {result.query_keypoints}")
    print(f"Good feature matches: {result.good_matches}")
    print(f"Match score         : {result.score:.4f}")
    print(f"Matcher decision    : {'MATCH' if result.is_same_place else 'NO MATCH'}")


if __name__ == "__main__":
    main()
