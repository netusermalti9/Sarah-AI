class CameraManager:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.camera = None
        self.started = False

    def start_camera(self):
        self.camera = cv2.VideoCapture(self.camera_index)
        if not self.camera.isOpened():
            print("❌ Error: Could not open camera.")
            return False
        self.started = True
        print("✅ Camera started successfully.")
        return True

    def capture_frame(self):
        if self.camera is None:
            print("❌ Error: Camera is not initialized.")
            return None

        ret, frame = self.camera.read()
        if not ret:
            print("❌ Error: Failed to capture frame.")
            return None
        return frame

    def stop_camera(self):
        if self.camera is not None:
            self.camera.release()
            self.started = False
            print("🛑 Camera stopped.")
