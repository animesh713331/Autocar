import cv2
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from picamera2 import Picamera2

camera = Picamera2()

config = camera.create_video_configuration(
    main={"size": (1280, 720), "format": "RGB888"}
)

camera.configure(config)
camera.start()
time.sleep(2)

lock = threading.Lock()

class CameraHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header(
            "Content-Type",
            "multipart/x-mixed-replace; boundary=frame"
        )
        self.end_headers()

        try:
            while True:
                with lock:
                    frame = camera.capture_array()

                frame = cv2.cvtColor(
                    frame, cv2.COLOR_RGB2BGR
                )

                success, encoded = cv2.imencode(
                    ".jpg", frame,
                    [cv2.IMWRITE_JPEG_QUALITY, 80]
                )

                if not success:
                    continue

                data = encoded.tobytes()

                self.wfile.write(b"--frame\r\n")
                self.wfile.write(
                    b"Content-Type: image/jpeg\r\n"
                )
                self.wfile.write(
                    f"Content-Length: {len(data)}\r\n\r\n".encode()
                )
                self.wfile.write(data)
                self.wfile.write(b"\r\n")

        except (BrokenPipeError, ConnectionResetError):
            print("Viewer disconnected")

    def log_message(self, format, *args):
        pass


server = ThreadingHTTPServer(
    ("0.0.0.0", 8000),
    CameraHandler
)

print("LIVE CAMERA SERVER STARTED")
print("Open http://10.223.120.22:8000 on your laptop")

try:
    server.serve_forever()
finally:
    server.server_close()
    camera.stop()
    camera.close()
