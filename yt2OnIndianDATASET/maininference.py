import cv2
import numpy as np
from ultralytics import YOLO
from tracker import EuclideanDistTracker
import torch
from torchvision.ops import nms

# Check CUDA availability
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"CUDA is {'available' if torch.cuda.is_available() else 'not available'}. GPU acceleration is {'enabled' if torch.cuda.is_available() else 'not enabled'}.")

# Load YOLOv8 models
pretrained_model = YOLO('yolov8x.pt')  # Pre-trained YOLOv8x model
custom_model = YOLO('/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/runs/detect/train7/weights/best.pt')  # Custom-trained YOLOv8 model

pretrained_model.model.to(device)
custom_model.model.to(device)

# Create tracker object
tracker = EuclideanDistTracker()

# Load line positions
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
crossed_vehicles = set()

def is_crossing_line(box, line_start, line_end):
    x, y, w, h = box
    cx, cy = (x + x + w) // 2, (y + y + h) // 2
    line_dx, line_dy = line_end[0] - line_start[0], line_end[1] - line_start[1]
    line_mag = np.sqrt(line_dx ** 2 + line_dy ** 2)
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

    detections = []

    # Pre-trained model detection
    pretrained_results = pretrained_model(frame)
    for result in pretrained_results:
        boxes = result.boxes.xyxy.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()
        for box, score in zip(boxes, scores):
            if score > 0.3:  # Confidence threshold
                x1, y1, x2, y2 = map(int, box)
                w, h = x2 - x1, y2 - y1
                detections.append([x1, y1, w, h, score])

    # Custom model detection
    custom_results = custom_model(frame)
    for result in custom_results:
        boxes = result.boxes.xyxy.cpu().numpy()
        scores = result.boxes.conf.cpu().numpy()
        for box, score in zip(boxes, scores):
            if score > 0.3:  # Confidence threshold
                x1, y1, x2, y2 = map(int, box)
                w, h = x2 - x1, y2 - y1
                detections.append([x1, y1, w, h, score])

    # Debug: Print detections to verify structure
    print("Detections:", detections)

    # Apply NMS to reduce overlapping boxes
    if detections:
        boxes = np.array([det[:4] for det in detections])
        scores = np.array([det[4] for det in detections])
        boxes = torch.tensor(boxes, dtype=torch.float32)
        scores = torch.tensor(scores, dtype=torch.float32)
        keep = nms(boxes, scores, iou_threshold=0.4)  # Adjust IoU threshold as needed
        detections = [list(boxes[i].numpy()) + [scores[i].item()] for i in keep]

    # Update tracker with detections
    boxes_ids = tracker.update([det[:4] for det in detections])  # Pass only x, y, w, h

    # Draw the results and detect line crossings
    for box_id in boxes_ids:
        x, y, w, h, id = box_id
        x, y, w, h = map(int, [x, y, w, h])  # Ensure coordinates are integers
        id = int(id)  # Ensure ID is an integer

        # Ensure text position is correct
        text_position = (x, y - 15)
        if text_position[0] < 0:
            text_position = (0, text_position[1])
        if text_position[1] < 0:
            text_position = (text_position[0], 0)

        cv2.putText(frame, str(id), text_position, cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)

        if line_start and line_end and id not in crossed_vehicles:
            if is_crossing_line([x, y, w, h], line_start, line_end):
                vehicle_count += 1
                crossed_vehicles.add(id)

    if line_start and line_end:
        cv2.line(frame, line_start, line_end, (0, 0, 255), 3)

    cv2.imshow("Frame", frame)
    print(f"Vehicle Count: {vehicle_count}")

    key = cv2.waitKey(30)
    if key == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()
