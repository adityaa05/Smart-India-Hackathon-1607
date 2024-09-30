import cv2

# Open video file
cap = cv2.VideoCapture("/home/adityaa/Downloads/NEWDATASET3GB/annotation/annotation/bus")

# Initialize variables for the interactive line setting
line_start = None
line_end = None
line_thickness = 3
drawing = False

def mouse_callback(event, x, y, flags, param):
    global line_start, line_end, drawing
    if event == cv2.EVENT_LBUTTONDOWN:
        if line_start is None:
            line_start = (x, y)
        else:
            line_end = (x, y)
            drawing = True

# Set up the window and mouse callback function
cv2.namedWindow("Calibration")
cv2.setMouseCallback("Calibration", mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Draw the line if both points are set
    if line_start and line_end:
        cv2.line(frame, line_start, line_end, (0, 0, 255), line_thickness)

    # Display the results
    cv2.imshow("Calibration", frame)

    key = cv2.waitKey(30)
    if key == 27:  # Press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()

# Save the line position
if line_start and line_end:
    with open("line_start_end.txt", "w") as f:
        f.write(f"{line_start[0]},{line_start[1]}\n{line_end[0]},{line_end[1]}")
