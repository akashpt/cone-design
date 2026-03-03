# classes/bridge.py

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot ,QThread
import json



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

    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self.live_mode = None

         # -------- CONTINUOUS TRAINING CONTROL --------
        self.training_thread = None
        self.training_worker = None
        self.training_active = False

    # -------- CAMERA ----------
    @pyqtSlot()
    def startCamera(self):
        #self.app_ref.start_camera()
         self.app_ref.start_camera(single_shot=False)

    @pyqtSlot()
    def stopCamera(self):
        self.app_ref.stop_camera()


    @pyqtSlot()
    def startTrainingCapture(self):       # TRAINING START (single frame)
        self.app_ref.start_camera(single_shot=True)  

    @pyqtSlot()
    def setTrainingMode(self):
        # Change capture to 200ms
        self.app_ref.set_capture_interval(200)

    @pyqtSlot()
    def resetNormalMode(self):
        # Restore default 30ms
        self.app_ref.set_capture_interval(30) 
#--------------------------------------------
            
    @pyqtSlot(str, str, str)
    def saveSettings(self, material, count, yarn):
            self.app_ref.save_Settings(material, count, yarn) 


    @pyqtSlot(str, str, str, str)
    def saveTrainingSettings(self, material, count, yarn, model):

        self.material =material
        self.count =count
        self.yarn =yarn
        self.app_ref.save_training_settings(material, count, yarn, model)
              

    # -------- NAVIGATION ----------
    @pyqtSlot()
    def goHome(self):
        self.app_ref.stop_camera()
        self.app_ref.load_page("index.html")

    @pyqtSlot()
    def goReport(self):
        self.app_ref.stop_camera()
        self.app_ref.open_report_window()

    @pyqtSlot()
    def goTraining(self):
        self.app_ref.stop_camera()
        self.app_ref.load_page("training.html")

    @pyqtSlot()
    def startTraining(self):
        print("Training started")
        self.app_ref.stop_camera()
        self.app_ref.start_training_process()  

    
    # --------- TRAINING CONTROL ----------  
    @pyqtSlot(str) 
    def startContinuousTraining(self, settings_json):

       
      

        if self.training_active:
            print("Training already running")
            return

        self.training_thread = QThread()
        self.training_worker = TrainingWorker(self, settings_json, interval_ms=500)

        self.training_worker.moveToThread(self.training_thread)

        self.training_thread.started.connect(self.training_worker.run)
        self.training_worker.finished.connect(self.stopContinuousTraining)

        self.training_thread.start()

        self.training_active = True
        print("✅ Continuous Training Started")   

    @pyqtSlot()
    def stopContinuousTraining(self):

        if not self.training_active:
            return

        self.training_active = False

        if self.training_worker:
            self.training_worker.stop()

        if self.training_thread:
            self.training_thread.quit()
            self.training_thread.wait()

        self.training_worker = None
        self.training_thread = None

        print("✅ Continuous Training Cleanly Stopped")         