
"""Thread-safe state shared between navigation and the web dashboard."""
import threading


class ControlState:
    def __init__(self):
        self.running = threading.Event()
        self.photo_requested = threading.Event()
        self.photo_done = threading.Event()
        self.left_requested = threading.Event()
        self.right_requested = threading.Event()

        self._lock = threading.Lock()
        self.last_photo_url = None
        self.last_description = None
        self.last_photo_path = None

    def set_photo_result(self, photo_url, description):
        with self._lock:
            self.last_photo_url = photo_url
            self.last_description = description
        self.photo_done.set()

    def set_photo_path(self, image_path):
        with self._lock:
            self.last_photo_path = str(image_path)

    def get_last_photo(self):
        with self._lock:
            return self.last_photo_url, self.last_description

    def get_last_photo_path(self):
        with self._lock:
            return self.last_photo_path

    def request_photo_and_wait(self, timeout):
        self.photo_done.clear()
        self.photo_requested.set()
        finished = self.photo_done.wait(timeout=timeout)
        url, description = self.get_last_photo()
        return finished, url, description
