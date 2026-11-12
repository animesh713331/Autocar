import cv2
import numpy as np
from pathlib import Path

ROOT = Path("data/linear_experiment")
LOCATIONS = ["A", "C", "B"]

orb = cv2.ORB_create(nfeatures=1500)
matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

def extract(path):
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise ValueError(f"Cannot read {path}")

    keypoints, descriptors = orb.detectAndCompute(image, None)
    return keypoints, descriptors

def compare(query, reference):
    kp1, des1 = query
    kp2, des2 = reference

    if des1 is None or des2 is None:
        return 0, 0, 0.0

    pairs = matcher.knnMatch(des1, des2, k=2)

    good = [
        m for pair in pairs if len(pair) == 2
        for m, n in [pair]
        if m.distance < 0.75 * n.distance
    ]

    if len(good) < 8:
        return len(good), 0, 0.0

    src = np.float32(
        [kp1[m.queryIdx].pt for m in good]
    ).reshape(-1, 1, 2)

    dst = np.float32(
        [kp2[m.trainIdx].pt for m in good]
    ).reshape(-1, 1, 2)

    _, mask = cv2.findHomography(
        src, dst, cv2.RANSAC, 5.0
    )

    inliers = int(mask.sum()) if mask is not None else 0
    ratio = inliers / len(good) if good else 0

    return len(good), inliers, ratio


# Load reference database
database = {}

for location in LOCATIONS:
    database[location] = []

    for path in sorted((ROOT / location).glob("*.jpg")):
        database[location].append((path.name, extract(path)))

# Independent test
print("\n========== INDEPENDENT LOCALIZATION ==========")

correct = 0
total = 0

for actual in LOCATIONS:
    test_folder = ROOT / "independent_test" / actual

    for test_path in sorted(test_folder.glob("*.jpg")):
        query = extract(test_path)
        location_results = {}

        for location in LOCATIONS:
            results = []

            for ref_name, reference in database[location]:
                good, inliers, ratio = compare(query, reference)
                results.append((inliers, good, ratio, ref_name))

            # Average the three strongest geometric matches
            results.sort(key=lambda x: x[0], reverse=True)
            top = results[:3]

            score = np.mean([x[0] for x in top])
            location_results[location] = (score, top)

        predicted = max(
            location_results,
            key=lambda x: location_results[x][0]
        )

        total += 1
        if predicted == actual:
            correct += 1

        print(f"\nTest: {test_path.name}")
        print(f"Actual: {actual} | Predicted: {predicted}")

        for location in LOCATIONS:
            score, top = location_results[location]
            print(
                f"  {location}: mean_top3_inliers={score:.1f}, "
                f"best_matches={top[0][1]}, "
                f"best_inliers={top[0][0]}, "
                f"best_inlier_ratio={top[0][2]:.3f}, "
                f"reference={top[0][3]}"
            )

print("\n========== FINAL RESULT ==========")
print(f"Correct predictions: {correct}/{total}")
print(f"Observed accuracy: {100 * correct / total:.2f}%")
