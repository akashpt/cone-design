# # app.py
# import sys
# from PyQt5.QtWidgets import QApplication ,QMainWindow
# from PyQt5.QtCore import QTimer, QUrl ,pyqtSlot ,Qt
# from PyQt5.QtWidgets import QMainWindow
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# from PyQt5.QtWebChannel import QWebChannel
# from classes.bridge import Bridge
# from path import TEMPLATES_DIR




# class MainWindow(QMainWindow):

#     def __init__(self):
#         super().__init__()

#         self.setWindowTitle("Cop Design System")
#         self.resize(1200, 800)
        
        

#         # Web view
#         self.view = QWebEngineView()
#         self.setCentralWidget(self.view)

#         # Bridge
#         self.bridge = Bridge(self)
#         self.channel = QWebChannel()
#         self.channel.registerObject("bridge", self.bridge)
#         self.view.page().setWebChannel(self.channel)

        

#         # Load first page
#         self.load_page("index.html")

      

#     # -------- PAGE LOAD --------
#     def load_page(self, page_name):

#         print(f"Switching to {page_name}")

#         self.view.setUrl(QUrl("about:blank"))

#         full_path = TEMPLATES_DIR / page_name

#         if full_path.exists():
#             self.view.load(QUrl.fromLocalFile(str(full_path)))
#         else:
#             print("Page not found:", full_path)

#         self.view.page().setWebChannel(self.channel)
# #----------------------------------------------------------------



# #----------- REPORT WINDOW --------
    
        
#     def open_report_window(self):

#         # If already open → bring to front
#         if hasattr(self, "report_window") and self.report_window:
#             if self.report_window.isVisible():
#                 self.report_window.activateWindow()
#                 return

#         # Create independent small window
#         self.report_window = QMainWindow()   # no parent

#         self.report_window.setWindowTitle("Report")
#         self.report_window.setFixedSize(1000, 700)  # fixed small 
#         self.report_window.setWindowState(Qt.WindowNoState)

#         view = QWebEngineView()
#         self.report_window.setCentralWidget(view)

#         report_file = TEMPLATES_DIR / "report.html"
#         view.load(QUrl.fromLocalFile(str(report_file.resolve())))

#         self.report_window.show()



        

# #----------- CLEANUP ON CLOSE --------
#     def closeEvent(self, event):

#         try:
#             self.bridge.stop_camera()
#         except:
#             pass

#         super().closeEvent(event)




# # -------------MAIN ENTRY POINT-------
# if __name__ == "__main__":

#     app = QApplication(sys.argv)

#     window = MainWindow()
#     window.show()

#     sys.exit(app.exec_())

    

# app.py

import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel

from classes.bridge import Bridge
from path import TEMPLATES_DIR


# ------------------------------
# Linux Qt platform fix
# # ------------------------------
# if sys.platform.startswith("linux"):
#     os.environ["QT_QPA_PLATFORM"] = "xcb"


# ==============================
# MAIN WINDOW
# ==============================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cop Design System")
        self.resize(1200, 800)

        # -----------------
        # Web View
        # -----------------
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # -----------------
        # Bridge + Channel
        # -----------------
        self.bridge = Bridge(self)

        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)

        self.view.page().setWebChannel(self.channel)

        # -----------------
        # Load first page
        # -----------------
        index_file = (TEMPLATES_DIR / "index.html").resolve()

        print("Loading page:", index_file)

        if index_file.exists():
            self.view.load(QUrl.fromLocalFile(str(index_file)))
        else:
            print("❌ index.html not found:", index_file)

    # =====================================
    # PAGE SWITCH FUNCTION (Bridge uses this)
    # =====================================

    def load_page(self, page_name):

        print(f"Switching to {page_name}")

        file_path = (TEMPLATES_DIR / page_name).resolve()

        if file_path.exists():

            # Clear previous page (important for Linux)
            self.view.setUrl(QUrl("about:blank"))

            # Load new page
            self.view.load(QUrl.fromLocalFile(str(file_path)))

            # Reconnect channel
            self.view.page().setWebChannel(self.channel)

        else:
            print("❌ Page not found:", file_path)

    # =====================================
    # REPORT WINDOW
    # =====================================

    def open_report_window(self):

        # if already open → bring front
        if hasattr(self, "report_window") and self.report_window:
            if self.report_window.isVisible():
                self.report_window.activateWindow()
                return

        self.report_window = QMainWindow()

        self.report_window.setWindowTitle("Report")
        self.report_window.setFixedSize(1000, 700)
        self.report_window.setWindowState(Qt.WindowNoState)

        view = QWebEngineView()
        self.report_window.setCentralWidget(view)

        report_file = (TEMPLATES_DIR / "report.html").resolve()

        if report_file.exists():
            view.load(QUrl.fromLocalFile(str(report_file)))
        else:
            print("❌ report.html not found:", report_file)

        self.report_window.show()

    # =====================================
    # CLOSE EVENT
    # =====================================

    def closeEvent(self, event):

        try:
            if hasattr(self.bridge, "stopCamera"):
                self.bridge.stopCamera()
        except Exception as e:
            print("Camera stop error:", e)

        super().closeEvent(event)


# ==============================
# MAIN ENTRY
# ==============================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())