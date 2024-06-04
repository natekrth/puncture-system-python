import sys
import os
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QToolBar, QAction, QWidget, QSlider, QLabel, QSplitter, QGraphicsView, QGraphicsScene, QHBoxLayout, QGridLayout, QSizePolicy, QMenu, QFileDialog, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QColor
from concurrent.futures import ThreadPoolExecutor

class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

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
        self.X = 0
        self.Y = 0
        self.Z = 0

        self.x_size = 0
        self.y_size = 0
        self.z_size = 0
        
        self.CenterPoint = Vector3D(0, 0, 0)
        
        self.NeedleMatrix3D = np.zeros((512, 512, 512), dtype=np.int16)
        self.NowMatrix3D = np.zeros((512, 512, 512), dtype=np.int16)
        
        self.IsSelectedItem = 0;   
        self.y_end = 512
        self.ImageStride = 512 * 2
        self.ImagePixelSize = 512 * 512 *2
        self.MaxCTvalue = 0
        self.CT_Ajust = -1000 # Example value, adjust accordingly

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
        self.toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("ZoomOut", self)
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

        self.add_slider(sliders_layout, "X Value", 512, 256, self.slider_changed, "X Value")
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
            self.X = value
        elif sender.objectName() == "Y Value":
            self.Y = value
        elif sender.objectName() == "Z Value":
            self.Z = value
        self.update_images()
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
        panel2 = self.create_panel("XY-Plane")
        panel3 = self.create_panel("YZ-Plane")
        panel4 = self.create_panel("XZ-Plane")

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
        view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(view)

        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scene.addWidget(label)

        panel.scene = scene
        panel.view = view
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
        file, _ = QFileDialog.getOpenFileName(self, "Select a RAW file", "", "RAW Files (*.raw);;All Files (*)", options=options)
        if not file:
            return

        self.load_raw_file(file)

    def load_raw_file(self, file):
        # Open and read the file into a buffer
        with open(file, 'rb') as f:
            buffer = f.read()

        # Convert the buffer to a numpy array
        bytes_array = np.frombuffer(buffer, dtype=np.uint8)
        z_size = int(len(buffer) / self.ImagePixelSize)
        image_data = np.zeros((512, 512, z_size), dtype=np.int16)

        gap1, gap2, gap3, gap4, gap5 = 0, 0, 0, 0, 0

        for k in range(z_size):
            kk = self.ImagePixelSize * k
            for j in range(512):
                jj = self.ImageStride * j
                if j < self.y_end:
                    for i in range(512):
                        BytesNum = kk + jj + 2 * i
                        s = np.int16(bytes_array[BytesNum] * 256 + bytes_array[BytesNum + 1])
                        if s > -600:
                            gap1 += 1
                        if s > self.MaxCTvalue:
                            self.MaxCTvalue = s
                        image_data[i, j, k] = s
                    if k == 0 and gap1 < 100 and gap3 > 300 and gap5 < 200 and j < self.y_end:
                        self.y_end = j - 5
                        j = self.y_end
                    gap5, gap4, gap3, gap2, gap1 = gap4, gap3, gap2, gap1, 0
                else:
                    for i in range(512):
                        image_data[i, j, k] = np.int16(self.CT_Ajust)

        # Create and add picture info to the list
        picture_info = PictureInfo(file)
        picture_info.image_data = image_data
        self.dataList.append(picture_info)
        self.y_end = 512
        
        # Update the list view with the file name
        item = QListWidgetItem(os.path.basename(file))  # Display only the file name
        self.list_view.addItem(item)

        # Print debug information
        print("File loaded:", os.path.basename(file))
        print("Image data shape:", image_data.shape)
        print("Picture Info",picture_info)
        print(image_data)

    def list_view_item_click(self, item):
        for pic_info in self.dataList:
            if os.path.basename(pic_info.file_name) == item.text():
                self.selectedItem = pic_info
                break

        if self.selectedItem:
            self.x_size, self.y_size, self.z_size = self.selectedItem.image_data.shape
            center_point = {'x': self.x_size / 2, 'y': self.y_size / 2, 'z': self.z_size / 2}
            self.IsSelectedItem = 1
            print(f"Selected Item: {os.path.basename(self.selectedItem.file_name)}")
            print(f"Center Point: {center_point}")

            # self.display_images(self.selectedItem.image_data)

    def btnLoadPictures_Click(self):
        if self.IsSelectedItem == 0:
            return
        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)
        # Reset the color of the load button
        # self.app_bar_load.setStyleSheet("")  # Reset to default style
        
    def load_panel_image(self, pa, num):
        if self.IsSelectedItem == 0:
            return
        
        image_2d = np.zeros((512, 512), dtype=np.int16)
        # make_3d_array(self.selected_item.image_data)
        print(pa)
        print(num)
        
        if num == 0:  # 任意断面　軸位断面 : XY 平面
            image_2d = self.make_2d_array_xy(self.NowMatrix3D, self.Z)
        elif num == 1:  # 任意断面　矢状断面 : YZ 平面
            image_2d = self.make_2d_array_yz(self.NowMatrix3D)
        elif num == 2:  # 任意断面　冠状断面 : XZ 平面
            image_2d = self.make_2d_array_xz(self.NowMatrix3D)
        elif num == 3:  # 立体構造
            image_2d = self.make_2d_array_rendering(self.NowMatrix3D)
        elif num == 4:  # 経路表示画面　クリック時点のXY平面表示
            image_2d = self.make_2d_array_xy(self.NowMatrix3D, self.Z)
        else:
            image_2d.fill(255)

        # software_bitmap = self.make_2d_image(image_2d)
        self.update_panel_image(pa, image_2d)
        # pa.set_soft_image(software_bitmap)

        
    # def display_images(self, image_data):
    #     # Assuming the slices are along the Z-axis
    #     xy_slice = self.make_2d_array_xy(image_data, self.Z)
    #     xz_slice = self.make_2d_array_xz(image_data)
    #     yz_slice = self.make_2d_array_yz(image_data)
    #     rendering_slice = self.make_2d_array_rendering(image_data)

    #     self.update_panel_image(self.panels[0], rendering_slice)  # 3D view placeholder
    #     self.update_panel_image(self.panels[1], xy_slice)
    #     self.update_panel_image(self.panels[2], yz_slice)
    #     self.update_panel_image(self.panels[3], xz_slice)

    def update_panel_image(self, panel, image_data):
        image = self.make_2d_image(image_data)
        pixmap = QPixmap.fromImage(image)

        panel.scene.clear()
        panel.scene.addPixmap(pixmap)

    def load_pictures(self):
        if self.selectedItem is None:
            return
        self.display_images(self.selectedItem.image_data)

    def make_2d_array_yz(self, Im):  # Y-Z plane
        vs = np.zeros((512, 512), dtype=np.int16)
        for j in range(512):
            for k in range(512):
                kk = abs(k - 512) - 1
                vs[j, kk] = Im[self.X, j, k]
        return vs

    def make_2d_array_xz(self, Im):  # X-Z plane
        vs = np.zeros((512, 512), dtype=np.int16)
        for i in range(512):
            for k in range(512):
                kk = abs(k - 512) - 1
                vs[i, kk] = Im[i, self.Y, k]
        return vs

    def make_2d_array_xy(self, Im, z):  # X-Y plane
        vs = np.zeros((512, 512), dtype=np.int16)
        ZZ = abs(z - 512) - 1
        for i in range(512):
            for j in range(512):
                vs[i, j] = Im[i, j, ZZ]
        return vs

    def make_2d_array_rendering(self, Im):  # Maximum intensity projection
        vs = np.zeros((self.x_size, self.y_size), dtype=np.int16)
        for i in range(self.x_size):
            for j in range(self.y_size, 16):
                vs[i, j] = self.max_intensity(Im, i, j)
                vs[i, j + 1] = self.max_intensity(Im, i, j + 1)
                vs[i, j + 2] = self.max_intensity(Im, i, j + 2)
                vs[i, j + 3] = self.max_intensity(Im, i, j + 3)
                
                vs[i, j + 4] = self.max_intensity(Im, i, j + 4)
                vs[i, j + 5] = self.max_intensity(Im, i, j + 5)
                vs[i, j + 6] = self.max_intensity(Im, i, j + 6)
                vs[i, j + 7] = self.max_intensity(Im, i, j + 7)
                
                vs[i, j + 8] = self.max_intensity(Im, i, j + 8)
                vs[i, j + 9] = self.max_intensity(Im, i, j + 9)
                vs[i, j + 10] = self.max_intensity(Im, i, j + 10)
                vs[i, j + 11] = self.max_intensity(Im, i, j + 11)
                
                vs[i, j + 12] = self.max_intensity(Im, i, j + 12)
                vs[i, j + 13] = self.max_intensity(Im, i, j + 13)
                vs[i, j + 14] = self.max_intensity(Im, i, j + 14)
                vs[i, j + 15] = self.max_intensity(Im, i, j + 15)
        return vs

    def max_intensity(self, v, I, J, z_size=512):
        M = self.CT_Ajust
        for k in range(z_size):
            _M = v[I, J, k]
            if _M > M:
                M = _M
                if M == self.MaxCTvalue:
                    return M
        return M
        
    # def make_2d_image(self, image_2d):
    #     image_size = 512
    #     qimage = QImage(image_size, image_size, QImage.Format_Grayscale8)

    #     for i in range(image_size):
    #         for j in range(image_size):
    #             value = np.clip(self.noise_reduction(image_2d[i, j]), 0, 255)
    #             qimage.setPixel(i, j, QColor(value, value, value).rgb())
    #     return qimage
    
    def make_2d_image(self, image_2d):
        image_size = 512
        qimage = QImage(image_size, image_size, QImage.Format_Grayscale8)

        for i in range(image_size):
            for j in range(image_size):
                value = np.clip(self.noise_reduction(image_2d[i, j]), 0, 255)
                qimage.setPixel(i, j, int(value)) 
        return qimage
    # def make_2d_image(self, image_2d):  # Create QImage from 2D array
    #     image_2d = ((image_2d - image_2d.min()) / (image_2d.max() - image_2d.min()) * 255).astype(np.uint8)
    #     image_2d = np.rot90(image_2d, k=3)  # Rotate image by 270 degrees clockwise
    #     height, width = image_2d.shape
    #     image_2d_bytes = image_2d.tobytes()
    #     image = QImage(image_2d_bytes, width, height, QImage.Format_Grayscale8)
    #     return image

    def make_z_rotation_matrix(theta):
        return np.array([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1]
        ])

    def make_x_rotation_matrix(theta):
        return np.array([
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)]
        ])

    def make_y_rotation_matrix(theta):
        return np.array([
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)]
        ])

    def calculation_matrix3x3(mat1, mat2):
        return np.dot(mat1, mat2)

    def calculation_matrix3x1(matrix3x3, vector3x1):
        return np.dot(matrix3x3, vector3x1)

    def noise_reduction(self, s):  # Convert CT value to pixel value
        s = self.CT_Ajust if s <= self.CT_Ajust else s
        pixel = (s - self.CT_Ajust) * 255 / (self.MaxCTvalue - self.CT_Ajust)
        return np.uint8(pixel)

    def show_add_menu(self):
        print("Show add menu")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainPage()
    main_window.show()
    sys.exit(app.exec_())
