from picamera2 import Picamera2
from libcamera import controls
import cv2, time

picam2 = Picamera2()
config = picam2.create_still_configuration(
    main={"size": (1280, 720)}
)
picam2.configure(config)
picam2.start()

picam2.set_controls({
    "AfMode": controls.AfModeEnum.Continuous
})

time.sleep(1.0)   # Laisse l’autofocus se caler
frame = picam2.capture_array()
frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
cv2.imwrite("test.jpg", frame_bgr)

picam2.stop()
picam2.close()
