# Vision-Based Robot Navigation

A fixed-route, vision-based indoor robot navigation prototype developed during a research internship at IIIT Dharwad.

The project uses a Raspberry Pi camera and ORB-based visual feature matching to recognize previously registered locations. A navigation graph and shortest-path planner are used to plan routes between known locations.

## 1. Project Overview

The demonstration environment contains three visual locations:

- **A** — Starting location
- **C** — Intermediate location
- **B** — Destination

The intended demonstration supports navigation in both directions:

- A → C → B
- B → C → A

The current scope is a fixed indoor route. It does not claim general-purpose autonomous navigation or full SLAM.

## 2. Hardware

| Component | Hardware |
|---|---|
| Main computer | Raspberry Pi 4B |
| Camera | Raspberry Pi Camera Module V2 (IMX219) |
| Motor driver | L298N dual H-bridge |
| Drive system | Four-wheel DC geared motor chassis |
| Motor arrangement | Left and right motor pairs |
| Power | Separate Raspberry Pi supply and motor battery pack |

### GPIO configuration

BCM numbering, as currently configured in `src/autocar/config.py`:

| Function | GPIO |
|---|---:|
| Left motor forward | 17 |
| Left motor backward | 27 |
| Left motor enable (PWM) | 18 |
| Right motor forward | 22 |
| Right motor backward | 23 |
| Right motor enable (PWM) | 13 |
| HC-SR04 trigger | 5 |
| HC-SR04 echo | 6 |

The motor-control software uses two independently controlled sides. The current physical setup uses one dual-channel L298N board, with the left and right motor pairs connected to separate channels.

**Electrical safety:** Use a suitable regulated supply for the Raspberry Pi, a correctly rated motor battery and a common ground between the Pi and motor driver. Do not connect the motor supply directly to the Pi GPIO or 5V rail. Check the L298N board's jumper and enable-pin configuration before powering the motors.

## 3. Software Architecture

The current navigation pipeline is:

```text
Raspberry Pi Camera
        |
        v
Image Capture
        |
        v
ORB Feature Extraction
        |
        v
Visual Place Database
        |
        v
Visual Place Matching
        |
        v
Location Recognition
        |
        v
Navigation Graph
        |
        v
Shortest Path Planning
        |
        v
Navigation Decision

Visual localization
The system registers reference images for known locations and compares newly captured images against the visual database.

The visual-place database currently contains:
- Location A: 5 reference images
- Location C: 5 reference images
- Location B: 5 reference images
Total: 15 registered reference images.

The matching implementation uses ORB features and geometric verification.
Navigation graph
The current graph is stored in data/navigation_map.json.

It contains three nodes and bidirectional connections:
A <------> C <------> B


The path planner supports both directions:
A -> B : A, C, B
B -> A : B, C, A


The current graph does not contain measured edge distances. Do not interpret the graph as a metrically calibrated map.
Navigation decisions
The visual navigation bridge connects image-based localization with route planning and navigation decisions.

The current controller provides advisory navigation decisions. Transition execution and steering direction metadata have not yet been verified for autonomous movement.
4. Repository Structure
autocar-project/
├── data/
│   ├── navigation_map.json
│   ├── visual_places/
│   │   ├── places.json
│   │   └── images/
│   ├── linear_experiment/
│   │   ├── A/
│   │   ├── C/
│   │   ├── B/
│   │   └── independent_test/
│   └── visual_test/
│
├── scripts/
│   ├── compare_places.py
│   ├── demo_navigation_graph.py
│   ├── evaluate_navigation.py
│   ├── evaluate_places.py
│   ├── integrated_navigation_demo.py
│   └── setup_pi.sh
│
├── src/autocar/
│   ├── camera.py
│   ├── config.py
│   ├── motor_control.py
│   ├── visual_place_database.py
│   ├── visual_place_matcher.py
│   ├── visual_navigation_bridge.py
│   ├── navigation_controller.py
│   ├── navigation_orchestrator.py
│   ├── path_planner.py
│   ├── map_builder.py
│   ├── map_storage.py
│   └── ...
│
├── models/
├── tests and evaluation scripts
├── pyproject.toml
├── uv.lock
└── README.md


5. Software Requirements
- Raspberry Pi OS / Debian-based Linux
- Python 3.13 (tested environment)
- OpenCV
- NumPy
- Picamera2
- gpiozero
- lgpio or a compatible Raspberry Pi GPIO backend
The project uses pyproject.toml for Python dependencies. Raspberry Pi camera and GPIO support may require system packages installed through APT.
6. Raspberry Pi Setup
Step 1: Clone the repository
git clone <YOUR_REPOSITORY_URL>
cd autocar-project


Step 2: Install system dependencies
Install the Raspberry Pi camera and GPIO packages using the package manager:
sudo apt update
sudo apt install -y python3-venv python3-picamera2 python3-lgpio


Step 3: Create the virtual environment
The system-site-packages option allows the virtual environment to access the APT-installed Picamera2 and GPIO packages.
python3 -m venv --system-site-packages .venv
source .venv/bin/activate


Step 4: Install the project
pip install -e .


If a dependency is already supplied by the Raspberry Pi system packages, verify compatibility before installing another copy into the virtual environment.
Step 5: Configure hardware
Review:
src/autocar/config.py


Verify GPIO wiring, motor-driver connections, battery voltage and common ground before running motor-control code.
7. Experimental Dataset
The repository includes the visual-place reference dataset and independent test images.
data/
├── visual_places/
│   ├── places.json
│   └── images/
└── linear_experiment/
    ├── A/
    ├── C/
    ├── B/
    └── independent_test/
        ├── A/
        ├── C/
        └── B/


The independent test images are separate from the registered reference images.

The dataset is intended to reproduce the stationary visual-localization experiments. It does not establish performance under continuous robot motion.
8. Verified Results
The following results were observed during development:
Experiment	Observed result
Reference database	15 images registered across A, C and B
Independent localization test	9/9 correct in the recorded stationary test
Persisted database test	9/9 correct in the recorded stationary test
Raspberry Pi camera localization	A, C and B each recognized in separate stationary captures
A to B route planning	A → C → B
B to A route planning	B → C → A
Navigation integration	Localization and advisory route planning connected successfully

Hardware-in-the-loop localization
Separate stationary captures from the Raspberry Pi Camera V2 were successfully recognized at A, C and B.

These results demonstrate stationary camera-based place recognition on the target hardware. They should not be interpreted as a moving-robot localization accuracy measurement.
9. Current Implementation Status
Implemented
- Raspberry Pi camera capture.
- ORB-based visual feature matching.
- Multi-reference visual-place database.
- Persistent visual-place storage.
- Independent stationary localization evaluation.
- Navigation graph with A, C and B.
- Bidirectional shortest-path planning.
- Navigation orchestrator and visual navigation bridge.
- GPIO-based differential drivetrain control interface.
Pending / Not yet verified
- Reliable motor startup and power delivery through the L298N under chassis load.
- Calibrated straight-line movement on the floor.
- Repeated localization while the robot is moving.
- Integration of recognized locations with closed-loop motor execution.
- Autonomous end-to-end A-to-B and B-to-A demonstrations.
- Measured route distances and steering calibration.
The current navigation decisions are advisory. Full autonomous movement has not yet been demonstrated.
10. Limitations and Future Work
The current prototype focuses on a constrained, fixed indoor route and visual place recognition.

Potential future work includes:
1. Verify motor power delivery and calibrate the drivetrain.
2. Test visual localization during controlled robot movement.
3. Implement verified transition execution.
4. Measure route segments and improve navigation reliability.
5. Extend the visual map to additional locations.
6. Evaluate performance under different lighting and environmental conditions.
11. Acknowledgement
Developed as part of a research internship at the Indian Institute of Information Technology Dharwad (IIIT Dharwad), under the guidance of Dr. Nataraj K. S.

Project status: Vision-based localization and bidirectional route planning implemented and tested; autonomous drivetrain integration remains under development.
