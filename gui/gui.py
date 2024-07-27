import tkinter as tk 
import cv2 
from PIL import Image, ImageTk 
from ultralytics import YOLO

# Load the YOLOv8 model
model = YOLO("yolov8m.pt")  # Replace with the path to your YOLOv8 model

# Initialize webcam
cap = cv2.VideoCapture(0)

# Create a Tkinter window
root = tk.Tk()
root.title("Detection Display")
root.geometry("640x480")

# Create a label to display the video frames
label = tk.Label(root)
label.pack()
  
# Create a label and display it on app 
label_widget = tk.Label(root) 
label_widget.pack() 
  
# Create a function to open camera and 
# display it in the label_widget on app 
  
def open_camera(): 

    '''
    This function reads frames and make predictions
    '''  
    # Read a frame from the webcam  
    _, frame = cap.read()
      
    # Perform object detection with YOLOv8
    results = model.predict(source=frame)
    # Draw bounding boxes and labels for detected objects
    for result in results:
        try: 
            x1,y1,x2,y2 = result.boxes.xyxy[0]   # box with xyxy format, (N, 4)
            # result.boxes.xywh   # box with xywh format, (N, 4)
            center = int((x1+x2)/2), int((y1+y2)/2)
            cv2.circle(frame, center,8,(0,0,255),8)
            cv2.putText(frame, ' '+result.names, center, cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA, False)
        except:
            print("Not Detected")

    # # Convert image from one color space to other 
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA) 
  
    # Capture the latest frame and transform to image 
    image = Image.fromarray(frame) 
    # Convert captured image to photoimage 
    photo = ImageTk.PhotoImage(image=image) 

    # Displaying photoimage in the label 
    label_widget.photo_image = photo 

    # Configure image in the label 
    label_widget.configure(image=photo) 

    # Repeat the same process after every 10 seconds 
    label_widget.after(10, open_camera) 

# Create a button to open the camera in GUI app 
btn_open = tk.Button(root, text="Open Camera", command=open_camera) 
# btn_open.grid(row=0,column=0) 
btn_open.pack()
  
# Create an infinite loop for displaying app on screen 
root.mainloop() 

# Release resources
cap.release()
cv2.destroyAllWindows()