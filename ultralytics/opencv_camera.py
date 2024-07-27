import cv2

# Initialize the camera
cap = cv2.VideoCapture(0)

# Check if the camera is opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Read frames from the camera
while True:
    ret, frame = cap.read()

    # Check if frame is read successfully
    if not ret:
        print("Error: Could not read frame.")
        break

    # Display the frame
    cv2.imshow("Camera Stream", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close the window
cap.release()
cv2.destroyAllWindows()