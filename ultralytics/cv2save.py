import cv2
import ultralytics.format_date_time as date


# Create a VideoCapture object to capture the video stream
cap = cv2.VideoCapture(0)

# Check if the camera is opened correctly
if not cap.isOpened():
    print("Error opening video capture")
    exit()

# Set the frame rate
# cap.set(cv2.CAP_PROP_FPS, 20)

# Create a window to display the frames
cv2.namedWindow('Webcam', cv2.WINDOW_NORMAL)

ret, frame = cap.read()
cv2.imshow('Webcam', frame)  

cv2.imwrite(date.get_time_in_mmddss()+'.jpg', frame)

cap.release()

# Close all windows
cv2.destroyAllWindows()