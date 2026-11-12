from pathlib import Path
import cv2
import csv

folder = Path("data/linear_experiment")
images = sorted(folder.glob("frame_*.jpg"))

orb = cv2.ORB_create(nfeatures=1500)
matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

features = {}

for path in images:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    keypoints, descriptors = orb.detectAndCompute(image, None)
    features[path.name] = (keypoints, descriptors)

output = []

print("\nCONSECUTIVE FRAME ANALYSIS")
print("-" * 65)

for i in range(len(images) - 1):
    name1, name2 = images[i].name, images[i + 1].name
    kp1, des1 = features[name1]
    kp2, des2 = features[name2]

    if des1 is None or des2 is None:
        good = []
    else:
        pairs = matcher.knnMatch(des1, des2, k=2)
        good = [m for pair in pairs if len(pair) == 2
                for m, n in [pair] if m.distance < 0.75 * n.distance]

    inliers = 0
    if len(good) >= 4:
        src = cv2.KeyPoint_convert(kp1, [m.queryIdx for m in good])
        dst = cv2.KeyPoint_convert(kp2, [m.trainIdx for m in good])
        _, mask = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)
        if mask is not None:
            inliers = int(mask.sum())

    print(f"{name1} -> {name2}: "
          f"matches={len(good)}, inliers={inliers}")

    output.append([name1, name2, len(good), inliers])

with open(folder / "analysis.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["frame_1", "frame_2", "good_matches", "ransac_inliers"])
    writer.writerows(output)

print("\nSaved:", folder / "analysis.csv")
