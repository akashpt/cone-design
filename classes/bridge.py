# classes/bridge.py
import cv2
import base64
import json
from path import BASE_DIR ,SETTINGS_FILE ,TRAINING_SETTINGS_FILE ,TRAINING_IMAGES_DIR
import time
from datetime import datetime
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot ,QThread, QTimer
from functools import wraps
from classes.plc import machine_status ,gripper_function ,count_status
from classes.webcam import WebcamCamera
from classes.lucidcamera import LucidCamera
from classes.mindvision_cam import MindVisionCamera
from classes.hikrobot import HikRobotCamera





def controller_access_required(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):

        if not self.controller_access:
            print("🚫 Controller access denied → Home page")

            self.stop_camera()
            self.app_ref.load_page("index.html")
            return

        return func(self, *args, **kwargs)

    return wrapper

class TrainingWorker(QObject):

    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, bridge, settings_json: str, interval_ms: int = 2000):
        super().__init__()
        self.bridge = bridge
        self.settings_json = settings_json
        self.interval_ms = interval_ms
        self._running = False

    @pyqtSlot()
    def run(self):
        self._running = True
        self.status.emit("🟢 Continuous Training Started")

        while self._running:
            QThread.msleep(self.interval_ms)

        self.status.emit("🔴 Continuous Training Stopped")
        self.finished.emit()

    def stop(self):
        self._running = False



class Bridge(QObject):

    frame_signal = pyqtSignal(str)
    controller_open_signal = pyqtSignal()

    def __init__(self, app_ref):
        super().__init__()

        # Reference to MainWindow
        self.app_ref = app_ref

        # Camera mode
        self.live_mode = None
        self.last_count_signal = 0
        # ---------------- CAMERA ----------------
        self.camera = None
        self.camera_type = "webcam"   # options: webcam / lucid / mindvision

        self.current_interval = 30

        self.timer = QTimer()
        self.timer.timeout.connect(self.grab_frame)

        self.prev_time = 0
        self.fps = 0

        # ---------------- TRAINING ----------------
        self.training_thread = None
        self.training_worker = None
        self.training_active = False

        # ---------------- PASSWORD ----------------
        self.entered_password = ""
        self.controller_access = False

        # Training settings storage
        self.material = None
        self.count = None
        self.yarn = None

       

 # ==========================================
        # 🔐 PASSWORD CHECK FROM HTML
 # ==========================================
  

    @pyqtSlot(str)
    def sendPassword(self, password):

        correct_password = "1234"

        if password == correct_password:

            print("✅ Password Correct")

            self.controller_access = True

            QTimer.singleShot(50, self.goController)

        else:

            print("❌ Wrong Password")

            self.controller_access = False
            self.app_ref.load_page("index.html")

# -------- CAMERA ----------

    @pyqtSlot(str)
    def selectCamera(self, cam_type):

        print("Camera Selected from UI:", cam_type)

        # stop running camera
        self.stop_camera()

        # set new camera type
        self.camera_type = cam_type

        print("Camera type set to:", self.camera_type)


    @pyqtSlot(str)
    def setExposure(self, exposure):

        print("Exposure received from UI:", exposure)

        self.exposure_value = float(exposure)

        if self.camera:
            try:
                self.camera.set_exposure(self.exposure_value)
                print("Exposure applied")
            except Exception as e:
                print("Exposure apply failed:", e)

    @pyqtSlot()
    def startCamera(self):

        print("Inspection started")

        self.training_active = False
        self.last_count_signal = 0
        
        self.current_interval = 30

        self.start_camera()

    # @pyqtSlot()
    # def stopCamera(self):
    #     self.stop_camera()

    @pyqtSlot()
    def stopCamera(self):
        self.timer.stop() # Stop the timer first!
        if self.camera:
            self.camera.stop()
            self.camera = None # Set to None so start_camera can re-init
        self.prev_time = 0 
        print("Camera Stopped and Cleaned")
    
    @pyqtSlot()
    def startTraining(self):
        print("Training started")
        self.stop_camera()
        self.start_training_process() 

    @pyqtSlot()
    def startTrainingCapture(self):    
        self.start_camera()  

    @pyqtSlot()
    def setTrainingMode(self):
        self.current_interval = 500
        self.timer.start(self.current_interval)

    @pyqtSlot()
    def resetNormalMode(self):
        self.current_interval = 30
        self.timer.start(self.current_interval)


    @pyqtSlot(str)
    def startContinuousTraining(self, settings):

        print("Continuous training started")
        print("Received settings:", settings)

        self.training_active = True
        self.last_count_signal = 0

        # slower capture for training
        self.current_interval = 500

        self.start_camera()

    @pyqtSlot()
    def stopContinuousTraining(self):
       self.training_active = False
#--------------------------------------------
            
    @pyqtSlot(str, str, str)
    def saveSettings(self, material, count, yarn):
            self.save_Settings(material, count, yarn) 


    @pyqtSlot(str, str, str, str)
    def saveTrainingSettings(self, material, count, yarn, model):

        self.material =material
        self.count =count
        self.yarn =yarn
        self.save_training_settings(material, count, yarn, model)

    @pyqtSlot(str, str)
    def saveControllerSettings(self, camera, exposure):

        print("Saving Controller Settings")

        # Stop camera before changing settings
        self.stop_camera()

        # Save camera type
        self.camera_type = camera

        # Convert exposure to float
        self.exposure_value = float(exposure)

        print("Camera:", self.camera_type)
        print("Exposure:", self.exposure_value)

      

        # try:
        #     self.start_camera()
        # except:
        #     print("Camera start failed")

        # Apply exposure after camera start
        if self.camera:
            try:
                self.camera.set_exposure(self.exposure_value)
                print("Exposure applied")
            except Exception as e:
                print("Exposure set failed:", e)

    # -------- NAVIGATION ----------
    @pyqtSlot()
    def goHome(self):

        self.controller_access = False
        self.stop_camera()
        self.app_ref.load_page("index.html")

    @pyqtSlot()
    def goReport(self):
        self.controller_access = False
        self.stop_camera()
        self.app_ref.open_report_window()

    @pyqtSlot()
    def goTraining(self):
        self.controller_access = False
        self.stop_camera()
        self.app_ref.load_page("training.html")
        
    @pyqtSlot()
    @controller_access_required
    def goController(self):

        print(">>> goController SLOT CALLED")

        self.stop_camera()
        self.app_ref.load_page("controller.html")


#----------------------------------------------------------

    def start_camera(self):

        # prevent multiple starts
        if self.timer.isActive():
            print("Camera already running")
            return

        # create camera object if not exists
        if self.camera is None:

            if self.camera_type == "webcam":
                self.camera = WebcamCamera()

            elif self.camera_type == "lucid":
                self.camera = LucidCamera()

            elif self.camera_type == "mindvision":
                self.camera = MindVisionCamera()

            elif self.camera_type == "hikrobot":
                self.camera = HikRobotCamera()

            else:
                print("Invalid camera type")
                return

        # start camera
        self.camera.start()

        # check camera started
        if hasattr(self.camera, "hCamera") and self.camera.hCamera == 0:
            print("Camera failed to start")
            self.camera = None
            return
        print(f"Starting camera: {self.camera_type}")

        if hasattr(self, "exposure_value") and self.camera:
            try:
                self.camera.set_exposure(self.exposure_value)
            except:
                print("Exposure not applied (camera not ready)")

  

        # start frame timer
        self.timer.start(self.current_interval)

    def stop_camera(self):

            self.timer.stop()
            self.fps=0
            self.prev_time=0
            if self.camera:
                self.camera.stop()
                self.camera = None

            print("Camera Stopped")

    def grab_frame(self):

        if not self.camera:
            return

        try:
            frame = self.camera.get_frame()
        except:
            return

        if frame is None:
            return

        # ---------- FPS ----------
        current_time = time.time()

        if self.prev_time != 0:
            self.fps = 1 / (current_time - self.prev_time)

        self.prev_time = current_time

        cv2.putText(frame,
                    f"FPS: {int(self.fps)}",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2)

        # ---------- SEND FRAME ----------
        _, buffer = cv2.imencode(".jpg", frame)
        jpg = base64.b64encode(buffer).decode()

        self.frame_signal.emit(jpg)


        # ====================================
        # PLC SIGNAL (READ ONLY ONCE)
        # ====================================

        signal = count_status()


        # ====================================
        # INSPECTION MODE
        # ====================================

        if not self.training_active:

            if signal == 1 and self.last_count_signal == 0:

                print("PLC trigger detected (Inspection)")

                self.run_prediction(frame)


        # ====================================
        # TRAINING MODE
        # ====================================

        else:

            if signal == 1 and self.last_count_signal == 0:

                print("PLC trigger detected (Training)")

                material = self.material
                count = self.count
                yarn = self.yarn

                if material and count and yarn:

                    save_dir = TRAINING_IMAGES_DIR / material / count / yarn
                    save_dir.mkdir(parents=True, exist_ok=True)

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    save_path = save_dir / f"train_{ts}.jpg"

                    cv2.imwrite(str(save_path), frame)

                    print("Training image saved:", save_path)


        # update PLC state
        self.last_count_signal = signal
    #-------- SETTINGS SAVE --------

    def save_Settings(self, material, count, yarn):
        data={
            "material": material,
            "count": count,
            "yarn": yarn
        }
       
        with open(SETTINGS_FILE, "w") as f:
          json.dump(data, f, indent=4)

        print("Settings saved:", data)

    # --------- TRAINING CONTROL ----------
 
    def start_training_process(self):
      print("Running training process...")   

    def save_training_settings(self, material, count, yarn, model):
        data={
            "material":material,
            "count":count,
            "yarn":yarn,
            "model":model
        }

       

        with open(TRAINING_SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)

        print("Training settings saved:", data) 



    def run_prediction(self, frame):

        print("Running prediction...")

        # Example placeholder
        # Replace with your AI model later

        result = "GOOD"

        print("Prediction result:", result)

        if result == "BAD":
            gripper_function([1,0,0,0])   


  