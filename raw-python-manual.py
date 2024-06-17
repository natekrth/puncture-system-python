import numpy as np
import pydicom
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def read_raw_file(raw_filename, num_images, rows, cols):
    # Read the raw file containing DICOM images
    with open(raw_filename, 'rb') as f:
        raw_data = np.fromfile(f, dtype=np.uint16)
    
    # Ensure the raw data length matches the expected number of images
    assert len(raw_data) == num_images * rows * cols, "Raw file size does not match expected number of images"
    
    return raw_data

def convert_to_dicom(raw_data, num_images, rows, cols):
    # Split the raw data into individual DICOM images
    dicom_images = []
    for i in range(num_images):
        dicom_image = raw_data[i * rows * cols: (i + 1) * rows * cols].reshape((rows, cols))
        dicom_images.append(dicom_image)
    
    return dicom_images

def show_dicom_images(dicom_images):
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    dicom_plot = ax.imshow(dicom_images[0], cmap='gray')

    ax_slider = plt.axes([0.2, 0.1, 0.65, 0.03])
    slider = Slider(ax_slider, 'Image Index', 0, len(dicom_images) - 1, valinit=0, valstep=1)

    def update(val):
        index = int(slider.val)
        dicom_plot.set_data(dicom_images[index])
        fig.canvas.draw_idle()

    slider.on_changed(update)
    plt.show()

# Example usage
raw_filename = 'pA.raw'  # Replace with your RAW file containing DICOM images
num_images = 166  # Number of DICOM images in the sequence
rows = 512  # Number of rows in each DICOM image
cols = 512  # Number of columns in each DICOM image

raw_data = read_raw_file(raw_filename, num_images, rows, cols)
dicom_images = convert_to_dicom(raw_data, num_images, rows, cols)
show_dicom_images(dicom_images)
