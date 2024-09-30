import os
import numpy as np
import cv2
from ultralytics import YOLO

# Load your custom model
model_path = '/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/runs/detect/train7/weights/best.pt'
model = YOLO(model_path)

# Path to your test images and ground truth labels
test_images_path = '/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/dataset/test/images'
ground_truth_path = '/home/adityaa/Desktop/Smart India Hackathon/yt2OnIndianDATASET/dataset/test/labels'

# Initialize counters for evaluation
total_objects = 0
true_positives = 0
false_positives = 0
false_negatives = 0

def read_ground_truth(image_name):
    label_file = os.path.join(ground_truth_path, image_name.replace('.jpg', '.txt').replace('.png', '.txt'))
    if not os.path.exists(label_file):
        return []
    with open(label_file, 'r') as f:
        lines = f.readlines()
    return [list(map(float, line.strip().split())) for line in lines]

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

# Iterate over all test images
for image_name in os.listdir(test_images_path):
    if image_name.endswith('.jpg') or image_name.endswith('.png'):
        # Load image
        image_path = os.path.join(test_images_path, image_name)
        image = cv2.imread(image_path)

        # Perform inference
        results = model(image)

        # Extract detections
        detections = results[0].boxes.xyxy.cpu().numpy()
        scores = results[0].boxes.conf.cpu().numpy()

        # Read ground truth
        ground_truth_objects = read_ground_truth(image_name)
        total_objects += len(ground_truth_objects)

        matched_gt = set()
        for det in detections:
            det_box = list(map(int, det))
            matched = False
            for idx, gt in enumerate(ground_truth_objects):
                gt_box = [int(gt[1] * image.shape[1]), int(gt[2] * image.shape[0]),
                          int(gt[3] * image.shape[1]), int(gt[4] * image.shape[0])]
                if calculate_iou(det_box, gt_box) > 0.5:
                    matched_gt.add(idx)
                    true_positives += 1
                    matched = True
                    break
            if not matched:
                false_positives += 1

        false_negatives += len(ground_truth_objects) - len(matched_gt)

# Calculate accuracy
precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
print(f"Precision: {precision:.2f}")
print(f"Recall: {recall:.2f}")
print(f"F1 Score: {2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0:.2f}")
