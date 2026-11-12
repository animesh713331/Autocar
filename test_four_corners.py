from pathlib import Path
from autocar.camera import Camera
from autocar.visual_place_database import VisualPlaceDatabase

camera = Camera()
try:
    image_path = camera.capture()
finally:
    camera.close()

db = VisualPlaceDatabase("data/visual_places")
result = db.observe(image_path)

print("\nLIVE IMAGE:", image_path)
print("RECOGNITION RESULT:")
print(result)
