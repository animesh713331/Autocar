import csv
import time
import shutil
from pathlib import Path
from datetime import datetime

from autocar.motor_control import Drivetrain
from autocar.camera import Camera
from autocar.visual_place_database import VisualPlaceDatabase


# ---------------- TEST CONFIGURATION ----------------

PWM = 0.50

MOVEMENTS = [
    ("FORWARD", 1.0),
    ("BACKWARD", 1.0),
    ("LEFT_TURN", 0.5),
    ("RIGHT_TURN", 0.5),
]

DATABASE_PATH = "data/visual_places"
OUTPUT_DIR = Path("movement_test_results")

SETTLE_TIME = 1.0

# ----------------------------------------------------


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def capture_image(camera, stage):
    """Capture and preserve a uniquely named image."""

    original_path = Path(camera.capture())

    OUTPUT_DIR.mkdir(exist_ok=True)

    saved_path = OUTPUT_DIR / f"{stage}_{timestamp()}.jpg"

    shutil.copy2(original_path, saved_path)

    print(f"Image saved: {saved_path}")

    return str(saved_path)


def recognize_place(database, image_path):
    """Recognize a captured image using the existing database."""

    try:
        result = database.observe(image_path)

        print("\nVisual localization:")
        print(f"Place: {result['place_id']}")
        print(f"Status: {result['status']}")
        print(f"Score: {result['score']:.4f}")
        print(f"Good matches: {result['good_matches']}")
        print(f"Geometric inliers: {result['geometric_inliers']}")

        return result

    except Exception as error:
        print("Localization error:", error)

        return {
            "place_id": None,
            "status": "error",
            "score": 0,
            "good_matches": 0,
            "geometric_inliers": 0,
        }


def log_observation(writer, stage, image_path, result):

    writer.writerow([
        stage,
        image_path,
        result["place_id"],
        result["status"],
        result["score"],
        result["good_matches"],
        result["geometric_inliers"],
        "",
        "",
        "",
    ])


def compare_images(database, before_path, after_path):
    """Compare camera views using the existing ORB matcher."""

    result = database.matcher.compare(before_path, after_path)

    print("\nORB VISUAL COMPARISON")
    print("---------------------")
    print("Good matches:", result.good_matches)
    print("Similarity score:", round(result.score, 4))
    print("Geometric inliers:", result.geometric_inliers)
    print("Inlier ratio:", round(result.inlier_ratio, 4))
    print("Same-place decision:", result.is_same_place)

    return result


def run_movement(drive, camera, database, writer,
                 movement_name, duration):

    print("\n" + "=" * 45)
    print("MOVEMENT:", movement_name)
    print("PWM:", PWM)
    print("Duration:", duration, "seconds")
    print("=" * 45)

    input("Position robot safely and press ENTER...")

    # Capture before movement
    before_path = capture_image(
        camera, movement_name + "_BEFORE"
    )

    before_result = recognize_place(database, before_path)

    log_observation(
        writer,
        movement_name + "_BEFORE",
        before_path,
        before_result
    )

    input("Press ENTER to execute movement...")

    try:
        if movement_name == "FORWARD":
            drive.forward(PWM)

        elif movement_name == "BACKWARD":
            drive.backward(PWM)

        elif movement_name == "LEFT_TURN":
            drive.turn_left(PWM)

        elif movement_name == "RIGHT_TURN":
            drive.turn_right(PWM)

        print("Movement executing...")
        time.sleep(duration)

    finally:
        drive.stop()
        print("MOTORS STOPPED")

    time.sleep(SETTLE_TIME)

    # Capture after movement
    after_path = capture_image(
        camera, movement_name + "_AFTER"
    )

    after_result = recognize_place(database, after_path)

    log_observation(
        writer,
        movement_name + "_AFTER",
        after_path,
        after_result
    )

    # Compare before and after views
    try:
        comparison = compare_images(
            database,
            before_path,
            after_path
        )

        writer.writerow([
            movement_name + "_ORB_COMPARISON",
            before_path + " | " + after_path,
            "",
            "",
            comparison.score,
            comparison.good_matches,
            comparison.geometric_inliers,
            comparison.inlier_ratio,
            comparison.is_same_place,
            "",
        ])

    except Exception as error:
        print("ORB comparison error:", error)

    print("\nCompleted:", movement_name)


def main():

    drive = None
    camera = None

    OUTPUT_DIR.mkdir(exist_ok=True)

    csv_path = OUTPUT_DIR / "movement_report.csv"

    try:
        print("\nINITIALIZING HARDWARE")

        drive = Drivetrain()
        camera = Camera()

        print("Loading visual place database...")

        database = VisualPlaceDatabase(DATABASE_PATH)

        places = database.list_places()

        print("Registered places:",
              [place["id"] for place in places])

        if not places:
            raise RuntimeError("Visual database is empty!")

        with open(csv_path, "w", newline="") as file:

            writer = csv.writer(file)

            writer.writerow([
                "Stage",
                "Image Paths",
                "Recognized Place",
                "Status",
                "Score",
                "Good Matches",
                "Geometric Inliers",
                "Inlier Ratio",
                "Same Place",
                "Notes",
            ])

            # Initial localization
            print("\nINITIAL CAMERA OBSERVATION")

            initial_path = capture_image(camera, "INITIAL")

            initial_result = recognize_place(
                database, initial_path
            )

            log_observation(
                writer,
                "INITIAL",
                initial_path,
                initial_result
            )

            # Execute all four movement tests
            for movement_name, duration in MOVEMENTS:

                run_movement(
                    drive,
                    camera,
                    database,
                    writer,
                    movement_name,
                    duration
                )

        print("\n" + "=" * 45)
        print("ALL MOVEMENT TESTS COMPLETED")
        print("=" * 45)

        print("Report:", csv_path)
        print("Images:", OUTPUT_DIR.resolve())

    except KeyboardInterrupt:
        print("\nTEST INTERRUPTED BY USER")

    except Exception as error:
        print("\nTEST ERROR:", repr(error))

    finally:

        if drive:
            drive.stop()
            drive.close()

        if camera:
            camera.close()

        print("\nMotors stopped.")
        print("Hardware resources released.")


if __name__ == "__main__":
    main()
