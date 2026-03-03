# app.py
import sys
import os
import cv2
import base64
import json
from PyQt5.QtWidgets import QApplication ,QMainWindow
from PyQt5.QtCore import QTimer, QUrl ,pyqtSlot ,Qt
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from pathlib import Path
from classes.bridge import Bridge
import time
import numpy as np
from classes.webcam import WebcamCamera
from classes.lucidcamera import LucidCamera
from classes.mindvision_cam import MindVisionCamera



import classes.sdk_setup as sdk_setup
sdk_setup.setup_sdk()

from arena_api.system import system

class MainWindow(QMainWindow):

    def __init__(self, base_dir):
        super().__init__()

        self.setWindowTitle("Cop Design System")
        self.resize(1200, 800)

        self.base_dir = base_dir
        self.templates_dir = os.path.join(base_dir, "templates")
        self.training_single_shot = False

        # Web view
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # Bridge
        self.bridge = Bridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Camera
        # options: 'lucid', 'webcam', 'mindvision'
        self.camera_type="lucid"  # or 'webcam' #lucid

        if self.camera_type=="webcam":
            self.camera=WebcamCamera()
        elif self.camera_type=="lucid":
            self.camera=LucidCamera()
        elif self.camera_type=="MindVision":
            self.camera=MindVisionCamera()
        
        else:
            self.camera = None
            print("Invalid camera type")

        self.timer = QTimer()
        self.timer.timeout.connect(self.grab_frame)
        self.prev_time = 0
        self.fps = 0

        # Load first page
        self.load_page("index.html")

      

    # -------- PAGE LOAD --------
    def load_page(self, page_name):

        print(f"Switching to {page_name}")

        # Stop timer safely
        if self.timer.isActive():
            self.timer.stop()

        # Stop current camera safely
        if hasattr(self, "camera") and self.camera:
            try:
                self.camera.stop()
            except Exception as e:
                print("Camera stop error:", e)

        # Reset page
        self.view.setUrl(QUrl("about:blank"))

        full_path = os.path.join(self.templates_dir, page_name)

        if os.path.exists(full_path):
            self.view.load(QUrl.fromLocalFile(full_path))
        else:
            print("Page not found:", full_path)



    # def start_camera(self):
       
    #     self.camera.start()
    #     self.timer.start(30)
    def start_camera(self, single_shot=False):

        self.training_single_shot = single_shot

        if self.camera is None:
            if self.camera_type == "webcam":
                self.camera = WebcamCamera()
            elif self.camera_type == "lucid":
                self.camera = LucidCamera()
            elif self.camera_type == "mindvision":
                self.camera = MindVisionCamera()
            else:
                print("Invalid camera type")
                return

        self.camera.start()

        if single_shot:
            self.grab_frame()   # capture only one frame
        else:
            self.timer.start(30)

            print("Starting camera:", self.camera_type)

            self.camera.start()
            self.timer.start(30)
        
    def stop_camera(self):

        self.timer.stop()

        if self.camera:
            self.camera.stop()
            self.camera = None

        print("Camera Stopped")

    def grab_frame(self):

        frame = self.camera.get_frame()
        # print("Grabbing frame")

        if frame is None:
            return
          # -------- FPS CALCULATION --------
        current_time = time.time()
        if self.prev_time != 0:
            self.fps = 1 / (current_time - self.prev_time)
        self.prev_time = current_time

        # Draw FPS on frame
        cv2.putText(frame,
                    f"FPS: {int(self.fps)}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2)
        _, buffer = cv2.imencode(".jpg", frame)
        jpg = base64.b64encode(buffer).decode()

        self.bridge.frame_signal.emit(jpg)
           

        if self.training_single_shot:
            self.timer.stop()
            self.training_single_shot = False

 #------- CAMERA START --------       

    # def start_camera(self):

    #     if self.timer.isActive():
    #         print("Camera already running")
    #         return

    #     print("Camera Starting...")

    #     if self.cap is None:
    #         self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    #     if not self.cap.isOpened():
    #         print("Camera not found")
    #         return

    #     self.timer.start(30)
    #     print("Camera Started")


    
    # # -------- CAMERA STOP --------
    # def stop_camera(self):

    #     self.timer.stop()

    #     if self.cap:
    #         self.cap.release()
    #         self.cap = None

    #     print("Camera Stopped")

    # # -------- FRAME SEND --------
    # def grab_frame(self):
    #     # print("Grabbing frame...")

    #     if not self.cap:
    #         return

    #     ret, frame = self.cap.read()

    #     if not ret:
    #         return

    #     _, buffer = cv2.imencode(".jpg", frame)
    #     jpg = base64.b64encode(buffer).decode()

    #     if self.view.page().webChannel():
    #         try:
    #             self.bridge.frame_signal.emit(jpg)
    #         except:
    #             pass


# # -------- CAMERA START/STOP WITH LUCID --------

#     def start_camera(self):
#         if self.timer.isActive():
#             print("camera already running")
#             return
#         print("Connecting Lucid camera...")

#         device=system.create_device()

#         if len(device)==0:
#             print("no camera fonud")
#             return
#         self.device=device[0]

#         nodemap=self.device.nodemap
          
#           # Important for inspection stability

#         nodemap['BalanceWhiteAuto'].value = 'Off'
#         nodemap['ExposureAuto'].value = 'Off'
#         nodemap['GainAuto'].value = 'Off'

#         nodemap['ExposureTime'].value = 65500.0   # adjust based on lighting
#         nodemap['Gain'].value = 0.0

#          # Pixel format
#         nodemap['PixelFormat'].value = 'BayerRG8'

#         self.device.start_stream()
#         self.timer.start(30) 
#         print("camera started")

#     def stop_camera(self):
       
#         self.timer.stop()

#         if self.device:
#             self.device.stop_stream()
#             system.destroy_device()
#             self.device = None

#         print("Lucid Camera Stopped") 

#     def grab_frame(self):

#         if not self.device:
#             return

#         buffer = self.device.get_buffer()

#         height = buffer.height
#         width = buffer.width

#         # Convert raw buffer to numpy
#         raw = np.ctypeslib.as_array(buffer.pdata,
#                                     shape=(height, width))

#         # Convert BayerRG8 to BGR
#         frame = cv2.cvtColor(raw, cv2.COLOR_BAYER_BG2BGR)

#         self.device.requeue_buffer(buffer)

#         _, buffer_jpg = cv2.imencode(".jpg", frame)
#         jpg = base64.b64encode(buffer_jpg).decode()

#         self.bridge.frame_signal.emit(jpg)      

#-------- SETTINGS SAVE --------

    def save_Settings(self, material, count, yarn):
        data={
            "material": material,
            "count": count,
            "yarn": yarn
        }
          
        json_path = Path(__file__).parent / "settings.json"
        with open(json_path, "w") as f:
          json.dump(data, f, indent=4)

        print("Settings saved:", data)


# -------- TRAINING --------
    def start_training_process(self):
      print("Running training process...")   

    def save_training_settings(self, material, count, yarn, model):
        data={
            "material":material,
            "count":count,
            "yarn":yarn,
            "model":model
        }

        json_path = Path(__file__).parent / "training_settings.json"

        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)

        print("Training settings saved:", data)




#----------- REPORT WINDOW --------
    
        
    def open_report_window(self):

        # If already open → bring to front
        if hasattr(self, "report_window") and self.report_window:
            if self.report_window.isVisible():
                self.report_window.activateWindow()
                return

        # Create independent small window
        self.report_window = QMainWindow()   # no parent

        self.report_window.setWindowTitle("Report")
        self.report_window.setFixedSize(1000, 700)  # fixed small 
        self.report_window.setWindowState(Qt.WindowNoState)

        view = QWebEngineView()
        self.report_window.setCentralWidget(view)

        report_file = Path(__file__).parent / "templates" / "report.html"
        view.load(QUrl.fromLocalFile(str(report_file.resolve())))

        self.report_window.show()

#----------- CLEANUP ON CLOSE --------
    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)




# -------------MAIN ENTRY POINT-------
if __name__ == "__main__":

    app = QApplication(sys.argv)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    window = MainWindow(base_dir)
    window.show()

    sys.exit(app.exec_())

    