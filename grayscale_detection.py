import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO

# Load the YOLOv8x model for maximum accuracy
model = YOLO('yolov8x.pt')

def detect_vehicles(image_path, output_path='output.jpg', conf_threshold=0.4, imgsz=1280, augment=True):
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image at {image_path} could not be loaded.")
    
    # Perform inference with the YOLOv8 model
    results = model.predict(image, conf=conf_threshold, iou=0.4, imgsz=imgsz, augment=augment)
    
    # Vehicle classes: 2: Car, 3: Motorcycle, 5: Bus, 7: Truck (COCO dataset classes)
    vehicle_classes = [2, 3, 5, 7]  
    
    vehicle_count = 0
    annotated_frame = results[0].plot()  # Annotate detections on the image
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls in vehicle_classes:
                vehicle_count += 1
    
    # Save annotated image
    cv2.imwrite(output_path, annotated_frame)
    
    print(f"Detected {vehicle_count} vehicles.")
    print(f"Annotated image saved to {output_path}.")

    # Display the result for debugging
    display_image(output_path)

def display_image(image_path):
    # Function to display image in Jupyter Notebook or save for external viewing
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(12, 8))
    plt.imshow(image)
    plt.axis('off')
    plt.show()

if __name__ == "__main__":
    # Example usage
    image_path = '/home/adityaa/Desktop/Smart India Hackathon/sample-vehicles-imgs/dense traffic.jpeg'  # Update with your image path
    output_path = 'detected_vehicles_yolov8.jpg'
    
    # Detect vehicles in the image
    detect_vehicles(image_path, output_path, conf_threshold=0.4, imgsz=1280, augment=True)
