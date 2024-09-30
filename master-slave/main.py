import cv2
import numpy as np
from ultralytics import YOLO
from tracker import EuclideanDistTracker
import threading
import time
import socket
import json

# SlaveClient class (embedded connection logic)
class SlaveClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False

    def connect(self):
        try:
            self.sock.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to master server at {self.host}:{self.port}")
        except Exception as e:
            print(f"Failed to connect to master server: {e}")

    def send_vehicle_count(self, lane, count):
        if not self.connected:
            print("Not connected to master server")
            return
        message = json.dumps({'lane': lane, 'count': count})
        try:
            self.sock.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"Failed to send data to master server: {e}")
            self.connected = False

    def close(self):
        self.sock.close()

# Load the YOLOv8 model
model = YOLO('yolov8x.pt')

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
cap = cv2.VideoCapture("/home/adityaa/Desktop/Smart India Hackathon/video samples/highway.mp4")

# Initialize counters and tracking data
vehicle_count = 0
crossed_vehicles = set()  # To store IDs of vehicles that have crossed the line

# Initialize SlaveClient
client = SlaveClient(host='0.0.0.0', port=5000)  # Replace with your master server's IP and port
client.connect()

def send_vehicle_count():
    global vehicle_count
    while True:
        if client.connected:
            client.send_vehicle_count("North", vehicle_count)  # Replace "North" with the actual lane
        else:
            print("Attempting to reconnect...")
            client.connect()
        time.sleep(5)  # Send updates every 5 seconds

# Start a thread to send vehicle count data
send_thread = threading.Thread(target=send_vehicle_count)
send_thread.daemon = True
send_thread.start()

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

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Object detection
        results = model(frame, conf=0.5)  # Adjust confidence threshold if needed
        detections = []
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            scores = result.boxes.conf.cpu().numpy()
            for box, score in zip(boxes, scores):
                x1, y1, x2, y2 = map(int, box)
                w, h = x2 - x1, y2 - y1
                if w * h > 500:  # Adjust this threshold as needed
                    detections.append([x1, y1, w, h])

        # Update tracker with detections
        boxes_ids = tracker.update(detections)

        # Draw the results and detect line crossings
        for box_id in boxes_ids:
            x, y, w, h, id = box_id
            cv2.putText(frame, str(id), (x, y - 15), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            
            # Check if the vehicle crosses the line segment
            if line_start and line_end and id not in crossed_vehicles:
                if is_crossing_line([x, y, w, h], line_start, line_end):
                    vehicle_count += 1
                    crossed_vehicles.add(id)

        # Draw the counting line on the full frame
        if line_start and line_end:
            cv2.line(frame, line_start, line_end, (0, 0, 255), 3)

        # Display the results
        cv2.imshow("Frame", frame)
        
        # Print vehicle count
        print(f"Vehicle Count: {vehicle_count}")

        key = cv2.waitKey(30)
        if key == 27:  # Press ESC to exit
            break

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    cap.release()
    cv2.destroyAllWindows()
    client.close()
    print("Cleaned up and exited")