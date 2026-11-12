
import csv
import time
from pathlib import Path
from datetime import datetime

from autocar.camera import Camera
from autocar.motor_control import Drivetrain
from autocar.visual_place_database import VisualPlaceDatabase


# ---------------- CONFIGURATION ----------------

TARGET_PLACE = "C"

PWM = 0.50
CAPTURE_INTERVAL = 0.5
MAX_RUN_SECONDS = 15

REQUIRED_CONSECUTIVE_DETECTIONS = 2

DATABASE_PATH = "data/visual_places"

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / (
    f"a_to_c_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
)


# ---------------- MAIN TEST ----------------

def main():

    drive = None
    camera = None

    consecutive_c = 0
    motors_started = False

    start_time = None

    try:
        print("\n===================================")
        print("   VISION-BASED A TO C TEST")
        print("===================================")

        print("\nInitializing drivetrain...")
        drive = Drivetrain()

        print("Initializing camera...")
        camera = Camera()

        print("Loading visual place database...")
        database = VisualPlaceDatabase(DATABASE_PATH)

        print("\nAvailable places:", database.list_places())

        # Verify starting location A
        print("\nChecking starting location A...")

        initial_image = camera.capture()
        initial_result = database.observe(initial_image)

        print(
            f"Initial Place={initial_result['place_id']} | "
            f"Status={initial_result['status']} | "
            f"Score={initial_result['score']:.4f}"
        )

        if (
            initial_result["place_id"] != "A"
            or initial_result["status"] != "recognized"
        ):
            print("\nSTART LOCATION A NOT VERIFIED.")
            print("Motors will remain stopped.")
            return

        print("\nStarting A -> C movement...")
        print("Target: C")
        print("PWM:", PWM)
        print("Maximum runtime:", MAX_RUN_SECONDS, "seconds")
        print(
            "Required consecutive C detections:",
            REQUIRED_CONSECUTIVE_DETECTIONS
        )

        print("\nStarting motors...\n")

        start_time = time.monotonic()

        with open(LOG_FILE, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "elapsed_seconds",
                "place",
                "status",
                "score",
                "good_matches",
                "geometric_inliers",
                "consecutive_c",
                "event"
            ])

            drive.forward(PWM)
            motors_started = True

            while True:

                cycle_start = time.monotonic()
                elapsed = cycle_start - start_time

                # Safety timeout
                if elapsed >= MAX_RUN_SECONDS:
                    print("\nTIME LIMIT REACHED.")
                    writer.writerow([
                        elapsed, "", "", "", "", "",
                        consecutive_c, "TIMEOUT"
                    ])
                    break

                # Capture and recognize current view
                image_path = camera.capture()
                result = database.observe(image_path)

                place = result["place_id"]
                status = result["status"]

                # Count consecutive C detections
                if place == TARGET_PLACE and status == "recognized":
                    consecutive_c += 1
                else:
                    consecutive_c = 0

                print(
                    f"\n[{elapsed:.2f}s] "
                    f"Place={place} | "
                    f"Status={status} | "
                    f"Score={result['score']:.4f} | "
                    f"Matches={result['good_matches']} | "
                    f"Inliers={result['geometric_inliers']} | "
                    f"C streak={consecutive_c}"
                )

                # Stop automatically after two consecutive C detections
                if consecutive_c >= REQUIRED_CONSECUTIVE_DETECTIONS:

                    drive.stop()
                    motors_started = False

                    print("\n===================================")
                    print("TARGET C REACHED")
                    print("MOTORS STOPPED")
                    print("===================================")

                    writer.writerow([
                        elapsed,
                        place,
                        status,
                        result["score"],
                        result["good_matches"],
                        result["geometric_inliers"],
                        consecutive_c,
                        "TARGET_REACHED"
                    ])

                    break

                # Log normal observation
                writer.writerow([
                    elapsed,
                    place,
                    status,
                    result["score"],
                    result["good_matches"],
                    result["geometric_inliers"],
                    consecutive_c,
                    "MOVING"
                ])

                file.flush()

                # Maintain capture interval where processing allows
                processing_time = time.monotonic() - cycle_start
                remaining_time = CAPTURE_INTERVAL - processing_time

                if remaining_time > 0:
                    time.sleep(remaining_time)

        print("\nTest log saved:", LOG_FILE)

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")

    except Exception as error:
        print("\nERROR:", error)
        raise

    finally:

        # Always attempt to stop motors
        if drive is not None:
            try:
                drive.stop()
                print("Drivetrain stopped.")
            except Exception as error:
                print("Motor stop error:", error)

        if camera is not None:
            try:
                camera.close()
                print("Camera closed.")
            except Exception as error:
                print("Camera close error:", error)

        if drive is not None:
            try:
                drive.close()
            except Exception as error:
                print("Drivetrain close error:", error)

        print("\nA TO C TEST FINISHED.")


if __name__ == "__main__":
    main()
