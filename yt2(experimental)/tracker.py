import numpy as np
from sort import Sort
import cvzone
import cv2


class VehicleTracker:
    def __init__(self, limits):
        self.tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)
        self.limits = limits  # The line to count vehicles crossing
        self.totalCount = []  # List to keep track of counted vehicles

    def get_detections(self, results):
        """
        Parse the results from YOLO and extract relevant detections.
        Only keep detections of cars, trucks, buses, and motorbikes with confidence > 0.3.
        """
        detections = np.empty((0, 5))  # Initialize empty detections
        classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck", "boat", ...]
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Get bounding box
                conf = box.conf[0]  # Get confidence score
                cls = int(box.cls[0])  # Get class ID
                currentClass = classNames[cls]
                
                if currentClass in ["car", "truck", "bus", "motorbike"] and conf > 0.3:
                    currentArray = np.array([x1, y1, x2, y2, conf])
                    detections = np.vstack((detections, currentArray))
        
        return detections

    def update_tracker(self, img, detections):
        """
        Update the tracker with new detections and check if vehicles cross the counting line.
        """
        resultsTracker = self.tracker.update(detections)
        
        # Draw the counting line
        cv2.line(img, (self.limits[0], self.limits[1]), (self.limits[2], self.limits[3]), (0, 0, 255), 5)
        
        for result in resultsTracker:
            x1, y1, x2, y2, id = map(int, result)
            w, h = x2 - x1, y2 - y1
            cx, cy = x1 + w // 2, y1 + h // 2

            # Draw rectangle and ID
            cvzone.cornerRect(img, (x1, y1, w, h), l=9, rt=2, colorR=(255, 0, 255))
            cvzone.putTextRect(img, f' {int(id)}', (x1, y1), scale=2, thickness=3, offset=10)

            # Check if vehicle crosses the counting line
            if self.limits[0] < cx < self.limits[2] and self.limits[1] - 15 < cy < self.limits[1] + 15:
                if id not in self.totalCount:
                    self.totalCount.append(id)
                    cv2.line(img, (self.limits[0], self.limits[1]), (self.limits[2], self.limits[3]), (0, 255, 0), 5)

        return img, len(self.totalCount)
