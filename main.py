import sys
import os
from time import strftime, gmtime
import threading
from time import sleep
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtCore import QObject, pyqtSignal

class Backend(QObject):
    updated = pyqtSignal(str, arguments=['updater'])  # Declare the signal here

    def __init__(self):
        super().__init__()

    def updater(self, curr_time):
        self.updated.emit(curr_time)

    def bootUp(self):
        t_thread = threading.Thread(target=self._bootUp)
        t_thread.daemon = True
        t_thread.start()

    def _bootUp(self):
        while True:
            curr_time = strftime("%H:%M:%S", gmtime())
            self.updater(curr_time)
            sleep(1)  # Update every second instead of 0.1 seconds for better readability

QQuickWindow.setSceneGraphBackend('software')
app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()

# Connect the engine's quit signal to the application quit
engine.quit.connect(app.quit)

# Construct the QML file path
qml_file = os.path.join(os.path.dirname(__file__), 'UI', 'main.qml')
print(f"Loading QML file from: {qml_file}")

# Check if the QML file exists
if not os.path.exists(qml_file):
    print("Error: QML file does not exist.")
    sys.exit(-1)

# Load the QML file
engine.load(qml_file)

# Check if the QML file was loaded successfully
if not engine.rootObjects():
    print("Error: No root objects found. The QML file might not have been loaded correctly.")
    sys.exit(-1)

# Access the root object
root_object = engine.rootObjects()[0]

back_end = Backend()
root_object.setProperty('backend', back_end)  # Correctly set the backend property
back_end.bootUp()

sys.exit(app.exec())
