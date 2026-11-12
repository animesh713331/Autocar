"""
Web dashboard for controlling the car from any phone or laptop browser on
the same Wi-Fi network as the Pi. Buttons: Start, Stop, Take Photo. The
captured photo + description appear directly on the page.

This module only sets flags on the shared ControlState - it never touches
hardware directly (see control_state.py for why).
"""
from __future__ import annotations

import logging
import os
import threading
from flask import (
    Flask,
    Response,
    jsonify,
    render_template_string,
    send_from_directory,
)

from . import config
from .control_state import ControlState
import json
from pathlib import Path
import cv2
from picamera2 import Picamera2
from .destination_resolver import DestinationResolver
from .map_storage import MapStorage
from .navigation_api import create_navigation_blueprint
from .navigation_controller import NavigationController
from .navigation_session import NavigationSession
from .map_builder import MapBuilder
from .navigation_orchestrator import NavigationOrchestrator
from .visual_navigation_bridge import VisualNavigationBridge
from .visual_place_database import VisualPlaceDatabase
log = logging.getLogger(__name__)

INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Autocar Control</title>
  <style>
    body { font-family: -apple-system, sans-serif; background: #111; color: #eee;
           display: flex; flex-direction: column; align-items: center; padding: 24px; }
    h1 { font-size: 1.3rem; margin-bottom: 4px; }
    #status { color: #9ad; margin-bottom: 20px; min-height: 1.2em; }
    .buttons { display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; justify-content: center; }
    button { font-size: 1.1rem; padding: 14px 22px; border-radius: 10px; border: none;
             cursor: pointer; color: white; }
    #startBtn { background: #2a8f4f; }
    #stopBtn { background: #b23b3b; }
    #photoBtn { background: #2a6f9f; }
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    #result { max-width: 480px; text-align: center; }
    #photo { max-width: 100%; border-radius: 10px; margin-top: 12px; display: none; }
    #description { font-size: 1.1rem; margin-top: 10px; }
        #navigationPanel {
      width: 100%;
      max-width: 480px;
      box-sizing: border-box;
      margin: 12px 0 24px;
      padding: 18px;
      background: #20242a;
      border: 1px solid #414750;
      border-radius: 12px;
    }
    #destinationInput {
      width: 100%;
      box-sizing: border-box;
      padding: 12px;
      margin: 8px 0 12px;
      border-radius: 8px;
      border: 1px solid #555;
      background: #111;
      color: #eee;
      font-size: 1rem;
    }
    #planBtn { background: #5366c9; }
    #navStopBtn { background: #a33b3b; }
    #navStatus {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      line-height: 1.5;
      margin-top: 14px;
      color: #bcd7ff;
    }
        #localizeBtn { background: #267b78; }
    #localizationResult {
      width: 100%;
      box-sizing: border-box;
      margin-top: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      color: #d6e8e8;
    }
  </style>
</head>
<body>
  <h1>Autocar Control</h1>
  <div id="status">Ready.</div>
  <div class="buttons">
    <button id="startBtn" onclick="sendCommand('start')">Start</button>
    <button id="stopBtn" onclick="sendCommand('stop')">Stop</button>
    <button id="leftBtn" onclick="sendCommand('left')">⬅ Left</button>
    <button id="rightBtn" onclick="sendCommand('right')">Right ➡</button>
    <button id="photoBtn" onclick="takePhoto()">Take a Photo</button>
  </div>
    <section id="navigationPanel">
    <h2>Visual Navigation</h2>
    <p>Request a destination and review the navigation decision.</p>

    <form id="navigationForm">
      <label for="destinationInput">Destination</label>
      <input
        id="destinationInput"
        type="text"
        placeholder="Enter a configured destination"
        required
      >

      <div class="buttons">
        <button id="planBtn" type="submit">Plan Navigation</button>
        <button id="navStopBtn" type="button" onclick="stopNavigation()">
          Stop Navigation
        </button>
        <button type="button" onclick="refreshNavigationStatus()">
          Refresh Status
        </button>
      </div>
    </form>

    <div id="navStatus" role="status" aria-live="polite">
      Navigation is idle. No motor commands will be issued.
    </div>
    
    <div class="buttons">
      <button
        id="localizeBtn"
        type="button"
        onclick="localizeLastPhoto()"
      >
        Localize Last Photo
      </button>
    </div>

    <div id="localizationResult" role="status" aria-live="polite">
      No localization attempted yet.
    </div>

  </section>

  <div id="result">
    <img id="photo">
    <div id="description"></div>
  </div>

  <script>
    
    async function refreshNavigationStatus() {
      const output = document.getElementById('navStatus');

      try {
        const response = await fetch('/api/navigation/status');
        const data = await response.json();
        output.textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        output.textContent = 'Could not retrieve navigation status.';
      }
    }

    document.getElementById('navigationForm').addEventListener(
      'submit',
      async function (event) {
        event.preventDefault();

        const destination =
          document.getElementById('destinationInput').value.trim();
        const output = document.getElementById('navStatus');

        if (!destination) {
          output.textContent = 'Please enter a destination.';
          return;
        }

        output.textContent = 'Submitting destination...';

        try {
          const response = await fetch('/api/navigation/destination', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ destination })
          });

          const data = await response.json();
          output.textContent = JSON.stringify(data, null, 2);
        } catch (error) {
          output.textContent = 'Navigation request failed.';
        }
      }
    );

    
    async function localizeLastPhoto() {
      const button = document.getElementById('localizeBtn');
      const resultBox = document.getElementById('localizationResult');
      const navStatus = document.getElementById('navStatus');

      button.disabled = true;
      resultBox.textContent = 'Localizing the last captured photo...';

      try {
        const response = await fetch(
          '/api/navigation/localize-last-photo',
          { method: 'POST' }
        );

        const data = await response.json();

        resultBox.textContent = JSON.stringify(data, null, 2);

        if (!response.ok) {
          resultBox.textContent =
            `Localization failed (${response.status}):\n` +
            JSON.stringify(data, null, 2);
        }

        await refreshNavigationStatus();
      } catch (error) {
        resultBox.textContent =
          'Could not contact the localization API.';
      } finally {
        button.disabled = false;
      }
    }

  </script>
</body>
</html>
"""


def create_app(state: ControlState) -> Flask:
    app = Flask(__name__)
    camera_lock = threading.Lock()

    @app.route("/camera/live")
    def camera_live():
        def generate():
            if not camera_lock.acquire(blocking=False):
                return

            picam2 = None

            try:
                picam2 = Picamera2()

                camera_config = picam2.create_video_configuration(
                    main={
                        "size": (640, 360),
                        "format": "BGR888",
                    }
                )

                picam2.configure(camera_config)
                picam2.start()

                import time
                time.sleep(1)

                while True:
                    frame = picam2.capture_array()

                    success, jpeg = cv2.imencode(
                        ".jpg",
                        frame,
                        [cv2.IMWRITE_JPEG_QUALITY, 75],
                    )

                    if not success:
                        continue

                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + jpeg.tobytes()
                        + b"\r\n"
                    )

            except GeneratorExit:
                raise

            except Exception:
                log.exception("Live camera stream failed")

            finally:
                if picam2 is not None:
                    try:
                        picam2.stop()
                        picam2.close()
                    except Exception:
                        log.exception("Camera cleanup failed")

                camera_lock.release()

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame",
            headers={"Cache-Control": "no-cache"},
        )
    # Advisory-only navigation setup. This loads the saved graph but
    # never creates or executes motor commands.
    map_storage = MapStorage("data/navigation_map.json")
    graph = map_storage.load()

    aliases_path = Path("data/destination_aliases.json")
    if aliases_path.exists():
        with aliases_path.open("r", encoding="utf-8") as file:
            aliases = json.load(file)
        if not isinstance(aliases, dict):
            raise ValueError(
                "data/destination_aliases.json must contain a JSON object."
            )
    else:
        aliases = {}

    resolver = DestinationResolver(graph, aliases)
    controller = NavigationController(graph)
    navigation_session = NavigationSession(controller)
    place_database = VisualPlaceDatabase("data/visual_places")
    map_builder = MapBuilder(storage=map_storage, graph=graph)

    orchestrator = NavigationOrchestrator(
        place_database=place_database,
        map_builder=map_builder,
        pending_dir="data/pending_places",
    )
    visual_bridge = VisualNavigationBridge(orchestrator)

    app.config["VISUAL_NAVIGATION_BRIDGE"] = visual_bridge
    app.config["VISUAL_PLACE_DATABASE"] = place_database
    app.register_blueprint(
        create_navigation_blueprint(navigation_session, resolver)
    )

    # Expose these for software tests and diagnostics.
    app.config["NAVIGATION_SESSION"] = navigation_session
    app.config["DESTINATION_RESOLVER"] = resolver
    @app.route("/")
    def index():
        return render_template_string(INDEX_HTML)

    @app.route("/command/start", methods=["POST"])
    def start():
        state.running.set()
        log.info("Web command: start")
        return jsonify(status="Driving.")

    @app.route("/command/left", methods=["POST"])
    def left():
        state.left_requested.set()
        log.info("Web command: left")
        return jsonify(status="Turning left.")

    @app.route("/command/right", methods=["POST"])
    def right():
        state.right_requested.set()
        log.info("Web command: right")
        return jsonify(status="Turning right.")

    @app.route("/command/stop", methods=["POST"])
    def stop():
        state.running.clear()
        log.info("Web command: stop")
        return jsonify(status="Stopped.")

    @app.route("/command/photo", methods=["POST"])
    def photo():
        log.info("Web command: take a photo")
        finished, url, description = state.request_photo_and_wait(
            timeout=config.PHOTO_TIMEOUT_SECONDS
        )
        if not finished:
            return jsonify(error="Timed out waiting for photo."), 504
        return jsonify(photo_url=url, description=description)

    @app.route("/captures/<path:filename>")
    def serve_capture(filename):
        return send_from_directory(os.path.abspath(config.CAPTURE_DIR), filename)

    @app.post("/api/navigation/localize-last-photo")
    def localize_last_photo():
        image_path_value = state.get_last_photo_path()

        if not image_path_value:
            return jsonify(
                error="No photo has been captured yet."
            ), 409

        try:
            capture_root = Path(config.CAPTURE_DIR).resolve()
            image_path = Path(image_path_value).resolve()

            # Only process images inside the configured capture directory.
            if not image_path.is_relative_to(capture_root):
                return jsonify(
                    error="The saved photo is outside the capture directory."
                ), 400

            if not image_path.is_file():
                return jsonify(
                    error="The saved photo no longer exists."
                ), 404

            bridge = app.config["VISUAL_NAVIGATION_BRIDGE"]
            result = bridge.localize_capture(image_path)

            if result.get("status") == "recognized":
                place_id = result.get("place_id")
                graph = map_storage.load()
                mapped_ids = {
                    node["id"] for node in graph.get("nodes", [])
                }

                if place_id not in mapped_ids:
                    return jsonify({
                        "status": "recognized_but_unmapped",
                        "place_id": place_id,
                        "message": (
                            "The image matched a reference, but its "
                            "location is not available in the navigation map."
                        ),
                        "execution": "advisory_only",
                    }), 200

                session_result = navigation_session.update_location(place_id)

                return jsonify({
                    **result,
                    "session": session_result,
                    "execution": "advisory_only",
                }), 200

            return jsonify({
                **result,
                "message": (
                    "Location not confirmed. The image has been "
                    "saved for review."
                ),
                "execution": "advisory_only",
            }), 200

        except Exception:
            log.exception("Visual localization failed")
            return jsonify(
                error="Localization failed. Check the server logs."
            ), 500

    return app


def start_web_server(state: ControlState) -> threading.Thread:
    """Starts the Flask dashboard in a background thread and returns it."""
    app = create_app(state)

    def _run():
        app.run(host=config.WEB_HOST, port=config.WEB_PORT, threaded=True, use_reloader=False)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log.info("Web dashboard running at http://<pi-ip-address>:%d", config.WEB_PORT)
    return thread
