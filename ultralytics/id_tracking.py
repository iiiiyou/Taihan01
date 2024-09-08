import cv2
from ultralytics import YOLO
import time
previous_id = 0

def is_id_increased(id):
    if id > previous_id:
        return True
    else:
        return False

def format_id(id):
    if id is not None:
        return int(max((id).numpy()))
    else:
        return 0

# Load the YOLOv8 model
model = YOLO("yolov8n.pt")

# Open the video file
cap = cv2.VideoCapture("vehicle-counting.mp4")

# Loop through the video frames
while cap.isOpened():
    # Read a frame from the video
    success, frame = cap.read()

    if success:
        # Run YOLOv8 tracking on the frame, persisting tracks between frames
        results = model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[2,5,7]) # 2:'car', 5:'bus, 7:'truck
        # results = model(frame)

        for result in results:
            # if check_id_increase()
            # id = int(max((result.boxes.id).numpy()))
            id = format_id(result.boxes.id)
            if is_id_increased(id): 
                print('**************************************************')
                print(f'previous_is {previous_id} and detected id is {id}')
                previous_id = id


        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        resized_image = cv2.resize(annotated_frame, (1980, 1080))

        # Display the annotated frame
        cv2.imshow("YOLOv8 Tracking: Cars and Trucks", resized_image)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    else:
        # Break the loop if the end of the video is reached
        break

# Release the video capture object and close the display window
cap.release()
cv2.destroyAllWindows()
