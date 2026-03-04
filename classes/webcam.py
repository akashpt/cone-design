import cv2


class WebcamCamera:

    def __init__(self):
        self.cap = None


    def start(self):

        print("Starting Webcam...")

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            print("Webcam not found")
            return False

        return True


    def get_frame(self):

        if self.cap is None:
            return None

        ret, frame = self.cap.read()

        if not ret:
            return None

        return frame


    def stop(self):

        if self.cap:
            self.cap.release()
            self.cap = None

        print("Webcam stopped")