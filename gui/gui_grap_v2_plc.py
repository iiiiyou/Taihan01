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

tlf = pylon.TlFactory.GetInstance()
devices = tlf.EnumerateDevices()

# list of pylon Device 
print(devices)
cameras = []
for i in range(len(devices)):
    print(devices[i].GetModelName(), devices[i].GetSerialNumber())
    # conecting to the available camera
    cameras.append(pylon.InstantCamera(tlf.CreateDevice(devices[i])))

    # the features of the device are only accessable after Opening the device
    # camera[i].Open()

    # Grabing Continusely (video) with minimal delay
    cameras[i].StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    cameras[i].ExposureTimeAbs.SetValue(300)


converter = pylon.ImageFormatConverter()

# converting to opencv bgr format
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

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

label_widgets = []
# Create a label and display it on app 
label_widgets.append(Label(root))
# label_widget.pack() 
label_widgets[0].place(x=1, y=47)

# Create a label and display it on app 
label_widgets.append(Label(root))
# label_widget.pack() 
label_widgets[1].place(x=334, y=47)

# Create a label and display it on app 
label_widgets.append(Label(root))
# label_widget.pack() 
label_widgets[2].place(x=667, y=47)

######  tkinter  end   ######
  
def open_camera():  
    imgsize, confidence = 640, 0.50
    grabResults, cams_bright_mean = [], []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []
    if cam_on:
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            if grabResults[i].GrabSucceeded():

                # Set Camera Exposure Time
                cams_bright_mean.append(np.mean(converter.Convert(grabResults[i]).GetArray()))
                print(np.mean(cams_bright_mean), cams_bright_mean)
                if (np.mean(cams_bright_mean) > 70):
                    cameras[i].ExposureTimeAbs.SetValue(150)
                elif (np.mean(cams_bright_mean) < 35):
                    cameras[i].ExposureTimeAbs.SetValue(300)

                images.append(converter.Convert(grabResults[i]))
                images[i] = images[i].GetArray()
                images[i] = cv2.resize(images[i], (imgsize,imgsize))

                # Run YOLOv8 inference on the frame
                # results1 = model(img1)
                results.append(model.predict(images[i], save=False, imgsz=imgsize, conf=confidence))
                # Visualize the results on the frame
                annotated_imgs.append(cv2.resize(results[i][0].plot(), (330,330)))

                ######  tkinter  start ######
                # Capture the latest frame and transform to image
                cap_imgs.append(Image.fromarray(annotated_imgs[i]))

                # Convert captured image to photoimage 
                photos.append(ImageTk.PhotoImage(image=cap_imgs[i]))

                # Displaying photoimage in the label 
                label_widgets[i].photo_image = photos[i]
                
                # Configure image in the label 
                label_widgets[i].configure(image=photos[i])

        # Repeat the same process after every 10 milliseconds 
        label_widgets[0].after(1, open_camera)

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
  