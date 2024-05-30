import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QToolBar, QAction, QWidget, QSlider, QLabel, QSplitter, QGraphicsView, QGraphicsScene, QHBoxLayout, QGridLayout, QSizePolicy, QMenu
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MR_PunctureSystem")
        self.setGeometry(100, 100, 1200, 800)

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

    def init_toolbar(self):
        menu_action = QAction("Menu", self)
        menu_action.triggered.connect(self.toggle_sidebar)
        self.toolbar.addAction(menu_action)

        file_action = QAction("File", self)
        file_action.triggered.connect(self.show_file_menu)
        self.toolbar.addAction(file_action)

        load_action = QAction("Load", self)
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

    def init_sidebar(self):
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(int(self.width() * 0.2))  # Set sidebar width to 2/10 of the window
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.splitter.addWidget(self.sidebar)

        self.init_sliders()

    def init_sliders(self):
        sliders_frame = QWidget()
        sliders_layout = QVBoxLayout(sliders_frame)
        sliders_layout.setSpacing(10)  # Optional: adjust spacing between sliders
        sliders_layout.setContentsMargins(0, 0, 0, 0)

        self.add_slider(sliders_layout, "X Value", 512, 256, self.slider_changed)
        self.add_slider(sliders_layout, "Y Value", 512, 256, self.slider_changed)
        self.add_slider(sliders_layout, "Z Value", 512, 256, self.slider_changed)
        self.add_slider(sliders_layout, "X Rotation", 180, 90, self.slider_changed)
        self.add_slider(sliders_layout, "Y Rotation", 180, 90, self.slider_changed)
        self.add_slider(sliders_layout, "Z Rotation", 180, 90, self.slider_changed)

        self.sidebar_layout.addWidget(sliders_frame)
        self.sidebar_layout.addStretch()  # Push sliders to the top

    def add_slider(self, layout, label, maximum, initial_value, callback):
        label_widget = QLabel(label)
        layout.addWidget(label_widget)
        slider = QSlider(Qt.Horizontal)
        slider.setMaximum(maximum)
        slider.setValue(initial_value)
        slider.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        slider.valueChanged.connect(callback)
        layout.addWidget(slider)

    def slider_changed(self, value):
        sender = self.sender()
        print(f"Slider changed: {value}")

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
        file_menu.addAction(raw_data_action)

        coordinate_data_action = QAction("座標データ", self)
        file_menu.addAction(coordinate_data_action)

        puncture_data_action = QAction("穿刺予定座標データ", self)
        file_menu.addAction(puncture_data_action)

        start_end_data_action = QAction("始点終点データ", self)
        file_menu.addAction(start_end_data_action)

        # Show the menu under the "File" action
        file_menu.exec_(self.toolbar.mapToGlobal(self.toolbar.actionGeometry(self.toolbar.actions()[1]).bottomLeft()))

    def show_add_menu(self):
        print("Show add menu")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainPage()
    main_window.show()
    sys.exit(app.exec_())
