# classes/bridge.py

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class Bridge(QObject):

    frame_signal = pyqtSignal(str)

    def __init__(self, app_ref):
        super().__init__()
        self.app_ref = app_ref
        self.live_mode = None

        # -------- TRAINING PLC CAPTURE CONTROL --------
        self._train_plc_last = False
        self._train_last_capture_time = 0
        self._train_min_interval = 0.2   # 200 milliseconds

    # -------- CAMERA ----------
    @pyqtSlot()
    def startCamera(self):
        #self.app_ref.start_camera()
         self.app_ref.start_camera(single_shot=False)

    @pyqtSlot()
    def stopCamera(self):
        self.app_ref.stop_camera()


    @pyqtSlot()
    def startTrainingCapture(self):     # TRAINING START (single frame)
        self.app_ref.start_camera(single_shot=True)   

            
    @pyqtSlot(str, str, str)
    def saveSettings(self, material, count, yarn):
            self.app_ref.save_Settings(material, count, yarn) 


    @pyqtSlot(str, str, str, str)
    def saveTrainingSettings(self, material, count, yarn, model):
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

    @pyqtSlot()
    def startTrainingCapture(self):
        print("Training single capture")
        self.app_ref.start_camera(single_shot=True)     