# autocar

Autonomous obstacle-avoiding car on a Raspberry Pi 4B (Debian 13 "Trixie").
Drives forward on its own, avoids obstacles with an ultrasonic sensor, and on
the command **"STOP AND TAKE A PHOTO"** it stops, takes a picture, runs YOLO
object detection, and tells you what it sees.

## Project layout

```
autocar/
├── pyproject.toml          # uv-managed project, Python 3.11
├── scripts/setup_pi.sh     # one-time Pi setup (run this first)
├── models/                 # yolov8n.pt goes here (downloaded by setup script)
├── captures/                # photos saved here at runtime
└── src/autocar/
    ├── config.py            # ALL pin numbers + tunable thresholds live here
    ├── motor_control.py      # L298N differential drive (left/right sides)
    ├── ultrasonic.py         # HC-SR04 distance sensor
    ├── camera.py             # picamera2 still capture
    ├── detector.py           # YOLOv8 inference + plain-English description
    ├── command_listener.py   # reads "STOP AND TAKE A PHOTO" from the terminal
    ├── navigation.py         # the main drive / avoid / photo loop
    └── main.py               # entry point
```

## Hardware wiring (matches `config.py` defaults — edit both together)

| Signal | Raspberry Pi BCM pin |
|---|---|
| Left motors forward | 17 |
| Left motors backward | 27 |
| Left motors enable (PWM) | 18 |
| Right motors forward | 22 |
| Right motors backward | 23 |
| Right motors enable (PWM) | 13 |
| HC-SR04 trigger | 5 |
| HC-SR04 echo | 6 (**use a voltage divider — echo is 5V, Pi GPIO is 3.3V**) |

Wire the 4 DC motors as two pairs (front-left + rear-left → one L298N
channel; front-right + rear-right → the other), so the car steers like a
tank/skid-steer robot. If you'd rather control all 4 motors independently,
say so and I'll extend `motor_control.py`.

## YOLO model

`models/yolov8n_ncnn_model/` ships pre-exported in this repo, ready to run —
you do **not** need to run any export step. This matters because raw
PyTorch inference (`yolov8n.pt`) crashes with an illegal-instruction error
on the Pi 4's Cortex-A72 CPU (its optimized convolution kernels assume ARM
dot-product instructions the A72 doesn't have), and exporting to ncnn *on
the Pi* hits the same crash, since export also runs a forward pass. The
bundled model was exported on an x86 machine instead, which doesn't have
this limitation.

If you ever need to re-export (e.g. a custom-trained model), do it on a
PC/laptop, not the Pi:
```bash
pip install ultralytics ncnn
python -c "from ultralytics import YOLO; YOLO('yourmodel.pt').export(format='ncnn')"
```
then copy the resulting `..._ncnn_model/` folder into `models/` on the Pi.

## Web dashboard (control from your phone or laptop)

Once `uv run autocar` is running, find the Pi's IP address:
```bash
hostname -I
```
Then open, from any phone or laptop **on the same Wi-Fi network** as the Pi:
```
http://<pi-ip-address>:5000
```
You'll see three buttons — **Start**, **Stop**, **Take a Photo** — and the
captured photo + description appear right on the page after you tap
"Take a Photo". No app install needed; it's just a webpage, so it works
identically on mobile or laptop. The typed terminal commands
(`STOP AND TAKE A PHOTO`, `start`, `stop`) still work at the same time.

## Step-by-step build

### 1. Flash and prep the Pi
- Flash Raspberry Pi OS (Debian 13 Trixie) with Raspberry Pi Imager.
- Enable SSH and Wi-Fi during imaging, or via `sudo raspi-config` after first boot.
- `sudo raspi-config` → Interface Options → enable the Camera.

### 2. Get the code onto the Pi
```bash
# on your laptop, after you've pushed this repo to GitHub:
ssh pi@<pi-ip-address>
git clone <your-repo-url> autocar
cd autocar
```

### 3. Run the setup script (installs uv, system camera libs, deps, YOLO weights)
```bash
bash scripts/setup_pi.sh
```
> If a pip download times out on your network (common on slow Wi-Fi for the
> large `lgpio` wheel), the setup script now installs `lgpio` via `apt`
> instead and it's excluded from `pyproject.toml`. If any other package still
> times out, re-run with a higher timeout: `UV_HTTP_TIMEOUT=180 uv sync`.
>
> **Python version matters for `--system-site-packages`.** It only works if
> the venv uses the *same* Python that `apt` installed `picamera2` for. On
> Debian 13 (Trixie) that's the system default (3.13), not a standalone
> 3.11 build. `scripts/setup_pi.sh` detects this automatically now. If you
> ever see `ModuleNotFoundError: No module named 'picamera2'` after `uv
> sync`, check with `cat .venv/pyvenv.cfg` — if the Python version there
> doesn't match `python3 --version`, recreate the venv:
> ```bash
> rm -rf .venv
> uv venv --system-site-packages --python $(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
> uv sync
> ```

### 4. Wire the hardware
Connect the L298N boards, motors, HC-SR04, and battery per the pin table
above. Double-check the echo pin voltage divider before powering on.

### 5. Run it
```bash
uv run autocar
```
The car starts driving forward immediately. While it's running, type:
```
STOP AND TAKE A PHOTO
```
and press Enter in the same terminal (SSH session works fine). The car
stops, captures `captures/capture_<timestamp>.jpg`, runs detection, and
prints something like:
```
I found one person.
I found two chairs and a bottle.
```
Then it resumes driving automatically.

Press `Ctrl+C` to shut down cleanly (motors stop, camera released).

### 6. Git workflow
```bash
git add -A
git commit -m "Initial autocar project"
git remote add origin <your-repo-url>
git push -u origin main
```

## Tuning

All thresholds (stop distance, slow distance, speeds, YOLO confidence) are
in `src/autocar/config.py` — no need to touch any other file to tune
behavior.

## Next steps you may want
- Swap the terminal command listener for voice control (e.g. `speech_recognition` + a wake word).
- Add a small web dashboard (Flask) to see the live camera feed and send commands from your phone.
- Replace yolov8n with a custom-trained model if you need to recognize specific objects (e.g. lab equipment).
