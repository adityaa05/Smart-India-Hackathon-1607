import cv2
from ultralytics import YOLO
import time
import matplotlib.pyplot as plt

def detect_vehicles(frame, model):
    results = model(frame)  # Perform detection

    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cls = int(box.cls[0].item())
            if cls in result.names:
                label = result.names[cls]
                detections.append((label, x1, y1, x2, y2))
            else:
                print(f"Class ID {cls} not in names")  # Debugging line

    return detections

def analyze_traffic_density(vehicle_counts, window_size=10):
    if len(vehicle_counts) < window_size:       
        return "Not enough data"

    avg_count = sum(vehicle_counts[-window_size:]) / window_size
    if avg_count > 10:  # Adjust threshold as needed
        return "Increasing"
    else:
        return "Normal"

def update_status_plot(ax, status):
    ax.clear()
    ax.text(0.5, 0.5, f"Traffic Status: {status}", fontsize=12, ha='center')
    ax.set_xticks([])
    ax.set_yticks([])
    plt.draw()
    plt.pause(0.1)

def main():
    video_source = '/home/adityaa/Desktop/Smart India Hackathon/traffic_Stock.mp4'
    process_interval = 5
    resize_dim = (640, 360)

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"Error: Could not open video source.")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    model = YOLO('yolov8s.pt')  # Load a lighter model

    frame_count = 0
    vehicle_counts = []

    # Create a figure for real-time traffic status
    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots()
    plt.show()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % process_interval == 0:
            small_frame = cv2.resize(frame, resize_dim)
            detections = detect_vehicles(small_frame, model)

            # Count vehicles
            count = sum(1 for label, _, _, _, _ in detections if label in ['car', 'bus', 'motorcycle', 'truck'])
            vehicle_counts.append(count)

            for label, x1, y1, x2, y2 in detections:
                x1, y1 = int(x1 * (frame_width / resize_dim[0])), int(y1 * (frame_height / resize_dim[1]))
                x2, y2 = int(x2 * (frame_width / resize_dim[0])), int(y2 * (frame_height / resize_dim[1]))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Analyze traffic density
            traffic_status = analyze_traffic_density(vehicle_counts)
            
            # Update the status plot
            update_status_plot(ax, traffic_status)

        cv2.imshow('Real-time Vehicle Detection', frame)
        time.sleep(0.1)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    plt.close(fig)

if __name__ == "__main__":
    main()
