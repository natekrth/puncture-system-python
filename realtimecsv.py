import csv
import time
import random

def generate_random_values(start_y, end_y, step_y):
    x = 256
    z = 83
    return x, z

def write_to_csv(filename, start_y, end_y, step_y):
    y = start_y
    while y <= end_y:
        x, z = generate_random_values(start_y, end_y, step_y)
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([x, y, z])
        print(f'Written values: x={x}, y={y}, z={z}')
        y += step_y
        time.sleep(5)

if __name__ == "__main__":
    # Create the file and clear any existing content
    filename = 'realtime.csv'
    with open(filename, mode='w', newline='') as file:
        pass

    write_to_csv(filename, start_y=179, end_y=320, step_y=10)
