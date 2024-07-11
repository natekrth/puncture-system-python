import sys
import os
import csv
import math
import numpy as np
import pydicom as dicom
from tkinter import Tk, Frame, Label, Button, Menu, Listbox, filedialog, Scale, HORIZONTAL, LEFT, END, Canvas, Scrollbar, VERTICAL, RIGHT, BOTTOM, X, Y, BOTH, TOP
from tkinter.ttk import Notebook
from PIL import Image, ImageTk
import shutil
from vispy import app, scene
from vispy.scene import visuals
from vispy.visuals.transforms import STTransform
import threading
import time

class Vector3D:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class NeedleInfo:
    def __init__(self, point, vector):
        self.point = point
        self.vector = vector

class MainPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Puncture System")
        self.root.geometry("1200x800")

        self.panels = []
        self.X_init = 256
        self.Y_init = 256
        self.Z_init = 256
        self.X = 256
        self.Y = 256
        self.Z = 256
        self.Z_for_axis = 256

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

        self.needleVector = []
        self.ok = 0
        self._count = 0
        self.timer = None
        self.selectedItem = None

        self.is_clear = False
        self.plan_line_deleted = False
        self.realtime_line_deleted = False
        
        self.init_toolbar()
        self.init_sidebar()
        self.init_main_view()

        self.dataList = []
        
        self.csv_file_path = None  # Path to your CSV file
        self.previous_data_length = 0
        self.realtime_points = []

        self.check_csv_thread = None
        self.stop_thread = False
        
    def init_toolbar(self):
        self.toolbar = Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        menu_button = Button(self.toolbar, text="Menu", command=self.toggle_sidebar)
        menu_button.pack(side="left")

        file_button = Button(self.toolbar, text="File", command=self.show_file_menu)
        file_button.pack(side="left")

        load_button = Button(self.toolbar, text="Load", command=self.btnLoadPictures_Click)
        load_button.pack(side="left")

        start_button = Button(self.toolbar, text="Start Real-Time Route", command=self.start_realtime_data)
        start_button.pack(side="left")
        
        stop_button = Button(self.toolbar, text="Stop Real-Time Route", command=self.stop_realtime_data)
        stop_button.pack(side="left")

    def init_sidebar(self):
        self.sidebar = Frame(self.root)
        self.sidebar.pack(side="left", fill="y")

        self.list_view = Listbox(self.sidebar)
        self.list_view.pack(fill="both", expand=True)
        self.list_view.bind("<<ListboxSelect>>", self.list_view_item_click)

        self.init_sliders()

    def init_sliders(self):
        sliders_frame = Frame(self.sidebar)
        sliders_frame.pack(fill="both", expand=True)

        self.add_slider(sliders_frame, "X Value", 512, 256, lambda value: self.slider_changed("X Value", value))
        self.add_slider(sliders_frame, "Y Value", 512, 256, lambda value: self.slider_changed("Y Value", value))
        self.add_slider(sliders_frame, "Z Value", 512, 256, lambda value: self.slider_changed("Z Value", value))
        self.add_slider(sliders_frame, "X Rotation", 180, 90, lambda value: self.slider_changed("X Rotation", value))
        self.add_slider(sliders_frame, "Y Rotation", 360, 90, lambda value: self.slider_changed("Y Rotation", value))
        self.add_slider(sliders_frame, "Z Rotation", 360, 90, lambda value: self.slider_changed("Z Rotation", value))

    def add_slider(self, parent, label_text, maximum, initial_value, command):
        label = Label(parent, text=label_text)
        label.pack()
        slider = Scale(parent, from_=0, to=maximum, orient=HORIZONTAL, command=command)
        slider.set(initial_value)
        slider.pack()

    def slider_changed(self, name, value):
        z_ratio = 512 / (self.Z_init)
        if name == "X Value":
            self.Y = int(value)
        elif name == "Y Value":
            self.X = int(value)
        elif name == "Z Value":
            self.Z_for_axis = int(value)
            low_end = 256 - (self.Z_init // 2)
            upper_end = 256 + (self.Z_init // 2)
            self.Z = int(value)
            if self.Z < low_end:
                self.Z = 1234
            elif self.Z > upper_end:
                self.Z = 1234
            else:
                self.Z = -int(int(value) - low_end)
                if self.Z == 0:
                    self.Z = -1
        elif name == "X Rotation":
            self.view.camera.elevation = float(value)
        elif name == "Y Rotation":
            self.view.camera.azimuth = float(value)
        elif name == "Z Rotation":
            self.view.camera.roll = float(value)
        self.update_images()
        self.draw_realtime_line()  # Redraw the real-time line on the XY-plane
        self.update_realtime_line_vispy()  # Redraw the real-time line in 3D
        print(f"Slider changed: {name} to {int(value)}")

    def init_main_view(self):
        self.main_view_frame = Frame(self.root)
        self.main_view_frame.pack(side="right", fill="both", expand=True)

        self.canvas = Canvas(self.main_view_frame)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar_y = Scrollbar(self.main_view_frame, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")

        self.scrollbar_x = Scrollbar(self.main_view_frame, orient=HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.main_view_frame.grid_rowconfigure(0, weight=1)
        self.main_view_frame.grid_columnconfigure(0, weight=1)

        self.canvas.configure(xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.content_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.init_panels()
        
        self.view = scene.SceneCanvas(keys='interactive', show=False).central_widget.add_view()

    def init_panels(self):
        self.panel2 = self.create_panel("XY", "magenta", "yellow")
        self.panel3 = self.create_panel("YZ", "blue", "magenta")
        self.panel4 = self.create_panel("XZ", "blue", "yellow")

        self.panel2.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.panel3.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.panel4.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)

        self.content_frame.grid_columnconfigure(0, weight=1, minsize=512)
        self.content_frame.grid_columnconfigure(1, weight=1, minsize=512)
        self.content_frame.grid_rowconfigure(0, weight=1, minsize=512)
        self.content_frame.grid_rowconfigure(1, weight=1, minsize=512)

        self.panels.extend([self.panel2, self.panel3, self.panel4])

        self.update_panel_images()

    def create_panel(self, label_text, x_color, y_color):
        panel = Frame(self.content_frame, bg="black", width=512, height=512)
        panel.pack_propagate(False)
        panel.canvas = Canvas(panel, bg="black")
        panel.canvas.pack(fill="both", expand=True, anchor="center")
        return panel

    def update_panel_images(self):
        for num, pa in enumerate(self.panels):
            size = min(pa.winfo_width(), pa.winfo_height())
            pa.config(width=size, height=size)
            self.load_panel_image(pa, num)
            if num == 0:
                self.draw_axes_value_change(pa, "magenta", "yellow", self.Y, self.X)
            elif num == 1:
                self.draw_axes_value_change(pa, "blue", "magenta", self.X, self.Z_for_axis)
            elif num == 2:
                self.draw_axes_value_change(pa, "blue", "yellow", self.Y, self.Z_for_axis)

    def draw_axes_value_change(self, panel, x_color, y_color, x_axis, y_axis):
        panel.canvas.delete("axes")
        width = panel.canvas.winfo_width()
        height = panel.canvas.winfo_height()
        width_ratio = 512 / width
        height_ratio = 512 / height
        if y_axis == self.Z_for_axis:
            panel.canvas.create_line(0, (height - (y_axis / height_ratio)), width, (height - (y_axis / height_ratio)), fill=x_color, tags="axes")
            panel.canvas.create_line(x_axis / width_ratio, 0, x_axis / width_ratio, height, fill=y_color, tags="axes")
        else:
            panel.canvas.create_line(0, y_axis / height_ratio, width, y_axis / height_ratio, fill=x_color, tags="axes")
            panel.canvas.create_line(x_axis / width_ratio, 0, x_axis / width_ratio, height, fill=y_color, tags="axes")
    
    def toggle_sidebar(self):
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y")

    def show_file_menu(self):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="DICOM Folder", command=self.input_button_click)
        menu.add_command(label="Puncture Planned Route CSV", command=self.input_plan_coor_data)
        menu.add_command(label="Puncture Real-Time Route CSV", command=self.select_realtime_csv)
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def select_realtime_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.csv_file_path = file_path
            self.realtime_line_deleted = False
            print(f"Selected CSV file: {self.csv_file_path}")

    def input_button_click(self):
        folder = filedialog.askdirectory(title="Select a Folder")
        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):
        folder_name = os.path.basename(folder)
        destination = os.path.join(os.getcwd() + "/dicom-folder", folder_name)
        if not os.path.exists(destination):
            shutil.copytree(folder, destination)
        self.dataList.append(destination)
        self.list_view.insert(END, folder_name)

    def list_view_item_click(self, event):
        selected_indices = self.list_view.curselection()
        if selected_indices:
            self.selectedItem = self.list_view.get(selected_indices[0])
            self.IsSelectedItem = 1
            self.load_dicom_images(self.selectedItem)

    def btnLoadPictures_Click(self):
        if self.IsSelectedItem == 0:
            return
        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)
        self.visualize_vispy(self.volume3d)

    def load_panel_image(self, pa, num):
        if self.IsSelectedItem == 0:
            return
        try:
            if num == 0:
                image_2d = self.volume3d[:, :, self.Z]
            elif num == 1:
                image_2d = np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
            elif num == 2:
                image_2d = np.flipud(np.rot90(self.volume3d[self.X, :, :]))
            else:
                image_2d = np.zeros((512, 512), dtype=np.int16)
        except IndexError:
            image_2d = np.zeros((512, 512), dtype=np.int16)
        self.update_panel_image(pa, image_2d)
        try:
            if not self.is_clear:
                self.draw_needle_plan()
        except AttributeError:
            pass

    def update_panel_image(self, panel, image_data):
        image = self.make_2d_image(image_data) if image_data is not None else None
        photo = ImageTk.PhotoImage(image=image) if image_data is not None else None
        panel.canvas.delete("axes")
        panel.canvas.delete("images")

        if photo:
            canvas_width = panel.canvas.winfo_width()
            canvas_height = panel.canvas.winfo_height()
            image_width = photo.width()
            image_height = photo.height()
            x = (canvas_width - image_width) // 2
            y = (canvas_height - image_height) // 2
            panel.canvas.create_image(x, y, image=photo, anchor='nw')
            panel.canvas.image = photo
        if panel == self.panel2:
            self.draw_axes_value_change(panel, "magenta", "yellow", self.Y, self.X)
        elif panel == self.panel3:
            self.draw_axes_value_change(panel, "blue", "magenta", self.X, self.Z_for_axis)
        elif panel == self.panel4:
            self.draw_axes_value_change(panel, "blue", "yellow", self.Y, self.Z_for_axis)

    def load_dicom_images(self, folder_name):
        path = "./dicom-folder/" + folder_name
        ct_images = os.listdir(path)
        slices = [dicom.read_file(os.path.join(path, s), force=True) for s in ct_images]
        slices = sorted(slices, key=lambda x: x.ImagePositionPatient[2], reverse=True)

        pixel_spacing = slices[0].PixelSpacing
        slices_thickness = slices[0].SliceThickness

        img_shape = list(slices[0].pixel_array.shape)
        img_shape.append(len(slices))
        self.volume3d = np.zeros(img_shape)

        for i, s in enumerate(slices):
            array2D = s.pixel_array
            self.volume3d[:, :, i] = array2D

        self.X_init = img_shape[0]
        self.Y_init = img_shape[1]
        self.Z_init = img_shape[2]
        self.X = img_shape[0] // 2
        self.Y = img_shape[1] // 2
        self.Z = img_shape[2] // 2
        print("X,Y,Z: ", self.X_init, self.Y_init, self.Z_init)

    def make_2d_image(self, image_2d):
        if image_2d.max() - image_2d.min() != 0:
            normalized_image = ((image_2d - image_2d.min()) / (image_2d.max() - image_2d.min()) * 255).astype(np.uint8)
        else:
            normalized_image = np.zeros(image_2d.shape, dtype=np.uint8)
        height, width = normalized_image.shape
        image = Image.fromarray(normalized_image)
        return image

    def update_images(self):
        for num, pa in enumerate(self.panels):
            self.load_panel_image(pa, num)

    def zoom_in(self):
        self.zoom(1.1)

    def zoom_out(self):
        self.zoom(0.9)

    def zoom(self, factor):
        pass

    def show_add_menu(self):
        menu2 = Menu(self.root, tearoff=0)
        menu2.add_command(label="New window")
        menu2.add_command(label="Axial cross section", command=self.add_panel_xy)
        menu2.add_command(label="Sagittal section", command=self.add_panel_yz)
        menu2.add_command(label="coronal section", command=self.add_panel_xz)
        menu2.add_command(label="3D Structure")
        menu2.add_command(label="Puncture needle position display")
        menu2.add_command(label="Puncture needle route display")
        menu2.add_command(label="Puncture route dispplay")
        menu2.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
        
    def add_panel_xy(self):
        self.panel5 = self.create_panel("options", "white", "white")
        self.panel5.grid(row=0, column=2, sticky="nsew", padx=1, pady=1)
        self.panels.append(self.panel5)
        self.load_panel_image(self.panel5, 1)
        
    def add_panel_yz(self):
        pass
    
    def add_panel_xz(self):
        pass
    
    def input_plan_coor_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        self.is_clear = False
        self.plan_line_deleted = False
        with open(file_path, newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            points = [list(map(float, row)) for row in csv_reader]
        
        if len(points) < 2:
            return

        self.point_start = points[0]
        self.point_end = points[1]
        print(self.point_start, self.point_end)
        
        self.draw_needle_plan()
        self.draw_needle_plan_vispy()

    def draw_needle_plan(self):
        if self.plan_line_deleted:
            return
        try:
            for panel, plane in zip([self.panel2], ["xy"]):
                if plane == "xy":
                    x0, y0 = self.point_start[0], self.point_start[1]
                    x1, y1 = self.point_end[0], self.point_end[1]
                x0 = x0 * (panel.canvas.winfo_width() / 512)
                y0 = y0 * (panel.canvas.winfo_height() / 512)
                x1 = x1 * (panel.canvas.winfo_width() / 512)
                y1 = y1 * (panel.canvas.winfo_height() / 512)
                self.create_dash_line(panel.canvas, x0, y0, x1, y1, fill="green", tags="needle")
        except AttributeError:
            pass

    def create_dash_line(self, canvas, x0, y0, x1, y1, fill, tags):
        dash_length = 5
        gap_length = 3
        line_width = 3
        total_length = ((x1 - x0)**2 + (y1 - y0)**2) ** 0.5
        num_dashes = int(total_length // (dash_length + gap_length))
        for i in range(num_dashes):
            start_x = x0 + (x1 - x0) * (i * (dash_length + gap_length)) / total_length
            start_y = y0 + (y1 - y0) * (i * (dash_length + gap_length)) / total_length
            end_x = start_x + (x1 - x0) * dash_length / total_length
            end_y = start_y + (y1 - y0) * dash_length / total_length
            canvas.create_line(start_x, start_y, end_x, end_y, fill=fill, tags=tags, width=line_width)
    
    def clear_needle(self):
        self.is_clear = True
        self.plan_line_deleted = True
        self.realtime_line_deleted = True
        for panel in self.panels:
            panel.canvas.delete("needle")
            panel.canvas.delete("realtime")
        if hasattr(self, 'dash_line'):
            self.dash_line.set_data(np.array([]))

    def visualize_vispy(self, volume3d):
        self.canvas = scene.SceneCanvas(keys='interactive', show=True)
        self.view = self.canvas.central_widget.add_view()

        new_volumn3d = np.flipud(np.rollaxis(volume3d, 2))
        self.volume = scene.visuals.Volume(new_volumn3d, parent=self.view.scene, threshold=0.225)

        self.view.camera = scene.cameras.TurntableCamera(parent=self.view.scene, fov=60, elevation=90, azimuth=270, roll=90)
        
        self.view.camera.elevation_range = (0, 180)
        self.view.camera.azimuth_range = (None, None)

        axis = scene.visuals.XYZAxis(parent=self.view.scene)
        s = STTransform(translate=(50, 50, 0), scale=(50, 50, 50))
        axis.transform = s

        self.scatter = visuals.Markers()
        self.view.add(self.scatter)
        
        self.dash_line = visuals.Line(color='green', width=3, method='gl', parent=self.view.scene)
        self.realtime_line_vispy = visuals.Line(color='red', width=2, method='gl', parent=self.view.scene)  # Initialize the real-time line visual
        self.view.add(self.realtime_line_vispy)  # Ensure the real-time line visual is added to the view
        
        self.draw_needle_plan_vispy()

    def draw_needle_plan_vispy(self):
        if self.plan_line_deleted:
            return
        try:
            x0, y0, z0 = self.point_start
            x1, y1, z1 = self.point_end
            dash_length = 5
            gap_length = 3
            total_length = ((x1 - x0)**2 + (y1 - y0)**2 + (z1 - z0)**2) ** 0.5
            num_dashes = int(total_length // (dash_length + gap_length))

            points = []
            for i in range(num_dashes):
                start_x = x0 + (x1 - x0) * (i * (dash_length + gap_length)) / total_length
                start_y = y0 + (y1 - y0) * (i * (dash_length + gap_length)) / total_length
                start_z = z0 + (z1 - z0) * (i * (dash_length + gap_length)) / total_length
                end_x = start_x + (x1 - x0) * dash_length / total_length
                end_y = start_y + (y1 - y0) * dash_length / total_length
                end_z = start_z + (z1 - z0) * dash_length / total_length
                points.extend([[start_x, start_y, start_z], [end_x, end_y, end_z]])

            self.dash_line.set_data(np.array(points), connect='segments')
        except AttributeError:
            pass
        
    def start_realtime_data(self):
        if self.csv_file_path is None:
            print("Please select a CSV file first.")
            return

        if self.check_csv_thread is None:
            self.stop_thread = False
            self.check_csv_thread = threading.Thread(target=self.check_csv_for_updates)
            self.check_csv_thread.daemon = True
            self.check_csv_thread.start()
            print("Started real-time data acquisition")

    def stop_realtime_data(self):
        self.stop_thread = True
        self.check_csv_thread = None
        print("Stopped real-time data acquisition")

    def check_csv_for_updates(self):
        while not self.stop_thread:
            with open(self.csv_file_path, 'r') as file:
                reader = csv.reader(file)
                data = list(reader)

            if len(data) > self.previous_data_length:
                new_rows = data[self.previous_data_length:]
                self.previous_data_length = len(data)

                for row in new_rows:
                    x, y, z = map(float, row)
                    self.realtime_points.append([x, y, z])
                    print(self.realtime_points)
                    self.draw_realtime_line()

            time.sleep(1)  # Check for new data every second

    def draw_realtime_line(self):
        if self.realtime_line_deleted:
            return
        # Draw on XY-plane
        self.panel2.canvas.delete("realtime")
        for i in range(1, len(self.realtime_points)):
            x0, y0 = self.realtime_points[i-1][:2]
            x1, y1 = self.realtime_points[i][:2]
            self.create_dash_line(self.panel2.canvas, x0, y0, x1, y1, fill="red", tags="realtime")

        # Draw on 3D visualization
        self.update_realtime_line_vispy()

    def update_realtime_line_vispy(self):
        if self.realtime_line_deleted:
            return
        if not hasattr(self, 'realtime_line_vispy'):
            self.realtime_line_vispy = visuals.Line(color='red', width=2, method='gl', parent=self.view.scene)

        # Ensure the real-time points are converted correctly for the 3D plot
        if self.realtime_points:
            points = np.array(self.realtime_points)
            self.realtime_line_vispy.set_data(points, connect='strip')
    
    def delete_plan_line(self):
        self.plan_line_deleted = True
        self.panel2.canvas.delete("needle")
        if hasattr(self, 'dash_line'):
            self.dash_line.set_data(np.array([]))

    def delete_realtime_line(self):
        self.realtime_line_deleted = True
        self.panel2.canvas.delete("realtime")
        if hasattr(self, 'realtime_line_vispy'):
            self.realtime_line_vispy.set_data(np.array([]))

if __name__ == '__main__':
    root = Tk()
    app = MainPage(root)
    root.mainloop()
