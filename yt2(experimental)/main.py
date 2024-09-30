import cv2
from ultralytics import YOLO
import numpy as np
import cvzone
from sort import Sort
from tracker import VehicleTracker  # Tracker class that you'll define in tracker.py
from calibrate import get_mask, get_limits  # Mask and line calibration from calibrate.py

# Load YOLO model
model = YOLO("yolov8l.pt")

# Initialize video capture
cap = cv2.VideoCapture("/home/adityaa/Desktop/Smart India Hackathon/video samples/highway.mp4")

# Get mask and line limits for counting from calibrate.py
mask = get_mask("/home/adityaa/Desktop/Smart India Hackathon/yt2(experimental)/mask.png")  # Load mask from file or dynamically generate
limits = get_limits()  # Predefined counting line (you can make this dynamic)

# Initialize the vehicle tracker from tracker.py
vehicle_tracker = VehicleTracker(limits)

while True:
    success, img = cap.read()
    if not success:
        break
    
    # Apply mask to focus on region of interest
    imgRegion = cv2.bitwise_and(img, mask)

    # Run object detection
    results = model(imgRegion, stream=True)
    
    detections = vehicle_tracker.get_detections(results)  # Get detections from tracker

    # Update tracker and get counting results
    img, totalCount = vehicle_tracker.update_tracker(img, detections)
    
    # Show the image with tracked vehicles and count
    cv2.putText(img, f"Count: {totalCount}", (50, 50), cv2.FONT_HERSHEY_PLAIN, 5, (0, 255, 0), 8)
    cv2.imshow("Image", img)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
