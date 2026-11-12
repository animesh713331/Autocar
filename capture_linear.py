import time
from pathlib import Path
from autocar.camera import Camera

OUTPUT = Path("data/linear_experiment")
TOTAL_IMAGES = 12
INTERVAL = 3

OUTPUT.mkdir(parents=True, exist_ok=True)

camera = Camera()

try:
    print("\nLinear experiment starting.")
    print("Start at Point A. Move the robot manually along a straight path.")
    print("Capturing one image every 3 seconds...\n")

    for i in range(1, TOTAL_IMAGES + 1):
        captured = Path(camera.capture())
        destination = OUTPUT / f"frame_{i:03d}.jpg"
        captured.replace(destination)

        print(f"[{i}/{TOTAL_IMAGES}] Saved {destination}")

        if i < TOTAL_IMAGES:
            time.sleep(INTERVAL)

finally:
    camera.close()

print("\nCapture completed.")
