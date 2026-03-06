# app.py
import sys
from PyQt5.QtWidgets import QApplication ,QMainWindow
from PyQt5.QtCore import QTimer, QUrl ,pyqtSlot ,Qt
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from classes.bridge import Bridge
from path import TEMPLATES_DIR




class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cop Design System")
        self.resize(1200, 800)
        
        

        # Web view
        self.view = QWebEngineView()
        self.setCentralWidget(self.view)

        # Bridge
        self.bridge = Bridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        

        # Load first page
        self.load_page("index.html")

      

    # -------- PAGE LOAD --------
    def load_page(self, page_name):

        print(f"Switching to {page_name}")

        self.view.setUrl(QUrl("about:blank"))

        full_path = TEMPLATES_DIR / page_name

        if full_path.exists():
            self.view.load(QUrl.fromLocalFile(str(full_path)))
        else:
            print("Page not found:", full_path)

        self.view.page().setWebChannel(self.channel)
#----------------------------------------------------------------



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

        report_file = TEMPLATES_DIR / "report.html"
        view.load(QUrl.fromLocalFile(str(report_file.resolve())))

        self.report_window.show()



        

#----------- CLEANUP ON CLOSE --------
    def closeEvent(self, event):

        try:
            self.bridge.stop_camera()
        except:
            pass

        super().closeEvent(event)




# -------------MAIN ENTRY POINT-------
if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

    