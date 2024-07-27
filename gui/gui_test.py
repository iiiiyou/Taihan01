# Python program to open the 
# camera in Tkinter 
# Import the libraries, 
# tkinter, cv2, Image and ImageTk 
  
from tkinter import *
import tkinter as tk 
import cv2 
from PIL import Image, ImageTk 
import traceback
import sys
  
# Define a video capture object 
# vid = cv2.VideoCapture(0) 
vid = cv2.VideoCapture("C:\\source\\mp4\\deform_spot__output_02.mp4") 
  
# Declare the width and height in variables 
width, height = 800, 600
  
######  tkinter  start ######
# Google search: Tkinter geometry site:www.geeksforgeeks.org
# https://076923.github.io/posts/Python-tkinter-12/
# Create a Tkinter window
cam_on = False
cam_count = 0
root = tk.Tk()
root.title("Detection Display")

# creating fixed geometry of the 
# tkinter window with dimensions 150x200
root.geometry("1300x700+600+0")

# Create a label to display the video frames
label = tk.Label(root)
label.pack()
  
# Create a label and display it on app 
label_widget = Label(root) 
# label_widget.pack() 
label_widget.place(x=650, y=47)

# Create a label and display it on app 
label_widget2 = Label(root) 
# label_widget.pack() 
label_widget2.place(x=3, y=47)

######  tkinter  end   ######
  
#count
def count_fire(detected_a):
    if cam_on:
        global cam_count
        if cam_count >= 50:
            for i in range(9):
                # Capture the video frame by frame 
                _, frame = vid.read() 
            
                # Convert image from one color space to other 
                opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA) 
                imS = cv2.resize(opencv_image, (640, 640))

                ######  tkinter  start ######
                # Capture the latest frame and transform to image 
                image2 = Image.fromarray(imS) 
            
                # Convert captured image to photoimage 
                photo2 = ImageTk.PhotoImage(image=image2) 
            
                # Displaying photoimage in the label 
                label_widget2.photo_image = photo2 
            
                # Configure image in the label 
                label_widget2.configure(image=photo2) 
            
                ######  tkinter  end   ######
            cam_count = 0
            
def open_camera():   
    if cam_on:
        global cam_count
        cam_count = cam_count + 1
        # Capture the video frame by frame 
        _, frame = vid.read() 
    
        # Convert image from one color space to other 
        opencv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA) 
        imS = cv2.resize(opencv_image, (640, 640))
    
        ######  tkinter  start ######
        # Capture the latest frame and transform to image 
        image = Image.fromarray(imS) 
    
        # Convert captured image to photoimage 
        photo = ImageTk.PhotoImage(image=image) 
    
        # Displaying photoimage in the label 
        label_widget.photo_image = photo 
    
        # Configure image in the label 
        label_widget.configure(image=photo)

        count_fire(cam_count)
        
        # Repeat the same process after every 10 milliseconds 
        label_widget.after(10, open_camera) 
        ######  tkinter  end   ######
  
def start_cam():
    global cam_on
    # stop_cam()
    cam_on = True
    open_camera()

def stop_cam():
    global cam_on
    # modbus.write_detected([1,0,0], client)
    print("Sent modbus [1,0,0]")
    cam_on = False


######  tkinter  start   ######

# Create a button to open the camera in GUI app 
btn_open = Button(root, text="Start Camera", command=start_cam) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=2, y=2)

# Create a button to close the camera in GUI app 
btn_stop = Button(root, text="Stop Camera", command=stop_cam) 
# btn_open.grid(row=0,column=0) 
# btn_close.pack()
btn_stop.place(x=92, y=2)

# Create a button to close the camera in GUI app 
btn_close = Button(root, text="Close Program", command=root.destroy) 
# btn_open.grid(row=0,column=0) 
# btn_close.pack()
btn_close.place(x=182, y=2)

# Auto start
start_cam()
# Create an infinite loop for displaying app on screen 
root.mainloop() 

# Release resources
try: 
    # cap.release()
    # cv2.destroyAllWindows()
    print("Camera is released")
except Exception as e:
    print(f"Error opening webcam: {e}")
    traceback.print_exc(file=sys.stdout)
finally:
    cv2.destroyAllWindows()
    # modbus.write_detected([1,0,0], client)
    print("Sent modbus [1,0,0]")
    print('fin')
######  tkinter  start   ######