
<div align="center">

# Vision-Based Robot Navigation 🤖

### Intelligent Indoor Navigation Using Computer Vision and Raspberry Pi

A vision-based indoor robot navigation system that recognizes predefined locations, plans bidirectional routes, and interfaces with a differential-drive robotic platform.

**Developed at IIIT Dharwad | Research Internship Project**

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?logo=opencv)
![Raspberry Pi](https://img.shields.io/badge/Hardware-Raspberry%20Pi-red?logo=raspberrypi)
![Platform](https://img.shields.io/badge/Platform-Linux-black?logo=linux)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>

---

## 📌 Overview

**Vision-Based Robot Navigation** is an indoor robotic navigation project that combines computer vision, visual place recognition, graph-based path planning, and embedded hardware control.

The robot uses a Raspberry Pi Camera Module V2 to capture environmental images and identify predefined locations through ORB (Oriented FAST and Rotated BRIEF) feature matching with geometric verification.

A navigation graph represents the indoor environment, allowing the system to calculate routes between registered locations using a shortest-path algorithm.

The project demonstrates how visual perception and graph-based planning can be integrated into a compact embedded robotic platform.

## ✨ Key Features

- **Visual Place Recognition:** Recognizes predefined indoor locations using ORB feature matching.
- **Multi-Reference Database:** Stores multiple reference images for each registered location.
- **Geometric Verification:** Uses geometric consistency to improve visual matching reliability.
- **Bidirectional Route Planning:** Calculates routes between locations in both directions.
- **Graph-Based Navigation:** Represents the environment using nodes and bidirectional connections.
- **Embedded Vision:** Performs image capture and visual processing on Raspberry Pi.
- **Differential Drive Control:** Provides independent left and right motor control through an L298N driver.
- **Persistent Visual Mapping:** Maintains registered visual locations and navigation data.

## 🗺️ Navigation Environment

The demonstration environment consists of three predefined visual locations:

| Location | Description |
|:---:|---|
| A | Starting Location |
| C | Intermediate Location |
| B | Destination |

### Supported Routes

<div align="center">

**Route 1: A → C → B**

```text
     A  ───────── C ───────── B
   Start       Intermediate  Destination
```

**Route 2: B → C → A**

```text
     B  ───────── C ───────── A
 Destination  Intermediate     Start
```

</div>

The navigation graph is bidirectional, enabling route planning from either endpoint.

## 🏗️ System Architecture

```text
              ENVIRONMENT
                   |
                   v
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
          Feature Matching and
          Geometric Verification
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
         Navigation Orchestrator
                   |
                   v
          Navigation Controller
                   |
                   v
          Drivetrain Interface
                   |
                   v
             L298N Driver
                   |
                   v
           DC Geared Motors
```

## 🔧 Hardware Components

| Component | Specification |
|---|---|
| Main Controller | Raspberry Pi 4B |
| Camera | Raspberry Pi Camera Module V2 (IMX219) |
| Motor Driver | L298N Dual H-Bridge |
| Drive System | Four-wheel DC geared motor chassis |
| Motor Configuration | Left and right motor pairs |
| Power Supply | Separate Raspberry Pi and motor power supplies |
| Distance Sensor | HC-SR04 Ultrasonic Sensor |

### GPIO Pin Configuration

The project uses BCM GPIO numbering.

| Function | BCM GPIO |
|---|---:|
| Left Motor Forward | 17 |
| Left Motor Backward | 27 |
| Left Motor Enable (PWM) | 18 |
| Right Motor Forward | 22 |
| Right Motor Backward | 23 |
| Right Motor Enable (PWM) | 13 |
| Ultrasonic Trigger | 5 |
| Ultrasonic Echo | 6 |

The drivetrain interface provides independent control of the left and right motor channels, supporting forward, backward, left-turn, right-turn, and stop operations.

**Electrical Note:** Use a regulated Raspberry Pi power supply, a suitably rated motor battery, and a common ground between the Raspberry Pi and motor driver. Verify motor-driver connections and voltage levels before operation. The HC-SR04 echo signal must be appropriately voltage-divided before connecting to a Raspberry Pi GPIO.

## 💻 Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Computer Vision | OpenCV |
| Feature Detection | ORB |
| Numerical Processing | NumPy |
| Camera Interface | Picamera2, libcamera |
| GPIO Control | gpiozero, lgpio |
| Path Planning | Graph-Based Shortest Path |
| Embedded Platform | Raspberry Pi 4B |
| Development Environment | Linux, VS Code |

## 📂 Project Structure

```text
autocar-project/
│
├── data/
│   ├── navigation_map.json
│   │
│   ├── visual_places/
│   │   ├── places.json
│   │   └── images/
│   │
│   ├── linear_experiment/
│   │   ├── A/
│   │   ├── C/
│   │   ├── B/
│   │   └── independent_test/
│   │
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
├── src/
│   └── autocar/
│       ├── camera.py
│       ├── config.py
│       ├── motor_control.py
│       ├── visual_place_database.py
│       ├── visual_place_matcher.py
│       ├── visual_navigation_bridge.py
│       ├── navigation_controller.py
│       ├── navigation_orchestrator.py
│       ├── path_planner.py
│       ├── map_builder.py
│       └── map_storage.py
│
├── models/
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

## 🧠 Visual Place Recognition

The visual localization subsystem identifies predefined locations using reference images.

### Registered Visual Database

| Location | Reference Images |
|:---:|---:|
| A | 5 |
| C | 5 |
| B | 5 |
| **Total** | **15** |

### Recognition Pipeline

1. Capture an image using the Raspberry Pi Camera.
2. Extract ORB keypoints and descriptors.
3. Compare the captured image against registered reference images.
4. Perform feature matching.
5. Apply geometric verification.
6. Determine the recognized visual location.

The system maintains a persistent database of reference images, allowing previously registered locations to be reused during localization.

## 🧭 Navigation and Path Planning

The indoor environment is represented as a graph.

```text
A <------> C <------> B
```

The graph is stored in:

```text
data/navigation_map.json
```

The shortest-path planner calculates routes between registered locations.

| Source | Destination | Planned Route |
|---|---|---|
| A | B | A → C → B |
| B | A | B → C → A |
| A | C | A → C |
| C | B | C → B |

The navigation architecture connects visual localization with route planning through the navigation bridge, orchestrator, and controller.

## 📊 Experimental Evaluation

The following results were obtained during the development and evaluation of the visual localization subsystem.

| Experiment | Observed Result |
|---|---|
| Registered Visual Database | 15 reference images |
| Independent Localization Test | 9/9 correct |
| Persisted Database Test | 9/9 correct |
| Raspberry Pi Camera Localization | A, C and B recognized in separate stationary captures |
| A-to-B Route Planning | A → C → B |
| B-to-A Route Planning | B → C → A |
| Navigation Integration | Visual localization connected with advisory route planning |

### Experimental Dataset

The repository includes:

- Registered reference images for A, C and B.
- Independent localization test images.
- Linear movement experiment captures.
- Visual matching evaluation data.

The independent test images are separate from the registered reference database.

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd autocar-project
```

### 2. Install System Dependencies

On Raspberry Pi OS or a compatible Debian-based system:

```bash
sudo apt update

sudo apt install -y \
    python3-venv \
    python3-picamera2 \
    python3-lgpio
```

### 3. Create a Virtual Environment

```bash
python3 -m venv --system-site-packages .venv

source .venv/bin/activate
```

### 4. Install the Project

```bash
pip install -e .
```

### 5. Configure Hardware

Review the hardware configuration:

```text
src/autocar/config.py
```

Verify the GPIO pin assignments, motor-driver wiring, camera connection, power supply and common ground.

### 6. Run the Navigation Demonstration

Available demonstration and evaluation scripts are located in:

```text
scripts/
```

For example:

```bash
python scripts/demo_navigation_graph.py
```

Individual scripts can be executed according to their implementation and hardware requirements.

## 🔮 Applications

The concepts demonstrated in this project can be extended to:

- Indoor service robots.
- Educational robotics platforms.
- Vision-based indoor localization.
- Embedded computer vision systems.
- Fixed-route delivery robots.
- Smart institutional and laboratory environments.
- Autonomous mobile robotics research.

## 👨‍💻 Author

**Animesh Kumar Singh**

B.Tech – Computer Science and Engineering (IoT)

GitHub: [@animesh713331](https://github.com/animesh713331)
Portfolio : [Animesh Kumar Singh](https://animeshkumarsingh.vercel.app/)
LinkedIn: [Animesh Kumar Singh](https://www.linkedin.com/in/animeshkrsingh/)

---

<div align="center">

### Building Intelligent Systems at the Edge 🚀

*Computer Vision · Embedded AI · Robotics · IoT*

</div>
