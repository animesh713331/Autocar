import cv2
from pathlib import Path

folder = Path("movement_test_results")

movements = ["FORWARD", "BACKWARD", "LEFT_TURN", "RIGHT_TURN"]

panels = []

for movement in movements:
    before_files = sorted(folder.glob(f"{movement}_BEFORE_*.jpg"))
    after_files = sorted(folder.glob(f"{movement}_AFTER_*.jpg"))

    if not before_files or not after_files:
        print("Missing images:", movement)
        continue

    before = cv2.imread(str(before_files[-1]))
    after = cv2.imread(str(after_files[-1]))

    if before is None or after is None:
        print("Could not read images:", movement)
        continue

    height = 360
    before = cv2.resize(
        before, (int(before.shape[1] * height / before.shape[0]), height)
    )
    after = cv2.resize(
        after, (int(after.shape[1] * height / after.shape[0]), height)
    )

    cv2.putText(before, movement + " BEFORE",
                (15, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    cv2.putText(after, movement + " AFTER",
                (15, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 255, 0), 2)

    panels.append(cv2.hconcat([before, after]))

if panels:
    sheet = cv2.vconcat(panels)
    output = folder / "movement_comparison.jpg"
    cv2.imwrite(str(output), sheet)
    print("Comparison saved:", output.resolve())
else:
    print("No image pairs found.")
