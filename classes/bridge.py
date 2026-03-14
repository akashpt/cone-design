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
from classes.training import TrainingDetector
from classes.prediction import PredictionDetector




def controller_access_required(func):

    @wraps(func)
    def wrapper(self, *args, **kwargs):

        if not self.controller_access:
            print("🚫 Controller access denied → Home page")

            self.stopCamera()
            self.app_ref.load_page("index.html")
            return

        return func(self, *args, **kwargs)

    return wrapper

class TrainingWorker(QObject):

    result_ready = pyqtSignal(object)
    status = pyqtSignal(str)

    def __init__(self, trainer):
        super().__init__()
        self.trainer = trainer
        self.running = True
        self.busy = False

    @pyqtSlot(object, str)
    def run_training(self, frame, model_key):

        if not self.running or self.busy:
            return

        self.busy = True

        try:

            result = self.trainer.train_from_image(frame, model_key)

            self.result_ready.emit(result)

        except Exception as e:

            self.status.emit(f"Training error: {e}")

        finally:
            self.busy = False

    def stop(self):
        self.running = False

class CameraGrabWorker(QObject):

    frame_ready = pyqtSignal(object)

    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.running = False
        self.camera = None

    @pyqtSlot()
    def run(self):

        self.running = True

        # open camera
        if self.bridge.camera_type == "webcam":
            self.camera = WebcamCamera()

        elif self.bridge.camera_type == "lucid":
            self.camera = LucidCamera()

        elif self.bridge.camera_type == "mindvision":
            self.camera = MindVisionCamera()

        elif self.bridge.camera_type == "hikrobot":
            self.camera = HikRobotCamera()

        else:
            print("Invalid camera")
            return

        self.camera.start()

        while self.running:

            frame = self.camera.get_frame()

            if not self.running:
                break

            if frame is not None:
                try:
                    self.frame_ready.emit(frame)
                except RuntimeError:
                    break

            QThread.msleep(10)

        if self.camera:
            self.camera.stop()

    def stop(self):
        print("Stopping camera worker")
        self.running = False

class PredictionWorker(QObject):

    result_ready = pyqtSignal(object, object, object)
    status = pyqtSignal(str)
    

    def __init__(self, predictor):
        super().__init__()
        self.predictor = predictor
        self.running = True
        self.busy = False

    @pyqtSlot(object, str)
    def run_prediction(self, frame, model_key):

        if not self.running or self.busy:
            return

        self.busy = True

        try:

            vis, results, bits = self.predictor.process_frame(
                frame,
                model_key
            )

            self.result_ready.emit(vis, results, bits)

        except Exception as e:

            self.status.emit(f"Prediction error: {e}")

        finally:
            self.busy = False

    def stop(self):
        self.running = False

class Bridge(QObject):

    frame_signal = pyqtSignal(str)
    controller_open_signal = pyqtSignal()
    request_prediction = pyqtSignal(object, str)
    request_training = pyqtSignal(object, str)
    cone_status_signal = pyqtSignal(list)


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

        self.load_controller_settings()

         # camera thread
        self.camera_thread = None
        self.camera_worker = None
        self.live_mode = "preview"

        # prediction thread
        self.pred_thread = None
        self.pred_worker = None

        # training thread
        self.train_thread = None
        self.train_worker = None

        self.prev_time = 0
        self.fps = 0
        self.model_key = None
        # ---------------- TRAINING ----------------
        self.trainer = TrainingDetector()
        self.predictor =PredictionDetector()
       
        self.training_active = False
        self.first_training_done = False

        # ---------------- PASSWORD ----------------
        self.entered_password = ""
        self.controller_access = False

        # Training settings storage
        self.material = None
        self.count = None
        self.yarn = None

  #-------------------------------* SLOTS*    ----------------------------     

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
        self.stopCamera()

        # set new camera type
        self.camera_type = cam_type

        print("Camera type set to:", self.camera_type)


    @pyqtSlot(str)
    def setExposure(self, exposure):

        # print("Exposure received from UI:", exposure)

        self.exposure_value = float(exposure)
        if self.camera_worker and self.camera_worker.camera:
            try:
                self.camera_worker.camera.set_exposure(self.exposure_value)
                print("Exposure applied")
            except Exception as e:
                print("Exposure apply failed:", e)

    @pyqtSlot(result=str)
    def getSavedSettings(self):

        if os.path.exists(SETTINGS_FILE):

            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)

            print("Loaded settings:", data)

            return json.dumps(data)

        return json.dumps({
            "material": "",
            "count": "",
            "yarn": ""
        })

    @pyqtSlot()
    def startCamera(self):

        print("Camera started in mode:", self.live_mode)

        if self.camera_thread:
            print("Camera already running")
            return

        settings = json.loads(self.getSavedSettings())

        material = settings.get("material")
        count = settings.get("count")
        yarn = settings.get("yarn")

        if material and count and yarn:
            self.model_key = f"{material}_{count}_{yarn}"

        self.camera_thread = QThread()
        self.camera_worker = CameraGrabWorker(self)

        self.camera_worker.moveToThread(self.camera_thread)

        self.camera_thread.started.connect(self.camera_worker.run)

        self.camera_worker.frame_ready.connect(self.on_new_frame)

        self.camera_thread.start()


        # start prediction thread

        self.pred_thread = QThread()

        self.pred_worker = PredictionWorker(self.predictor)

        self.pred_worker.moveToThread(self.pred_thread)

        self.request_prediction.connect(self.pred_worker.run_prediction)

        self.pred_worker.result_ready.connect(self.on_prediction_result)

        self.pred_thread.start()

        # start training thread

        self.train_thread = QThread()

        self.train_worker = TrainingWorker(self.trainer)

        self.train_worker.moveToThread(self.train_thread)

        self.request_training.connect(self.train_worker.run_training)

        self.train_worker.result_ready.connect(self.on_training_result)

        self.train_thread.start()

    @pyqtSlot()
    def stopCamera(self):

        # stop camera worker
        if self.camera_worker:
            self.camera_worker.stop()

        # stop camera thread
        if self.camera_thread:
            self.camera_thread.requestInterruption()
            self.camera_thread.quit()
            self.camera_thread.wait()

        # clear references
        self.camera_worker = None
        self.camera_thread = None

        # stop prediction worker
        if self.pred_worker:
            self.pred_worker.stop()

        if self.pred_thread:
            self.pred_thread.quit()
            self.pred_thread.wait()

        self.pred_worker = None
        self.pred_thread = None

        if self.train_worker:
            self.train_worker.stop()

        if self.train_thread:
            self.train_thread.quit()
            self.train_thread.wait()

        self.train_worker = None
        self.train_thread = None

        print("Camera stopped")



    @pyqtSlot(str, str)
    def setPredictionSettings(self, green, threshold):

        try:

            self.predictor.green_margin = int(green) if green else None
            self.predictor.threshold_margin = int(threshold) if threshold else None

            print(
                "Prediction settings updated:",
                "Green =", self.predictor.green_margin,
                "Threshold =", self.predictor.threshold_margin
            )

        except Exception as e:
            print("Prediction settings error:", e)

    @pyqtSlot()
    def startLiveView(self):

        print("Live view started")

        self.live_mode = "preview"

        self.stopCamera()
        self.startCamera()

    @pyqtSlot()
    def startInspection(self):

        print("Inspection started")

        self.live_mode = "inspection"

        self.stopCamera()
        self.startCamera()
            
    @pyqtSlot()
    def startTraining(self):

        print("Training page opened")

        self.training_active = False
        self.stopCamera()

        # show static training image
        self.showTrainingStaticImage()
        

    @pyqtSlot()
    def startTrainingCapture(self):

        print("Training capture started")

        self.live_mode = "training"

        self.stopCamera()
        self.startCamera()

   
    @pyqtSlot(str)
    def startContinuousTraining(self, settings):

        print("Continuous training started")

        settings_data = json.loads(settings)

        self.material = settings_data["material"]
        self.count = settings_data["count"]
        self.yarn = settings_data["yarn"]

        self.last_count_signal = 0

        # STEP 1 → run static training
        self.run_static_training()

        # STEP 2 → switch to TRAINING MODE
        self.live_mode = "training"

        # STEP 3 → start camera
        self.stopCamera()
        self.startCamera()

       
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

        if self.camera_thread:
           self.stopCamera()

        self.camera_type = camera
        self.exposure_value = float(exposure)

        data = {
            "camera": camera,
            "exposure": self.exposure_value
        }

        settings_file = BASE_DIR / "controller_settings.json"

        with open(settings_file, "w") as f:
            json.dump(data, f, indent=4)

        print("Controller settings saved:", data)

        # Apply exposure if camera already running
        if self.camera_worker and self.camera_worker.camera:
            try:
                self.camera_worker.camera.set_exposure(self.exposure_value)
                print("Exposure applied")
            except Exception as e:
                print("Exposure set failed:", e)

    @pyqtSlot(result=str)
    def getControllerSettings(self):

        settings_file = BASE_DIR / "controller_settings.json"

        if os.path.exists(settings_file):

            with open(settings_file,"r") as f:
                data = json.load(f)

            return json.dumps(data)

        return json.dumps({
            "camera": "webcam",
            "exposure": 5000
        })        

    

    @pyqtSlot(result=str)
    def getTrainedModels(self):

        models = set()

        if not TRAINING_IMAGES_DIR.exists():
            return json.dumps([])

        for material in TRAINING_IMAGES_DIR.iterdir():

            if not material.is_dir():
                continue

            for count in material.iterdir():

                if not count.is_dir():
                    continue

                for yarn in count.iterdir():

                    if not yarn.is_dir():
                        continue

                    model = f"{material.name}_{count.name}_{yarn.name}"
                    models.add(model)

        models_list = sorted(list(models))

        print("Available models:", models_list)

        return json.dumps(models_list)



    @pyqtSlot()
    def run_static_training(self):

        print("Running static training images")

        static_dir = BASE_DIR / "static" / "img"/"training"

        images = sorted(static_dir.glob("*.bmp"))

        if not images:
            print("No static training images found")
            return

        if not (self.material and self.count and self.yarn):
            print("Training settings not set yet")
            return

        model_key = f"{self.material}_{self.count}_{self.yarn}"

        for img_path in images:

            print("Training using:", img_path)

            img = cv2.imread(str(img_path))

            # show image in UI
            _, buffer = cv2.imencode(".jpg", img)
            jpg = base64.b64encode(buffer).decode()
            self.frame_signal.emit(jpg)

            result = self.trainer.train_from_image(img, model_key)

            print("Training result:", result)

            QThread.msleep(200)   # small delay
           

    @pyqtSlot(str)
    def deleteTrainedModel(self, model_name):

        print("Deleting model:", model_name)

        ref_file = BASE_DIR / "models" / f"{model_name}_reference.csv"
        train_file = BASE_DIR / "models" / f"{model_name}_training.csv"

        try:

            if ref_file.exists():
                os.remove(ref_file)
                print("Deleted:", ref_file)

            if train_file.exists():
                os.remove(train_file)
                print("Deleted:", train_file)

            print("Model deleted successfully")

        except Exception as e:
            print("Delete error:", e)

    # -------- NAVIGATION ----------
    @pyqtSlot()
    def goHome(self):

        self.controller_access = False
        self.live_mode = "preview"   # ⭐ reset mode
        self.stopCamera()
        self.app_ref.load_page("index.html")

    @pyqtSlot()
    def goReport(self):
        self.controller_access = False
        self.stopCamera()
        self.app_ref.open_report_window()

   
    @pyqtSlot()
    def goTraining(self):

        if self.live_mode == "inspection" and self.camera_running():
            print("⚠ Stop inspection before opening Training page")

            self.frame_signal.emit("STOP_CAMERA_FIRST")
            return
        
        print("training page")
        self.controller_access = False
        self.live_mode = "preview"   # ⭐ reset mode
        self.stopCamera()

        self.app_ref.load_page("training.html")

      
        
    @pyqtSlot()
    @controller_access_required
    def goController(self):

        if self.live_mode == "inspection" and self.camera_running():
            print("⚠ Stop inspection before opening Training page")

            self.frame_signal.emit("STOP_CAMERA_FIRST")
            return
              

        print(">>> goController SLOT CALLED")

        self.stopCamera()
        self.app_ref.load_page("controller.html")


#-------------------          * FUNCTION *     ---------------------------------------
    def on_new_frame(self, frame):

        signal = count_status()

        if self.live_mode == "preview":

            # ONLY SHOW CAMERA
            _, buffer = cv2.imencode(".jpg", frame)
            jpg = base64.b64encode(buffer).decode()
            self.frame_signal.emit(jpg)

        elif self.live_mode == "inspection":

            _, buffer = cv2.imencode(".jpg", frame)
            jpg = base64.b64encode(buffer).decode()
            self.frame_signal.emit(jpg)

            if signal == 1 and self.last_count_signal == 0:

                print("PLC trigger detected (Inspection)")

                if self.model_key:
                    self.request_prediction.emit(frame, self.model_key)

        elif self.live_mode == "training":

            if signal == 1 and self.last_count_signal == 0:

                print("PLC trigger detected (Training)")

                material = self.material
                count = self.count
                yarn = self.yarn

                if material and count and yarn:
                # show only captured frame
                    _, buffer = cv2.imencode(".jpg", frame)
                    jpg = base64.b64encode(buffer).decode()
                    self.frame_signal.emit(jpg)

                    # save image
                    save_dir = TRAINING_IMAGES_DIR / material / count / yarn
                    save_dir.mkdir(parents=True, exist_ok=True)

                    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    save_path = save_dir / f"train_{ts}.jpg"

                    cv2.imwrite(str(save_path), frame)

                    print("Training image saved:", save_path)

                    # run training
                    model_key = f"{material}_{count}_{yarn}"
                    self.request_training.emit(frame, model_key)

                    # IMPORTANT: prevent multiple triggers
                    QThread.msleep(150)

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

    def on_training_result(self, result):

        if result.get("ok"):

            print("Training success")

        else:

            print("Training skipped: No threads detected")

    def on_prediction_result(self, vis, results, bits):

            # show frame
            _, buffer = cv2.imencode(".jpg", vis)
            jpg = base64.b64encode(buffer).decode()
            self.frame_signal.emit(jpg)

            print("Thread Results:", results)
            print("PLC Bits:", bits)

            statuses = ["", "", "", ""]

            for i, r in enumerate(results):

                if isinstance(r, dict):
                    cone_id = r["cone"]
                    status = r["status"]
                    statuses[cone_id - 1] = status

                else:
                    statuses[i] = r

            print("Final Statuses:", statuses)

            # ⭐ SEND TO UI
            self.cone_status_signal.emit(statuses)

            if "DEFECT" in statuses:
                plc_bits = [int(b) for b in bits]
                gripper_function(plc_bits)

     
            
    def load_controller_settings(self):

        settings_file = BASE_DIR / "controller_settings.json"

        if os.path.exists(settings_file):

            with open(settings_file, "r") as f:
                data = json.load(f)

            self.camera_type = data.get("camera", "webcam")
            self.exposure_value = float(data.get("exposure", 5000))

            print("Loaded controller settings:", data)

        else:
            self.exposure_value = 5000 
  
    def camera_running(self):
        return self.camera_thread is not None