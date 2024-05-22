import sys
import os
import numpy as np
import pydicom
from PyQt6.QtGui import QGuiApplication, QImage
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtQuick import QQuickWindow
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

class Backend(QObject):
    imageChanged = pyqtSignal(str, arguments=['image_path'])

    def __init__(self):
        super().__init__()

    @pyqtSlot(str)
    def loadDicom(self, file_path):
        if not os.path.exists(file_path):
            print("Error: DICOM file does not exist.")
            return
        
        dataset = pydicom.dcmread(file_path)
        if 'PixelData' in dataset:
            image_array = dataset.pixel_array
            image_array = self.normalize_image(image_array)
            image_path = self.save_image(image_array)
            self.imageChanged.emit(image_path)

    def normalize_image(self, image_array):
        # Normalize the image to 8-bit grayscale
        image_array = image_array.astype(np.float32)
        image_array = (np.maximum(image_array, 0) / image_array.max()) * 255.0
        return image_array.astype(np.uint8)

    def save_image(self, image_array):
        image = QImage(image_array.data, image_array.shape[1], image_array.shape[0], image_array.strides[0], QImage.Format_Grayscale8)
        image_path = "temp_image.png"
        image.save(image_path)
        return image_path

QQuickWindow.setSceneGraphBackend('software')
app = QGuiApplication(sys.argv)
engine = QQmlApplicationEngine()

engine.quit.connect(app.quit)

qml_file = os.path.join(os.path.dirname(__file__), 'UI', 'main.qml')
print(f"Loading QML file from: {qml_file}")

if not os.path.exists(qml_file):
    print("Error: QML file does not exist.")
    sys.exit(-1)

engine.load(qml_file)

if not engine.rootObjects():
    print("Error: No root objects found. The QML file might not have been loaded correctly.")
    sys.exit(-1)

root_object = engine.rootObjects()[0]

back_end = Backend()
root_object.setProperty('backend', back_end)

sys.exit(app.exec())
