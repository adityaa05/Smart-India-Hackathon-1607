import cv2

def main():
    video_source = '/home/adityaa/Desktop/Smart India Hackathon/150642759-busy-traffic-hours-bangalore-i.mp4'  # Ensure this path is correct
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Frame width: {width}, Frame height: {height}")

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # For MP4
    output_file = 'output.mp4'
    out = cv2.VideoWriter(output_file, fourcc, 20.0, (width, height))

    if not out.isOpened():
        print("Error: Could not open video writer.")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("No frame read or end of video.")
            break

        out.write(frame)

    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
