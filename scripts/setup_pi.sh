#!/usr/bin/env bash
# Run this ON THE RASPBERRY PI (Debian 13 "Trixie"), not on your laptop.
set -e

echo "== 1. System packages (camera stack, GPIO backend, git) =="
sudo apt update
sudo apt install -y \
    python3-picamera2 \
    python3-libcamera \
    python3-lgpio \
    libcamera-apps \
    git \
    curl

echo "== 2. Install uv (if not already installed) =="
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Slow/flaky home Wi-Fi can time out large aarch64 wheel downloads.
export UV_HTTP_TIMEOUT=120

echo "== 3. Create the venv WITH access to system site-packages =="
# --system-site-packages is required so the venv can see the apt-installed
# picamera2 / libcamera bindings, which cannot be installed via pip on the Pi.
# IMPORTANT: this only works if the venv uses the SAME interpreter apt
# installed picamera2 for (/usr/bin/python3, e.g. 3.13 on Trixie). Passing
# just a version number to `uv venv --python` can make uv fetch its own
# standalone build instead of using the system one, which breaks
# --system-site-packages — so we point at the exact system binary.
SYS_PYTHON="/usr/bin/python3"
echo "Using $SYS_PYTHON ($($SYS_PYTHON --version)) so the venv can see apt packages."
uv venv --system-site-packages --python "$SYS_PYTHON"

echo "== 4. Install project dependencies =="
uv sync

echo "== 5. Verify bundled YOLO model =="
if [ -f "models/yolov8n_ncnn_model/model.ncnn.param" ]; then
    echo "Found pre-exported ncnn model at models/yolov8n_ncnn_model/ (no export needed)."
else
    echo "models/yolov8n_ncnn_model/ not found — exporting is NOT possible on the Pi itself"
    echo "(PyTorch's conv kernels crash with illegal-instruction on Pi 4's Cortex-A72)."
    echo "Export it on a PC/laptop instead:"
    echo "  pip install ultralytics ncnn"
    echo "  python -c \"from ultralytics import YOLO; YOLO('yolov8n.pt').export(format='ncnn')\""
    echo "then copy the resulting yolov8n_ncnn_model/ folder into models/ on the Pi."
fi

echo "Done. Enable the camera interface with 'sudo raspi-config' if you haven't,"
echo "then run:  uv run autocar"
