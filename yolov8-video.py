import cv2
from ultralytics import YOLO
import time

def detect_vehicles(frame, model):
    results = model(frame)  # Perform detection

    detections = []
    for result in results:
        for box in result.boxes:
            # Convert tensors to integers
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls = int(box.cls[0].item())  # Ensure class index is an integer
            if cls in result.names:
                label = result.names[cls]  # Retrieve class name
                detections.append((label, x1, y1, x2, y2))
            else:
                print(f"Class ID {cls} not in names")  # Debugging line

    return detections

def main():
    video_source = '/home/adityaa/Desktop/Smart India Hackathon/150642759-busy-traffic-hours-bangalore-i.mp4'
    process_interval = 5  # Process every 5th frame
    resize_dim = (640, 360)  # Resize dimensions

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source.")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    model = YOLO('yolov8s.pt')  # Load a lighter model

    frame_count = 0
    prev_detections = []  # To keep track of previous detections

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % process_interval == 0:
            # Resize frame to speed up processing
            small_frame = cv2.resize(frame, resize_dim)

            # Detect vehicles
            detections = detect_vehicles(small_frame, model)

            # Draw bounding boxes and labels
            for label, x1, y1, x2, y2 in detections:
                # Scale bounding box coordinates back to the original frame size
                x1, y1 = int(x1 * (frame_width / resize_dim[0])), int(y1 * (frame_height / resize_dim[1]))
                x2, y2 = int(x2 * (frame_width / resize_dim[0])), int(y2 * (frame_height / resize_dim[1]))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Optionally, you can keep previous detections to maintain consistency
            prev_detections = detections

        # Display the frame with detections
        cv2.imshow('Real-time Vehicle Detection', frame)

        # Introduce a small delay to reduce processing speed
        time.sleep(0.1)  # Delay in seconds

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
