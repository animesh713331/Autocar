from pathlib import Path
from autocar.visual_place_matcher import VisualPlaceMatcher

ROOT = Path("data/linear_experiment")
locations = ["A", "C", "B"]

matcher = VisualPlaceMatcher()

references = {
    loc: sorted((ROOT / loc).glob("*.jpg"))
    for loc in locations
}

correct = 0
total = 0

print("\n===== EXISTING PROJECT MATCHER TEST =====")

for actual in locations:
    tests = sorted(
        (ROOT / "independent_test" / actual).glob("*.jpg")
    )

    for query in tests:
        scores = {}

        for location in locations:
            results = []

            for reference in references[location]:
                result = matcher.compare(reference, query)

                results.append({
                    "file": reference.name,
                    "score": result.score,
                    "matches": result.good_matches,
                    "inliers": result.geometric_inliers,
                    "accepted": result.is_same_place
                })

            best = max(results, key=lambda x: x["score"])
            scores[location] = best

        accepted = [
            loc for loc in locations
            if scores[loc]["accepted"]
        ]

        if accepted:
            predicted = max(
                accepted,
                key=lambda loc: scores[loc]["score"]
            )
        else:
            predicted = "UNKNOWN"

        total += 1
        correct += int(predicted == actual)

        print(f"\n{query.name}: actual={actual}, predicted={predicted}")

        for loc in locations:
            r = scores[loc]
            print(
                f"  {loc}: reference={r['file']}, "
                f"score={r['score']:.4f}, "
                f"matches={r['matches']}, "
                f"inliers={r['inliers']}, "
                f"accepted={r['accepted']}"
            )

print("\n===== SUMMARY =====")
print(f"Correct: {correct}/{total}")
print(f"Accuracy: {100 * correct / total:.2f}%")
