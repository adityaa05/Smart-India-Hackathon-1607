import os
import numpy as np
import torch
from ultralytics import YOLO

# Check CUDA availability
if torch.cuda.is_available():
    device = 'cuda'
    print("CUDA is available. GPU acceleration is enabled.")
else:
    device = 'cpu'
    print("CUDA is not available. GPU acceleration is not enabled.")

# Clear CUDA cache
torch.cuda.empty_cache()

# Training script
def train_model():
    # Load the YOLOv8 model configuration
    model = YOLO('yolov8n.yaml')  # Use a smaller model to reduce memory usage

    # Train the model
    model.train(
        data='/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/dataset/data.yaml',
        epochs=50,          # Reduce the number of epochs
        imgsz=640,          # Reduce the image size
        batch=16,           # Reduce the batch size
        amp=True,           # Enable Automatic Mixed Precision (AMP)
        save_dir='/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/runs/train/exp'  # Specify the save directory
    )

# Check if trained model exists, if not, train it
model_path = '/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/runs/train/exp/weights/best.pt'
if not os.path.exists(model_path):
    print("Training model...")
    train_model()
else:
    print("Model already trained.")

# Load the YOLOv8 model
model = YOLO(model_path)  # Use the trained model
model.model.to(device)    # Move model to GPU if available

# Rest of your code for inference and tracking follows here...

# Create tracker object
from tracker import EuclideanDistTracker
tracker = EuclideanDistTracker()  # No dist_threshold argument needed

# Load the saved line positions
try:
    with open("line_start_end.txt", "r") as f:
        line_start = tuple(map(int, f.readline().strip().split(',')))
        line_end = tuple(map(int, f.readline().strip().split(',')))
except FileNotFoundError:
    print("Line position file not found. Run the calibration script first.")
    exit()

# Open video file
import cv2
cap = cv2.VideoCapture("/home/adityaa/Desktop/Smart India Hackathon/video samples/highway.mp4")

# Initialize counters and tracking data
vehicle_count = 0
crossed_vehicles = set()  # To store IDs of vehicles that have crossed the line

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
    results = model(frame)  # Inference
    detections = []

    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()  # Move tensor to CPU and convert to NumPy array
        scores = result.boxes.conf.cpu().numpy()  # Move tensor to CPU and convert to NumPy array
        for box, score in zip(boxes, scores):
            x1, y1, x2, y2 = map(int, box)
            w, h = x2 - x1, y2 - y1
            # Append detection if area is significant
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

cap.release()
cv2.destroyAllWindows()
