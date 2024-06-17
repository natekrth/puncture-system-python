import rawpy
import imageio
import numpy as np
from PIL import Image

def process_raw_file(file_path):
    # Open the raw file
    with rawpy.imread(file_path) as raw:
        # Process the raw file into an RGB image
        rgb_image = raw.postprocess()
        
        # Convert to PIL Image for further processing or saving
        image = Image.fromarray(rgb_image)
        
        return [image]

def save_images(images, output_path_template):
    for i, image in enumerate(images):
        image.save(output_path_template.format(i + 1))

def main():
    # Specify the path to your raw file
    raw_file_path = 'pA.raw'
    output_path_template = 'output_image_{}.jpg'
    
    # Process and save the images
    images = process_raw_file(raw_file_path)
    save_images(images, output_path_template)

if __name__ == "__main__":
    main()
