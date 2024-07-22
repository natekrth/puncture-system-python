import csv
import time
import random

def generate_random_values():
    x = int(random.uniform(0, 512))
    y = int(random.uniform(0, 512))
    z = int(random.uniform(0, 166))
    return x, y, z

def write_to_csv(filename):
    # save = 10
    while True:
        x, y, z = generate_random_values()
        # save += 10
        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([x, y, z])
        print(f'Written values: x={x}, y={y}, z={z}')
        time.sleep(5)

if __name__ == "__main__":
    # Create the file and clear any existing content
    filename = 'realtime.csv'
    with open(filename, mode='w', newline='') as file:
        pass

    write_to_csv(filename)
