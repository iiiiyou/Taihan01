# Python program to open the 
# camera in Tkinter 
# Import the libraries, 
# tkinter, cv2, Image and ImageTk 
  
from tkinter import *
import tkinter as tk 
from pypylon import pylon
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image, ImageTk 
import traceback
import sys
sys.path.append('C:/source')


# Load the YOLOv8 model#
model = YOLO('C:/source/models/taihanfiber_2-1_best.pt')

# conecting to the first available camera
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

# Create pylon Instant Camera
for x in pylon.TlFactory.GetInstance().EnumerateDevices():
    print(x.GetSerialNumber())
    if x.GetSerialNumber() == "24985755":   # Upside
        print (x.GetIpAddress())
        camera1 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))
    elif x.GetSerialNumber() == "25002690": # Right
        print (x.GetIpAddress())
        camera2 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))
    elif x.GetSerialNumber() == "25002686": # Left
        print (x.GetIpAddress())
        camera3 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))

# Grabing Continusely (video) with minimal delay
camera1.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
camera2.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 
camera3.StartGrabbing(pylon.GrabStrategy_LatestImageOnly) 

# Change ExposureTime
# d = camera1.ExposureTimeAbs.Value
# camera1.ExposureTimeAbs.Value = 300
camera1.ExposureTimeAbs.SetValue(300)
camera2.ExposureTimeAbs.SetValue(300)
camera3.ExposureTimeAbs.SetValue(300)

converter = pylon.ImageFormatConverter()

# converting to opencv bgr format
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned


# Define a video capture object 
# vid = cv2.VideoCapture(0) 
vid = cv2.VideoCapture("C:/source/mp4/deform_spot__output_02.mp4") 

# IPS screen (10.1 inch HD Capacitive Touchscreen with HD vision)
# Resolution: 1280*800  
# Declare the width and height in variables 
width, height = 1000, 600

  
######  tkinter  start ######
# Google search: Tkinter geometry site:www.geeksforgeeks.org
# https://076923.github.io/posts/Python-tkinter-12/
# Create a Tkinter window
cam_on = False
cam_count = 0
root = tk.Tk()
root.title("Detection Display")

# creating fixed geometry of the 
# tkinter window with dimensions 1300x700
root.geometry("1000x600+100+0")

# Create a label to display the video frames
label = tk.Label(root)
label.pack()
  
# Create a label and display it on app 
label_widget1 = Label(root) 
# label_widget.pack() 
label_widget1.place(x=1, y=47)

# Create a label and display it on app 
label_widget2 = Label(root) 
# label_widget.pack() 
label_widget2.place(x=334, y=47)

# Create a label and display it on app 
label_widget3 = Label(root) 
# label_widget.pack() 
label_widget3.place(x=667, y=47)

######  tkinter  end   ######
  
def open_camera():   
    if cam_on:
        grabResult1 = camera1.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        grabResult2 = camera2.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        grabResult3 = camera3.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        imgsize, confidence = 640, 0.50
        if grabResult1.GrabSucceeded() and grabResult2.GrabSucceeded() and grabResult3.GrabSucceeded():
        # Access the image data

            grabResult1_mean = np.mean(converter.Convert(grabResult1).GetArray())
            print(grabResult1_mean)
            if (grabResult1_mean > 70):
                camera1.ExposureTimeAbs.SetValue(150)
                camera2.ExposureTimeAbs.SetValue(150)
                camera3.ExposureTimeAbs.SetValue(150)

            elif (grabResult1_mean < 35):
                camera1.ExposureTimeAbs.SetValue(300)
                camera2.ExposureTimeAbs.SetValue(300)
                camera3.ExposureTimeAbs.SetValue(300)

            image1 = converter.Convert(grabResult1)
            img1 = image1.GetArray()
            img1r = cv2.resize(img1, (imgsize,imgsize))

            # Run YOLOv8 inference on the frame
            # results1 = model(img1)
            results1 = model.predict(img1r, save=False, imgsz=imgsize, conf=confidence)
            # Visualize the results on the frame
            annotated_img1 = cv2.resize(results1[0].plot(), (330,330))
            
            image2 = converter.Convert(grabResult2)
            img2 = image2.GetArray()
            img2r = cv2.resize(img2, (imgsize,imgsize))

            # Run YOLOv8 inference on the frame
            # results2 = model(img2)
            results2 = model.predict(img2r, save=False, imgsz=imgsize, conf=confidence)
            # Visualize the results on the frame
            annotated_img2 = cv2.resize(results2[0].plot(), (330,330))
            
            image3 = converter.Convert(grabResult3)
            img3 = image3.GetArray()
            img3r = cv2.resize(img3, (imgsize,imgsize))

            # Run YOLOv8 inference on the frame
            # results3 = model(img3)
            results3 = model.predict(img3r, save=False, imgsz=imgsize, conf=confidence)
            # Visualize the results on the frame
            annotated_img3 = cv2.resize(results3[0].plot(), (330,330))

            ######  tkinter  start ######
            # Capture the latest frame and transform to image 
            image1 = Image.fromarray(annotated_img1) 
            image2 = Image.fromarray(annotated_img2) 
            image3 = Image.fromarray(annotated_img3) 
        
            # Convert captured image to photoimage 
            photo1 = ImageTk.PhotoImage(image=image1) 
            photo2 = ImageTk.PhotoImage(image=image2) 
            photo3 = ImageTk.PhotoImage(image=image3) 
        
            # Displaying photoimage in the label 
            label_widget1.photo_image = photo1
            label_widget2.photo_image = photo2
            label_widget3.photo_image = photo3
        
            # Configure image in the label 
            label_widget1.configure(image=photo1)
            label_widget2.configure(image=photo2)
            label_widget3.configure(image=photo3)
            
            # Repeat the same process after every 10 milliseconds 
            label_widget1.after(1, open_camera)
            # label_widget2.after(10, open_camera) 
            # label_widget3.after(10, open_camera)

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