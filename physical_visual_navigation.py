import time
from pathlib import Path

from autocar.motor_control import Drivetrain
from autocar.camera import Camera
from autocar.visual_place_database import VisualPlaceDatabase


# -------- EXPERIMENT CONFIGURATION --------

PWM = 0.50
PULSE_DURATION = 0.50
SETTLE_TIME = 1.0

DATABASE_PATH = "data/visual_places"
OUTPUT_DIR = Path("physical_navigation_results")

EXPECTED_ROUTE = ["A", "C", "B"]

# ------------------------------------------


def observe(database, camera, stage):

    image_path = camera.capture()

    destination = OUTPUT_DIR / f"{stage}.jpg"
    OUTPUT_DIR.mkdir(exist_ok=True)

    import shutil
    shutil.copy2(image_path, destination)

    result = database.observe(destination)

    print("\n------------- VISUAL RESULT -------------")
    print("Image:", destination)
    print("Recognized place:", result["place_id"])
    print("Status:", result["status"])
    print("Score:", round(result["score"], 4))
    print("Good matches:", result["good_matches"])
    print("Geometric inliers:", result["geometric_inliers"])
    print("-----------------------------------------")

    return result


def main():

    drive = None
    camera = None

    pulse_number = 0
    last_recognized = None

    try:

        print("\nINITIALIZING ROBOT")
        drive = Drivetrain()
        camera = Camera()

        database = VisualPlaceDatabase(DATABASE_PATH)

        print("\nRegistered locations:",
              [p["id"] for p in database.list_places()])

        # Initial localization
        result = observe(database, camera, "initial_A")

        if result["place_id"] != "A":
            print("\nERROR: Robot is not confidently localized at A.")
            print("Position robot at reference location A and retry.")
            return

        print("\nSTART LOCATION A CONFIRMED!")

        print("\nFORWARD NAVIGATION TEST STARTED")
        print("Route: A -> C -> B")
        print("Each movement requires manual confirmation.")

        while True:

            command = input(
                "\nENTER = move forward | Q = quit: "
            ).strip().lower()

            if command == "q":
                print("Navigation stopped by user.")
                break

            pulse_number += 1

            print(f"\nFORWARD PULSE {pulse_number}")
            print("PWM:", PWM)
            print("Duration:", PULSE_DURATION, "seconds")

            try:
                drive.forward(PWM)
                time.sleep(PULSE_DURATION)

            finally:
                drive.stop()

            print("MOTORS STOPPED")

            time.sleep(SETTLE_TIME)

            result = observe(
                database,
                camera,
                f"pulse_{pulse_number:03d}"
            )

            place = result["place_id"]

            if result["status"] == "recognized":

                print("\nLOCATION IDENTIFIED:", place)

                if place == "B":
                    print("\nDESTINATION B REACHED!")
                    print("A -> C -> B demonstration completed.")
                    break

                if place == "C" and last_recognized != "C":
                    print("\nMIDPOINT C IDENTIFIED!")

                if place not in EXPECTED_ROUTE:
                    print("Unexpected route location. Pausing.")
                    break

                last_recognized = place

            else:
                print("\nLOCATION UNKNOWN / CANDIDATE")
                print("Do not assume the robot has reached C or B.")
                print("Inspect the camera view before continuing.")

        print("\nEXPERIMENT FINISHED")
        print("Forward pulses:", pulse_number)

    except KeyboardInterrupt:
        print("\nEMERGENCY USER INTERRUPTION")

    except Exception as error:
        print("\nERROR:", repr(error))

    finally:

        if drive:
            drive.stop()
            drive.close()

        if camera:
            camera.close()

        print("\nMOTORS STOPPED")
        print("HARDWARE RELEASED")


if __name__ == "__main__":
    main()
