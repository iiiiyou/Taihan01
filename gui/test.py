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
import os
import sys
sys.path.append('C:/source')
import util.format_date_time as date
import SQL.insert_sqllite_start as start
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *
import time

# Load the YOLOv8 model#
model = YOLO('C:/source/models/taihanfiber_2-1_best.pt')

# Define a class mapping dictionary
class_mapping = {
    1: 'Detect', # The key is the class id, you may need to adjust according to your model
    # Add more mappings as needed
}

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

# Make folders if not exsist #
def makedirs(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print("Error: Failed to create the directory.")
# Make folder end #


######  Get m53, m54 Start   ######
global m53, m54
m53, m54 = False, False
m53m, m54m = m53, m54
getm = 0
# def get_m():
#     #############################
#     global getm, m53, m54
#     getm = getm + 1
#     if getm <= 200:
#         m53, m54 = False, False
#         print(i, ": 컴퓨터 키고 변화 Start 버튼 실행 안함")
#     if getm > 200 and getm <= 300:
#         m53, m54 = True, False
#         print(i, ": 컴퓨터 키고 변화 Start 버튼 처음 실행 함")
#     if getm > 300 and getm <= 400:
#         m53, m54 = False, True
#         print(i, ": 컴퓨터 키고 변화 Start 버튼 두번째 실행 함")
#     if getm > 400 and getm <= 500:
#         m53, m54 = True, False
#         print(i, ": 컴퓨터 키고 변화 Start 버튼 세번째 실행 함")
#     if getm > 500:
#         getm = 0
######  Get m53, m54 Start   ######

client = ModbusTcpClient('192.168.0.20' ,502)
######  Start button status check start   ######
def check_start():
    global m53, m54, m53m, m54m
    result_m53 = client.read_coils(0x53)
    result_m54 = client.read_coils(0x54)
    m53, m54 = result_m53.bits[0], result_m54.bits[0]

    # get_m()

    # 컴퓨터 키고, 광통신 start 버튼 안눌렀을때 -> m53, M54 = False, False
    # 광통신 start 버튼 처음 누름              -> m53, M54 = True, False
    # 광통신 start 버튼 두번째 누름            -> m53, M54 = False, True

    # 컴퓨터 부팅 후 물리적 Start 버튼이 아직 안눌린 상태이면
    if m53 == False and m54 == False:
        if client.connected:
            result_m53 = client.read_coils(0x53)
            result_m54 = client.read_coils(0x54)
            m53, m54 = result_m53.bits[0], result_m54.bits[0]
        m53m, m54m = m53, m54
        print("   ", i," :화면 전송만 실행")
        print(" m53: " + str(m53) + " m54: " + str(m54) + " m53m: " + str(m53m) + " m54m: " + str(m54m))
        show_camera()

    # 방금 Start 버튼이 눌렸나?
    elif not((m53m == m53) & (m54m == m54)):
        # 면적 DB 보관할 폴더 있는지 확인 후 없으면 생성
        path='C:/Users/user01/Desktop/areaDB'+date.format_date()+'/'
        makedirs(path)

        # 제품번호 material_number 가져오기
        result_n0_1_2  = client.read_holding_registers(0x0000)    # D0  0x0000 제품번호
        result_n0_3_4  = client.read_holding_registers(0x0001)
        result_n0_5    = client.read_holding_registers(0x0002)

        ad=(result_n0_1_2.registers[0])
        bd=(result_n0_3_4.registers[0])
        cd=(result_n0_5.registers[0])
        c1 = (ad & 0x00ff)
        c2 = ad >> 8
        c3 = (bd & 0x00ff)
        c4 = bd >> 8
        c5 = cd
        s_n = chr(c1)+chr(c2)+chr(c3)+chr(c4)+chr(c5)

        # 시작 시간 가져오기
        s_time = int(date.get_date_time())

        #SQL insert (시작시간, 제품번호)
        start.write_sql(s_time,s_n)

        print("   ", i," :10프레임 실행: 밝기 측정, Exposure Time 변경")
        exposure_change()
        print("   ", i," :10프레임 실행: Segmentation area 측정, 기준 넓이로 지정")
        mask_area_base_set()
        time.sleep(5)
        print("   ", i," :Detact 실행(Start 버튼 누른 후)")
        detect_camera()
        print()
        m53m, m54m = m53, m54
    # Start 버튼 눌른 후 다음 Start 버튼 누르기 전인가?
    else:
        print("   ", i," :Detact 실행")
        detect_camera()
        print()

######  Start button status check end   ######

def exposure_change():
    grabResults, cams_bright_mean = [], []
    for h in range (10):
        h = h + 1
        i = 0
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            if grabResults[i].GrabSucceeded():

                cams_bright_mean.append(np.mean(converter.Convert(grabResults[i]).GetArray()))
                # print(np.mean(cams_bright_mean), cams_bright_mean)

    # Set Camera Exposure Time Start
    if (np.mean(cams_bright_mean) > 70):
        cameras[i].ExposureTimeAbs.SetValue(150)
    elif (np.mean(cams_bright_mean) < 35):
        cameras[i].ExposureTimeAbs.SetValue(300)
    # Set Camera Exposure Time End
    
    print('camera bright:', int(np.mean(cams_bright_mean)), ', len:', len(cams_bright_mean))


mean_masks = []

def mask_area_base_set():
    print('mask_area_base_set')


def show_camera():  
    imgsize, confidence = 640, 0.50
    grabResults = []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []
    masks = []

    if cam_on:
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            if grabResults[i].GrabSucceeded():

                images.append(converter.Convert(grabResults[i]))
                images[i] = images[i].GetArray()
                images[i] = cv2.resize(images[i], (imgsize,imgsize))

                # Visualize the results on the frame
                annotated_imgs.append(cv2.resize(images[i], (330,330)))

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
        label_widgets[0].after(1, check_start)
                ######  tkinter  end   ######

def detect_camera():  
    imgsize, confidence = 640, 0.50
    grabResults = []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []
    masks = []

    if cam_on:
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            if grabResults[i].GrabSucceeded():

                images.append(converter.Convert(grabResults[i]))
                images[i] = images[i].GetArray()
                images[i] = cv2.resize(images[i], (imgsize,imgsize))

                # Run YOLOv8 inference on the frame
                # results1 = model(img1)
                results.append(model.predict(images[i], save=False, imgsz=imgsize, conf=confidence))

                # Replace class names with custom labels in the results
                for result in results[i]:
                    for cls_id, custom_label in class_mapping.items():
                        if cls_id in result.names: # check if the class id is in the results
                            result.names[cls_id] = custom_label # replace the class name with the custom label

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
                
                #### mask area start ####
                # Detect가 되고, Detect 의 Class가 0 ("cable") 이면 Mask area 저장
                if not(results[i][0].masks==None) and (int(results[i][0].boxes.cls[0]) == 0):
                    # Segmentation
                    data = results[i][0].masks.data      # masks, (N, H, W)

                    # generate mask
                    mask = data[0]  # torch.unique(mask) = [0., 1.]
                    # Convert the tensor to a NumPy array
                    mask = mask.cpu().numpy()*255 # np.unique(mask) = [0, 255]
                    mask_count = np.count_nonzero(mask == 0)
                    masks.append(mask_count)
                #### mask area end ####

        if len(mean_masks) >= 20:
            mean_masks.pop(0)

        # Mask Area에 값이 있으면 mean_masks에 append
        if len(masks) > 0:
            mean_masks.append([date.get_time_in_all(), int(np.mean(masks))])

        # 면적이상 이벤트 코드 시작 #
            # 불량 감지 코드 추가
            # 외경 측정 코드 추가
        # 면적이상 이벤트 코드 끝 #
        
        # Repeat the same process after every 10 milliseconds
        label_widgets[0].after(1, check_start)

                ######  tkinter  end   ######
  
def start_cam():
    global cam_on
    # stop_cam()
    cam_on = True
    # open_camera()
    check_start()

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
  