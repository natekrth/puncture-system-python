import sys
import os
import numpy as np
import pydicom as dicom
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QToolBar, QAction, QWidget, QSlider, QLabel, QSplitter, QGraphicsView, QGraphicsScene, QHBoxLayout, QGridLayout, QSizePolicy, QMenu, QFileDialog, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, QLineF
from PyQt5.QtGui import QImage, QPixmap, QColor, QPen
import shutil


class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Matrix3D:
    def __init__(self, x1=0, x2=0, x3=0, y1=0, y2=0, y3=0, z1=0, z2=0, z3=0):
        self.x1 = x1
        self.x2 = x2
        self.x3 = x3
        self.y1 = y1
        self.y2 = y2
        self.y3 = y3
        self.z1 = z1
        self.z2 = z2
        self.z3 = z3
        
class PictureInfo:
    def __init__(self, file_name):
        self.file_name = file_name
        self.image_data = None

class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MR_PunctureSystem")
        self.setGeometry(100, 100, 1200, 800)

        # Placeholder for panel number and current slice indexes
        self.panels = []
        self.X = 256
        self.Y = 256
        self.Z = 256

        self.x_size = 512
        self.y_size = 512
        self.z_size = 512
        
        self.thetaX = 0
        self.thetaY = 0
        self.thetaZ = 0
        
        self.CenterPoint = Vector3D(0, 0, 0)
        
        self.NeedleMatrix3D = np.zeros((512, 512, 512), dtype=np.int16)
        self.NowMatrix3D = np.zeros((512, 512, 512), dtype=np.int16)
        
        self.IsSelectedItem = 0   
        self.y_end = 512
        self.ImageStride = 512 * 2
        self.ImagePixelSize = 512 * 512 * 2
        self.MaxCTvalue = 0
        self.CT_Ajust = -1000  # Example value, adjust accordingly

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        self.toolbar = QToolBar()
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.init_toolbar()

        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        self.init_sidebar()
        self.init_main_view()

        self.dataList = []
        self.selectedItem = None
        
    def init_toolbar(self):
        menu_action = QAction("Menu", self)
        menu_action.triggered.connect(self.toggle_sidebar)
        self.toolbar.addAction(menu_action)

        file_action = QAction("File", self)
        file_action.triggered.connect(self.show_file_menu)
        self.toolbar.addAction(file_action)

        load_action = QAction("Load", self)
        load_action.triggered.connect(self.btnLoadPictures_Click)
        self.toolbar.addAction(load_action)

        add_action = QAction("Add", self)
        add_action.triggered.connect(self.show_add_menu)
        self.toolbar.addAction(add_action)

        delete_action = QAction("Delete", self)
        self.toolbar.addAction(delete_action)

        exchange_action = QAction("Exchange", self)
        self.toolbar.addAction(exchange_action)

        zoom_in_action = QAction("ZoomIn", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        self.toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("ZoomOut", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        self.toolbar.addAction(zoom_out_action)

        self.load_pictures_action = QAction("Load Pictures", self)
        self.load_pictures_action.triggered.connect(self.load_pictures)
        self.toolbar.addAction(self.load_pictures_action)

    def init_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(int(self.width() * 0.2))  # Set sidebar width to 2/10 of the window
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.splitter.addWidget(self.sidebar)

        self.list_view = QListWidget()
        self.list_view.itemClicked.connect(self.list_view_item_click)
        self.sidebar_layout.addWidget(self.list_view)

        self.init_sliders()

    def init_sliders(self):
        sliders_frame = QWidget()
        sliders_layout = QVBoxLayout(sliders_frame)
        sliders_layout.setSpacing(10)  # Optional: adjust spacing between sliders
        sliders_layout.setContentsMargins(0, 0, 0, 0)

        self.add_slider(sliders_layout, "X Value", 170, 0, self.slider_changed, "X Value")
        self.add_slider(sliders_layout, "Y Value", 512, 256, self.slider_changed, "Y Value")
        self.add_slider(sliders_layout, "Z Value", 512, 256, self.slider_changed, "Z Value")
        self.add_slider(sliders_layout, "X Rotation", 180, 90, self.slider_changed, "X Rotation")
        self.add_slider(sliders_layout, "Y Rotation", 180, 90, self.slider_changed, "Y Rotation")
        self.add_slider(sliders_layout, "Z Rotation", 180, 90, self.slider_changed, "Z Rotation")

        self.sidebar_layout.addWidget(sliders_frame)
        self.sidebar_layout.addStretch()  # Push sliders to the top

    def add_slider(self, layout, label, maximum, initial_value, callback, object_name):
        label_widget = QLabel(label)
        layout.addWidget(label_widget)
        slider = QSlider(Qt.Horizontal)
        slider.setMaximum(maximum)
        slider.setValue(initial_value)
        slider.setObjectName(object_name)
        slider.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        slider.valueChanged.connect(callback)
        layout.addWidget(slider)

    def slider_changed(self, value):
        sender = self.sender()
        if sender.objectName() == "X Value":
            self.Z = value
        elif sender.objectName() == "Y Value":
            self.X = value
        elif sender.objectName() == "Z Value":
            self.Y = value
        self.update_images()
        self.update_axis_lines()
        print(f"Slider changed: {sender.objectName()} to {value}")

    def init_main_view(self):
        self.main_view_container = QWidget()
        self.main_view_layout = QGridLayout(self.main_view_container)
        self.main_view_layout.setSpacing(0)  # Remove spacing between panels
        self.main_view_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the layout
        self.splitter.addWidget(self.main_view_container)

        self.init_panels()

    def init_panels(self):
        # Add panels to the grid layout
        panel1 = self.create_panel("3D")
        panel2 = self.create_panel("XY")
        panel3 = self.create_panel("YZ")
        panel4 = self.create_panel("XZ")  # Placeholder for 3D view if needed

        self.main_view_layout.addWidget(panel1, 0, 0)
        self.main_view_layout.addWidget(panel2, 0, 1)
        self.main_view_layout.addWidget(panel3, 1, 0)
        self.main_view_layout.addWidget(panel4, 1, 1)

        self.panels.extend([panel1, panel2, panel3, panel4])

    def create_panel(self, label_text):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(0)  # Remove spacing within the panel
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins within the panel

        scene = QGraphicsScene()
        view = QGraphicsView(scene)
        view.setBackgroundBrush(QColor(Qt.black))  # Set the background to black
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(view)
        
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        # label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setFixedSize(100, 40)  # Adjust the size as needed
        scene.addWidget(label)
        
        # Add x-axis and y-axis lines
        pen_x = QPen(QColor(Qt.magenta))
        pen_y = QPen(QColor(Qt.yellow))
        pen_z = QPen(QColor(Qt.cyan))
        panel.x_axis = scene.addLine(QLineF(0, 0, 0, 0), pen_x)  # Placeholder line
        panel.y_axis = scene.addLine(QLineF(0, 0, 0, 0), pen_y)  # Placeholder line
        panel.z_axis = scene.addLine(QLineF(0, 0, 0, 0), pen_z)  # Placeholder line

        panel.scene = scene
        panel.view = view
        panel.scale_factor = 1.0  # Add a scale factor attribute to the panel
        
        view.resizeEvent = lambda event: self.update_axis_lines()  # Update lines when the view is resized
        return panel

    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()

    def show_file_menu(self):
        # Create a drop-down menu for the "File" action
        file_menu = QMenu(self)

        raw_data_action = QAction("RAWデータ", self)
        raw_data_action.triggered.connect(self.input_button_click)
        file_menu.addAction(raw_data_action)

        coordinate_data_action = QAction("座標データ", self)
        file_menu.addAction(coordinate_data_action)

        puncture_data_action = QAction("穿刺予定座標データ", self)
        file_menu.addAction(puncture_data_action)

        start_end_data_action = QAction("始点終点データ", self)
        file_menu.addAction(start_end_data_action)

        # Show the menu under the "File" action
        file_menu.exec_(self.toolbar.mapToGlobal(self.toolbar.actionGeometry(self.toolbar.actions()[1]).bottomLeft()))

    def input_button_click(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        folder = QFileDialog.getExistingDirectory(self, "Select a Folder", options=options)
        if not folder:
            return

        self.load_folder(folder)

    def load_folder(self, folder):
        # Get the folder name
        folder_name = os.path.basename(folder)
        
        # Define the destination path in the current working directory
        destination = os.path.join(os.getcwd()+"/dicom-folder", folder_name)
        # Copy the entire folder to the destination
        if not os.path.exists(destination):
            shutil.copytree(folder, destination)
        
        # Save the folder path in dataList
        self.dataList.append(destination)
        
        # Update the list view with the folder name
        item = QListWidgetItem(folder_name)  # Display only the folder name
        self.list_view.addItem(item)

    def list_view_item_click(self, item):
        self.selectedItem = item.text()
        
        if self.selectedItem:
            self.IsSelectedItem = 1
            print(f"Selected Item: {self.selectedItem}")
            self.load_dicom_images(self.selectedItem)  # Load the DICOM images
            # self.update_images()

    def btnLoadPictures_Click(self):
        if self.IsSelectedItem == 0:
            return
        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)

    def load_panel_image(self, pa, num):
        if self.IsSelectedItem == 0:
            return
        
        if num == 1:  # Axial view XY
            image_2d = self.volume3d[:, :, self.Z]
        elif num == 2:  # Sagittal view YZ 
            image_2d = np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
        elif num == 3:  # Coronal view XZ
            image_2d = np.flipud(np.rot90(self.volume3d[self.X, :, :]))
        else:
            image_2d = np.zeros((512, 512), dtype=np.int16)  # Placeholder for the 3D view
        self.update_panel_image(pa, image_2d)

    def update_panel_image(self, panel, image_data):
        image = self.make_2d_image(image_data)
        pixmap = QPixmap.fromImage(image)
        panel.scene.clear()
        panel.scene.addPixmap(pixmap)
        panel.view.setScene(panel.scene)
        panel.view.setTransform(panel.view.transform().scale(panel.scale_factor, panel.scale_factor))  # Apply scaling

    def load_pictures(self):
        # if self.selectedItem is None:
        #     return
        self.display_images(self.selectedItem.image_data)

    def make_2d_image(self, image_2d):
        # Normalize the image data
        normalized_image = ((image_2d - image_2d.min()) / (image_2d.max() - image_2d.min()) * 255).astype(np.uint8)
        
        # Set the background to black where pixel values are above a certain threshold (e.g., 250)
        threshold = 250
        background_mask = normalized_image > threshold
        normalized_image[background_mask] = 0
        
        # Create QImage
        height, width = normalized_image.shape
        image_2d_bytes = normalized_image.tobytes()
        image = QImage(image_2d_bytes, width, height, QImage.Format_Grayscale8)
        return image

    def get_image_position(slice):
        return slice.ImagePositionPatient[2]

    def load_dicom_images(self, folder_name):
        path = "./dicom-folder/" + folder_name
        ct_images = os.listdir(path)
        slices = [dicom.read_file(path + '/' + s, force=True) for s in ct_images]
        slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2], reverse=True)

        pixel_spacing = slices[0].PixelSpacing
        slices_thickness = slices[0].SliceThickness

        axial_aspect_ratio = pixel_spacing[1] / pixel_spacing[0]
        sagittal_aspect_ratio = pixel_spacing[1] / slices_thickness
        coronal_aspect_ratio = slices_thickness / pixel_spacing[0]

        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        self.volume3d = np.zeros(img_shape)

        for i, s in enumerate(slices):
            array2D = s.pixel_array
            self.volume3d[:, :, i] = array2D

        self.X = img_shape[0] // 2
        self.Y = img_shape[1] // 2
        self.Z = img_shape[2] // 2

    def show_add_menu(self):
        print("Show add menu")

    def update_images(self):
        # if not self.selectedItem:
        #     return

        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)

    def zoom_in(self):
        self.zoom(1.1)

    def zoom_out(self):
        self.zoom(0.9)

    def zoom(self, factor):
        for panel in self.panels:
            panel.scale_factor *= factor
            panel.view.setTransform(panel.view.transform().scale(factor, factor))
            self.update_panel_image(panel, self.get_current_image_data(panel))

    def get_current_image_data(self, panel):
        if panel == self.panels[0]:  # Axial view XY
            return self.volume3d[:, :, self.Z]
        elif panel == self.panels[1]:  # Sagittal view YZ
            return np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
        elif panel == self.panels[2]:  # Coronal view XZ
            return np.flipud(np.rot90(self.volume3d[self.X, :, :]))
        else:
            return np.zeros((512, 512), dtype=np.int16)  # Placeholder for the 3D view

    def update_axis_lines(self):
        for panel in self.panels:
            width = panel.view.viewport().width()
            height = panel.view.viewport().height()
            if panel == self.panels[1]:  # XY panel
                panel.x_axis.setLine(QLineF(0, self.X, width, self.X))
                panel.y_axis.setLine(QLineF(self.Z, 0, self.Z, height))
            elif panel == self.panels[2]:  # YZ panel
                panel.z_axis.setLine(QLineF(0, self.Y, width, self.Y))
                panel.x_axis.setLine(QLineF(self.X, 0, self.X, height))
            elif panel == self.panels[3]:  # XZ panel
                panel.z_axis.setLine(QLineF(0, self.Y, width, self.Y))
                panel.y_axis.setLine(QLineF(self.Z, 0, self.Z, height))



    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_axis_lines()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainPage()
    main_window.show()
    sys.exit(app.exec_())
