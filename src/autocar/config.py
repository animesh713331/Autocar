"""
Central configuration: GPIO pin map, thresholds, file paths.
Edit this file to match your actual wiring — nothing else should need pin numbers.

Wiring assumption (common 4WD chassis, 2x L298N driver boards):
  - Left side motors (front-left + rear-left) wired in parallel to L298N #1, channel A
  - Right side motors (front-right + rear-right) wired in parallel to L298N #2, channel A
  This lets the car be steered as a 2-wheel differential-drive robot (skid steering).
  If you wire all 4 motors independently to 4 channels instead, extend motor_control.py.
"""

# ---- Motor driver (L298N) pins, BCM numbering ----
LEFT_MOTOR_FORWARD = 17
LEFT_MOTOR_BACKWARD = 27
LEFT_MOTOR_ENABLE = 18          # PWM-capable pin

RIGHT_MOTOR_FORWARD = 22
RIGHT_MOTOR_BACKWARD = 23
RIGHT_MOTOR_ENABLE = 13         # PWM-capable pin

# ---- Ultrasonic sensor (HC-SR04) ----
ULTRASONIC_TRIGGER = 5
ULTRASONIC_ECHO = 6
ULTRASONIC_MAX_DISTANCE_M = 2.0   # gpiozero DistanceSensor max range

# ---- Obstacle-avoidance behavior ----
STOP_DISTANCE_M = 0.20      # stop immediately if closer than this
SLOW_DISTANCE_M = 0.50      # start slowing down if closer than this
DRIVE_SPEED = 0.6           # 0.0 - 1.0
SLOW_SPEED = 0.5
AVOID_TURN_SECONDS = 0.6    # how long to turn away from an obstacle
SENSOR_POLL_HZ = 10         # how often to read the ultrasonic sensor per second

# ---- Camera / capture ----
CAPTURE_DIR = "captures"
CAPTURE_RESOLUTION = (1280, 720)

# ---- YOLO detection ----
# NOTE: we load the ncnn export (models/yolov8n_ncnn_model/), not the raw
# yolov8n.pt. Raw PyTorch inference crashes with an illegal-instruction
# error on the Pi 4's Cortex-A72 CPU — its optimized convolution kernels
# assume ARM dot-product instructions the A72 doesn't have. ncnn is built
# for ARM SBCs and avoids this entirely, and is faster besides.
# Generate it once with:
#   uv run python -c "from ultralytics import YOLO; YOLO('models/yolov8n.pt').export(format='ncnn')"
YOLO_MODEL_PATH = "models/yolov8n_ncnn_model"
YOLO_CONFIDENCE_THRESHOLD = 0.5

# ---- Voice/text command ----
STOP_AND_PHOTO_PHRASES = [
    "stop and take a photo",
    "stop and take photo",
    "stop and take picture",
]
START_PHRASES = ["start", "go", "resume"]
STOP_PHRASES = ["stop"]

# ---- Web dashboard (control from phone or laptop browser) ----
WEB_HOST = "0.0.0.0"   # listen on all network interfaces so phone/laptop on same Wi-Fi can reach it
WEB_PORT = 5000
PHOTO_TIMEOUT_SECONDS = 30   # how long the web UI waits for a photo to be captured + detected
