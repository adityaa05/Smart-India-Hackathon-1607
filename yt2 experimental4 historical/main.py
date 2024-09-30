import cv2
import numpy as np
import csv
import time
from ultralytics import YOLO
from tracker import EuclideanDistTracker
from queue import Queue
from graph import plot_graph  # Import the graph plotting function

# Load the YOLOv8 model
model = YOLO('yolov8x.pt')  # Use the YOLOv8x model

# Create tracker object
tracker = EuclideanDistTracker()

# Load the saved line positions
try:
    with open("line_start_end.txt", "r") as f:
        line_start = tuple(map(int, f.readline().strip().split(',')))
        line_end = tuple(map(int, f.readline().strip().split(',')))
except FileNotFoundError:
    print("Line position file not found. Run the calibration script first.")
    exit()

# Open video file
cap = cv2.VideoCapture("/home/adityaa/Downloads/NEWDATASET3GB/annotation/annotation/bus")

# Initialize counters and tracking data
vehicle_count = 0
crossed_vehicles = set()  # To store IDs of vehicles that have crossed the line

# Define CSV file path
csv_file = 'vehicle_data.csv'

# Open CSV file in append mode
with open(csv_file, 'a', newline='') as file:
    writer = csv.writer(file)
    # Write header if file is empty
    if file.tell() == 0:
        writer.writerow(['Timestamp', 'Vehicle Count'])

    # Initialize graph data queue
    queue = Queue()
    start_time = time.time()

    def is_crossing_line(box, line_start, line_end):
        x, y, w, h = box
        cx, cy = (x + x + w) // 2, (y + y + h) // 2
        line_dx, line_dy = line_end[0] - line_start[0], line_end[1] - line_start[1]
        line_mag = np.sqrt(line_dx**2 + line_dy**2)
        if line_mag == 0:
            return False
        u = ((cx - line_start[0]) * line_dx + (cy - line_start[1]) * line_dy) / line_mag
        if u < 0 or u > line_mag:
            return False
        intersection = (line_start[0] + u * (line_dx / line_mag), line_start[1] + u * (line_dy / line_mag))
        return np.abs(intersection[1] - cy) < 10  # Adjust this tolerance as needed

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Object detection
        results = model(frame, conf=0.5)
        detections = []

        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
            for box, score in zip(boxes, scores):
                x1, y1, x2, y2 = map(int, box)
                w, h = x2 - x1, y2 - y1
                if w * h > 500:
                    detections.append([x1, y1, w, h])

        # Update tracker with detections
        boxes_ids = tracker.update(detections)

        # Draw the results and detect line crossings
        for box_id in boxes_ids:
            x, y, w, h, id = box_id
            cv2.putText(frame, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

            if line_start and line_end and id not in crossed_vehicles:
                if is_crossing_line([x, y, w, h], line_start, line_end):
                    vehicle_count += 1
                    crossed_vehicles.add(id)

        # Draw the counting line on the full frame
        if line_start and line_end:
            cv2.line(frame, line_start, line_end, (0, 0, 255), 3)

        # Save data to CSV
        elapsed_time = time.time() - start_time
        writer.writerow([elapsed_time, vehicle_count])

        # Update the graph data
        queue.put((elapsed_time, vehicle_count))
        plot_graph(queue)  # Update the graph

        # Display the results
        cv2.imshow("Frame", frame)

        # Print vehicle count
        print(f"Vehicle Count: {vehicle_count}")

        key = cv2.waitKey(30)
        if key == 27:  # Press ESC to exit
            break

cap.release()
cv2.destroyAllWindows()
