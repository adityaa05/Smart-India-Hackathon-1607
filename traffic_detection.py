import cv2
import numpy as np
import tkinter as tk
from tkinter import Label, Frame
from PIL import Image, ImageTk
import threading

# Define paths to the YOLO files
weights_path = '/home/adityaa/Desktop/Smart India Hackathon/yolov3.weights'  # Adjust path if needed
config_path = '/home/adityaa/Desktop/Smart India Hackathon/yolov3.cfg'       # Adjust path if needed

# Load YOLO
net = cv2.dnn.readNet(weights_path, config_path)
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Create the main window
root = tk.Tk()
root.title("Traffic Detection")

# Create a frame for the video feed
video_frame = Frame(root)
video_frame.pack()

# Create a label to display the video feed
video_label = Label(video_frame)
video_label.pack()

# Create a label to display the count of detected cars
count_label = Label(root, text="Number of cars detected: 0", font=("Helvetica", 16))
count_label.pack()

# Open video capture
cap = cv2.VideoCapture('/home/adityaa/Desktop/Smart India Hackathon/vecteezy_landscape-view-with-street-and-traffic-of-cars-on-asphalt_14394048.mp4')  # Adjust path if needed

# Set video resolution and frame rate
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Further reduced width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 180) # Further reduced height
fps = 5  # Further reduced frame rate
frame_interval = int(1000 / fps)

# Shared variables
frame = None
lock = threading.Lock()

def capture_video():
    global frame
    while True:
        ret, captured_frame = cap.read()
        if not ret:
            cap.release()
            break
        with lock:
            frame = cv2.resize(captured_frame, (320, 180))  # Resize frame for faster processing

def process_frame():
    global frame
    while True:
        with lock:
            if frame is None:
                continue

            # Detecting objects
            blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
            net.setInput(blob)
            outs = net.forward(output_layers)

            class_ids = []
            confidences = []
            boxes = []

            for out in outs:
                for detection in out:
                    for obj in detection:
                        obj = obj.flatten()
                        scores = obj[5:]
                        if scores.size == 0:
                            continue
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.5 and class_id == 2:  # Class ID 2 is for 'car' in YOLOv3
                            center_x = int(obj[0] * frame.shape[1])
                            center_y = int(obj[1] * frame.shape[0])
                            w = int(obj[2] * frame.shape[1])
                            h = int(obj[3] * frame.shape[0])
                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)

                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))

            # Apply non-max suppression
            indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

            # Debug: Print number of detections and bounding boxes
            if indices is not None:
                indices = indices.flatten() if isinstance(indices, np.ndarray) else np.array(indices).flatten()
                print(f"Detected {len(indices)} cars")
                if len(indices) > 0:
                    for i in indices:
                        print(f"Box: {boxes[i]}")

                # Draw bounding boxes and count cars
                car_count = len(indices) if len(indices) > 0 else 0
                for i in indices:
                    box = boxes[i]
                    x, y, w, h = box
                    color = (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            else:
                car_count = 0

            # Update car count label
            count_label.config(text=f"Number of cars detected: {car_count}")

            # Convert frame to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            frame_tk = ImageTk.PhotoImage(frame_pil)

            # Update video label
            video_label.config(image=frame_tk)
            video_label.image = frame_tk

        # Sleep for a short time to prevent excessive CPU usage
        cv2.waitKey(frame_interval)

# Start video capture and processing threads
capture_thread = threading.Thread(target=capture_video, daemon=True)
capture_thread.start()

process_thread = threading.Thread(target=process_frame, daemon=True)
process_thread.start()

# Start the Tkinter event loop
root.mainloop()
