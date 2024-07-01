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
import SimpleITK as sitk
from vispy import app, scene

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
        self.root.title("MR_PunctureSystem")
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
        self.init_toolbar()
        self.init_sidebar()
        self.init_main_view()

        self.dataList = []
        self.selectedItem = None

    def init_toolbar(self):
        self.toolbar = Frame(self.root)
        self.toolbar.pack(side="top", fill="x")

        menu_button = Button(self.toolbar, text="Menu", command=self.toggle_sidebar)
        menu_button.pack(side="left")

        file_button = Button(self.toolbar, text="File", command=self.show_file_menu)
        file_button.pack(side="left")

        load_button = Button(self.toolbar, text="Load", command=self.btnLoadPictures_Click)
        load_button.pack(side="left")

        add_button = Button(self.toolbar, text="Add", command=self.show_add_menu)
        add_button.pack(side="left")

        delete_button = Button(self.toolbar, text="Delete")
        delete_button.pack(side="left")

        exchange_button = Button(self.toolbar, text="Exchange")
        exchange_button.pack(side="left")

        zoom_in_button = Button(self.toolbar, text="ZoomIn", command=self.zoom_in)
        zoom_in_button.pack(side="left")

        zoom_out_button = Button(self.toolbar, text="ZoomOut", command=self.zoom_out)
        zoom_out_button.pack(side="left")

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
        self.add_slider(sliders_frame, "Y Rotation", 180, 90, lambda value: self.slider_changed("Y Rotation", value))
        self.add_slider(sliders_frame, "Z Rotation", 180, 90, lambda value: self.slider_changed("Z Rotation", value))

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
            print(self.Z_for_axis)
            low_end = 256 - (self.Z_init // 2)
            upper_end = 256 + (self.Z_init // 2)
            upper_end_ratio = upper_end / self.Z_init
            self.Z = int(value)
            if self.Z < low_end:  # set screen to black with z-value lower than low end of the image
                self.Z = 1234
            elif self.Z > upper_end:  # set screen to black with z-value higher than upper end of the image
                self.Z = 1234
            else:
                self.Z = -int(int(value) - low_end)
                if self.Z == 0:  # prevent img from being loop when self.Z == 0 because it the same number with
                    self.Z = -1
        self.update_images()
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

    def init_panels(self):
        self.panel1 = self.create_panel("3D", "white", "white")
        self.panel2 = self.create_panel("XY", "magenta", "yellow")
        self.panel3 = self.create_panel("YZ", "blue", "magenta")
        self.panel4 = self.create_panel("XZ", "blue", "yellow")

        self.panel1.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.panel2.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.panel3.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        self.panel4.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)

        self.content_frame.grid_columnconfigure(0, weight=1, minsize=512)
        self.content_frame.grid_columnconfigure(1, weight=1, minsize=512)
        self.content_frame.grid_rowconfigure(0, weight=1, minsize=512)
        self.content_frame.grid_rowconfigure(1, weight=1, minsize=512)

        self.panels.extend([self.panel1, self.panel2, self.panel3, self.panel4])

        # Initial axes
        self.update_panel_images()

    def create_panel(self, label_text, x_color, y_color):
        panel = Frame(self.content_frame, bg="white", width=512, height=512)
        panel.pack_propagate(False)  # Prevent the panel from resizing to fit its contents
        panel.canvas = Canvas(panel, bg="white")
        panel.canvas.pack(fill="both", expand=True, anchor="center")
        # panel.bind("<Configure>", self.on_panel_resize)
        
        return panel

    # def on_panel_resize(self, event):
        # Delay the execution to ensure the size update is complete
        # self.root.after(100, self.update_panel_images)

    def update_panel_images(self):
        for num, pa in enumerate(self.panels):
            size = min(pa.winfo_width(), pa.winfo_height())
            pa.config(width=size, height=size)
            self.load_panel_image(pa, num)
            # Draw axes after loading the image
            # if num == 0:
                # self.draw_axes_center(pa, "white", "white")
            if num == 1:
                self.draw_axes_value_change(pa, "magenta", "yellow", self.Y, self.X)
            elif num == 2:
                self.draw_axes_value_change(pa, "blue", "magenta", self.X, self.Z_for_axis)
            elif num == 3:
                self.draw_axes_value_change(pa, "blue", "yellow", self.Y, self.Z_for_axis)

    def draw_axes_center(self, panel, x_color, y_color):
        panel.canvas.delete("axes")  # Clear previous axes
        width = panel.canvas.winfo_width()
        height = panel.canvas.winfo_height()
        panel.canvas.create_line(0, height // 2, width, height // 2, fill=x_color, tags="axes")  # x-axis
        panel.canvas.create_line(width // 2, 0, width // 2, height, fill=y_color, tags="axes")  # y-axis

    def draw_axes_value_change(self, panel, x_color, y_color, x_axis, y_axis):
        panel.canvas.delete("axes")  # Clear previous axes
        width = panel.canvas.winfo_width()
        height = panel.canvas.winfo_height()
        width_ratio = 512 / width
        height_ratio = 512 / height
        if y_axis == self.Z_for_axis:  # start the axis from the bottom
            panel.canvas.create_line(0, (height - (y_axis / height_ratio)), width, (height - (y_axis / height_ratio)), fill=x_color, tags="axes")  # x-axis
            panel.canvas.create_line(x_axis / width_ratio, 0, x_axis / width_ratio, height, fill=y_color, tags="axes")  # y-axis
        else:
            panel.canvas.create_line(0, y_axis / height_ratio, width, y_axis / height_ratio, fill=x_color, tags="axes")  # x-axis
            panel.canvas.create_line(x_axis / width_ratio, 0, x_axis / width_ratio, height, fill=y_color, tags="axes")  # y-axis
    
    def toggle_sidebar(self):
        if self.sidebar.winfo_viewable():
            self.sidebar.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y")

    def show_file_menu(self):
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="DICOM Folder", command=self.input_button_click)
        menu.add_command(label="Coordinate Data")
        menu.add_command(label="Puncture Planned Coordinate Data", command=self.input_plan_coor_data)
        menu.add_command(label="Start Point End Point Data")
        menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())

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

    def load_panel_image(self, pa, num):
        if self.IsSelectedItem == 0:
            return
        try:
            if num == 1:  # Axial view XY
                image_2d = self.volume3d[:, :, self.Z]
            elif num == 2:  # Sagittal view YZ
                image_2d = np.flipud(np.rot90(self.volume3d[:, self.Y, :]))
            elif num == 3:  # Coronal view XZ
                image_2d = np.flipud(np.rot90(self.volume3d[self.X, :, :]))
            else:
                image_2d = np.zeros((512, 512), dtype=np.int16)  # Placeholder for the 3D view
        except IndexError:
            image_2d = np.zeros((512, 512), dtype=np.int16)  # Set the panel to black screen in case of error

        self.update_panel_image(pa, image_2d)
        self.draw_needle_plan()

    def update_panel_image(self, panel, image_data):
        image = self.make_2d_image(image_data) if image_data is not None else None
        photo = ImageTk.PhotoImage(image=image) if image_data is not None else None
        panel.canvas.delete("axes")  # Clear previous images and axes
        panel.canvas.delete("images")

        # Center the image
        if photo:
            canvas_width = panel.canvas.winfo_width()
            canvas_height = panel.canvas.winfo_height()
            image_width = photo.width()
            image_height = photo.height()
            x = (canvas_width - image_width) // 2
            y = (canvas_height - image_height) // 2
            panel.canvas.create_image(x, y, image=photo, anchor='nw')
            panel.canvas.image = photo
        # Redraw axes with the correct colors
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

        self.visualize_vispy(self.volume3d)  # Use Vispy to visualize the image in panel1

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
        pass  # Implement zoom functionality
        
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
        # Open file dialog to select a CSV file
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        with open(file_path, newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                a = float(row[0])
                b = float(row[1])
                c = float(row[2])
                point = Vector3D(a, b, c)

                d = float(row[3])
                e = float(row[4])
                f = float(row[5])
                S = math.sqrt(d * d + e * e + f * f)

                vector = Vector3D(d / S, e / S, f / S)  # Normalized vector
                needle_info = NeedleInfo(point, vector)
                self.needleVector.append(needle_info)
                print(needle_info.point.x, needle_info.point.y, needle_info.point.z)
                print(needle_info.vector.x, needle_info.vector.y, needle_info.vector.z)
        
        self.draw_needle_plan()
    
    def draw_needle_plan(self):
        for needle in self.needleVector:
            for panel, plane in zip([self.panel2, self.panel3, self.panel4], ["xy", "yz", "xz"]):
                if plane == "xy":
                    x0, y0 = needle.point.x, needle.point.y
                    x1, y1 = x0 + needle.vector.x * 100, y0 + needle.vector.y * 100
                elif plane == "yz":
                    x0, y0 = needle.point.y, needle.point.z
                    x1, y1 = x0 + needle.vector.y * 100, y0 + needle.vector.z * 100
                elif plane == "xz":
                    x0, y0 = needle.point.x, needle.point.z
                    x1, y1 = x0 + needle.vector.x * 100, y0 + needle.vector.z * 100
                    print("asdfasd")

                x0 = x0 * (panel.canvas.winfo_width() / 512)
                y0 = y0 * (panel.canvas.winfo_height() / 512)
                x1 = x1 * (panel.canvas.winfo_width() / 512)
                y1 = y1 * (panel.canvas.winfo_height() / 512)

                panel.canvas.create_line(x0, y0, x1, y1, fill="red", width=1, tags="needle")

    def visualize_vispy(self, volume3d):
        canvas = scene.SceneCanvas(keys='interactive', show=True)
        view = canvas.central_widget.add_view()
        
        volume = scene.visuals.Volume(volume3d, parent=view.scene, threshold=0.225)
        
        view.camera = scene.cameras.TurntableCamera(parent=view.scene, fov=60)
        view.camera.set_range()
        
        canvas.native.master = self.panel1
        canvas.native.pack(side=TOP, fill=BOTH, expand=1)

if __name__ == '__main__':
    root = Tk()
    app = MainPage(root)
    root.mainloop()
