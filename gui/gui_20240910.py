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
import SQL.insert_sqllite_detect as detect
import SQL.insert_sqllite_area as areadb
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *
import time
import logging

## 20240908 id Tracking 추가 시작 ##
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
## 20240908 id Tracking 추가 끝 ##

logging.basicConfig(filename='C:/source/test.log', level=logging.ERROR)

# Load the YOLOv8 model#
# model = YOLO('C:/source/models/taihanfiber_4-1_best_anyang.pt')
model = YOLO('C:/source/models/taihanfiber_3-2_best_t.pt')
imgsize, confidence = 640, 0.70
# 케이블 면적 기준 값
cable_area_base = 0

client = ModbusTcpClient('192.168.102.20' ,502)
# # Define a class mapping dictionary
# class_mapping = {
#     1: 'Defect', # The key is the class id, you may need to adjust according to your model
#     # Add more mappings as needed
# }

tlf = pylon.TlFactory.GetInstance()
devices = tlf.EnumerateDevices()

# list of pylon Device 
# print(devices)
cameras = []
for i in range(len(devices)):
    # print(devices[i].GetModelName(), devices[i].GetSerialNumber())
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
win = Tk()
win.title("Detection Display")

# creating fixed geometry of the 
# tkinter window with dimensions 1300x700
win.geometry("1000x540+100+0")

# Create a label to display the video frames
# label = tk.Label(win)
# label.pack()

label_cameras = []

# Camera 0
label_camera1 = Label(win)
label_camera1.place(x=1, y=47)
# img = PhotoImage(file = "C:/source/tkinter/Daum_communication_logo.svg.png", master = win)
# img = img.subsample(3)
# lab_d.config(image = img)
# lab_d.pack()
def show_camera1(camera1):
    label_camera1.config(image = camera1)
# label_camera1.pack()

# Camera 2
label_camera2 = Label(win)
label_camera2.place(x=334, y=47)
def show_camera2(camera2):
    label_camera2.config(image = camera2)
# label_camera2.pack()

# Camera 3
label_camera3 = Label(win)
label_camera3.place(x=667, y=47)
def show_camera3(camera3):
    label_camera3.config(image = camera3)
# label_camera3.pack()

# 케이블 기준 면적 라벨
label_cable1 = Label(win)
label_cable1.config(text = "케이블 기준 면적: ")
label_cable1.place(x=20, y=400)
# label_cable1.pack()

# 케이블 기준 면적 값
value_cable1= Label(win)
value_cable1.config(text = "측정 전", font=("Consolas", 10))
value_cable1.place(x=120, y=400)
def show_area_base(mask_area_base):
    mask_area_base = f"{mask_area_base:,}"
    value_cable1.config(text = mask_area_base)
# value_cable1.pack()

# 현재 케이블 면적 라벨
label_cable2 = Label(win)
label_cable2.config(text = "현재 케이블 면적: ")
label_cable2.place(x=20, y=420)
# label_cable2.pack()

# 현재 케이블 면적 값
value_cable2 = Label(win)
value_cable2.config(text = "측정 전", font=("Consolas", 10))
value_cable2.place(x=120, y=420)
def show_mask_area(current_mask_area):
    # 2024-09-08 면적 비율 추가
    area_ratio = current_mask_area / cable_area_base * 100
    area_ratio = f"{area_ratio:.2f}"
    # area_ratio = str(area_ratio).zfill(6)
    area_ratio = str(area_ratio).rjust(6)
    area_ratio = f"{current_mask_area:,} ({area_ratio} %)"
    value_cable2.config(text = area_ratio)
# value_cable2.pack()

# m01 라벨
label_m01 = Label(win)
label_m01.config(text = "m01_value: ")
label_m01.place(x=20, y=460)
# label_m01.pack()

# m01 값
value_m01 = Label(win)
value_m01.config(text = "측정 전", font=("Consolas", 10))
value_m01.place(x=120, y=460)
def show_m01_value(m01_value):
    value_m01.config(text = m01_value)
# value_m01.pack()

# cur_m53 라벨
label_cur_m53 = Label(win)
label_cur_m53.config(text = "cur_m53_value: ")
label_cur_m53.place(x=20, y=480)
# label_cur_m53.pack()

# cur_m53 값
value_cur_m53 = Label(win)
value_cur_m53.config(text = "측정 전", font=("Consolas", 10))
value_cur_m53.place(x=120, y=480)
def show_cur_m53_value(cur_m53_value):
    value_cur_m53.config(text = cur_m53_value)
# value_cur_m53.pack()

# cur_m54 라벨
label_cur_m54 = Label(win)
label_cur_m54.config(text = "cur_m54_value: ")
label_cur_m54.place(x=20, y=500)
# label_cur_m54.pack()

# cur_m54 값
value_cur_m54 = Label(win)
value_cur_m54.config(text = "측정 전", font=("Consolas", 10))
value_cur_m54.place(x=120, y=500)
def show_cur_m54_value(cur_m54_value):
    value_cur_m54.config(text = cur_m54_value)
# value_cur_m54.pack()

# m04 라벨
label_m04 = Label(win)
label_m04.config(text = "m04_value: ")
label_m04.place(x=20, y=520)
# label_m04.pack()

# m04 값
value_m04 = Label(win)
value_m04.config(text = "측정 전", font=("Consolas", 10))
value_m04.place(x=120, y=520)
def show_m04_value(m04_value):
    value_m04.config(text = m04_value)
# value_m04.pack()

# 2024-09-08 추가
# ===============================================
# 생산 시작 시간 라벨
label_stime = Label(win)
label_stime.config(text = "시작시간: ")
label_stime.place(x=320, y=400)
# label_cable1.pack()

# 생산 시작 시간 값
value_stime= Label(win)
value_stime.config(text = "측정 전", font=("Consolas", 10))
value_stime.place(x=420, y=400)
def show_stime(stime_value):
    value_stime.config(text = stime_value)
# value_stime.pack()

# 제품번호(sn) 라벨
label_sn = Label(win)
label_sn.config(text = "제품번호: ")
label_sn.place(x=320, y=420)
# label_cable1.pack()

# 제품번호(sn) 값
value_sn= Label(win)
value_sn.config(text = "측정 전", font=("Consolas", 10))
value_sn.place(x=420, y=420)
def show_sn(sn_value):
    value_sn.config(text = sn_value)
# value_stime.pack()

# 현재 케이블 생산 meter 라벨
label_meter = Label(win)
label_meter.config(text = "케이블 생산미터: ")
label_meter.place(x=320, y=440)
# label_cable2.pack()

# 현재 케이블 생산 meter 값
value_meter = Label(win)
value_meter.config(text = "측정 전", font=("Consolas", 10))
value_meter.place(x=420, y=440)
def show_meter(meter_value):
    meter_value = f"{meter_value:,} 미터"
    value_meter.config(text = meter_value)
# value_cable2.pack()

# 현재 케이블 생산 feet 라벨
label_feet = Label(win)
label_feet.config(text = "케이블 생산피트: ")
label_feet.place(x=320, y=460)
# label_cable2.pack()

# 현재 케이블 생산 feet 값
value_feet = Label(win)
value_feet.config(text = "측정 전", font=("Consolas", 10))
value_feet.place(x=420, y=460)
def show_feet(feet_value):
    feet_value = f"{feet_value:,.0f} 피트"
    value_feet.config(text = feet_value)
# value_cable2.pack()

# cnt 라벨
label_cnt = Label(win)
label_cnt.config(text = "케이블 생산회전: ")
label_cnt.place(x=320, y=480)
# label_cnt.pack()

# cnt 값
value_cnt = Label(win)
value_cnt.config(text = "측정 전", font=("Consolas", 10))
value_cnt.place(x=420, y=480)
def show_cnt(cnt_value):
    cnt_value = f"{cnt_value:,} 회전"
    value_cnt.config(text = cnt_value)
# value_cnt.pack()


# ===============================================


def start_btn_check():
    try:
        global m01, m04, cur_m53, cur_m54, mem_m53, mem_m54, s_time, count, client
        if not(client.connected):
            client = ModbusTcpClient('192.168.102.20' ,502)
        result_cur_m53 = client.read_coils(0x53)
        result_cur_m54 = client.read_coils(0x54)
        result_m01 = client.read_coils(0x01)
        result_m04 = client.read_coils(0x04)
        # print("type(result_cur_m53.bits[0]): ", type(result_cur_m53.bits[0]))
        # print("result_cur_m53.bits[0]: ", result_cur_m53.bits[0])
        # print("type(result_cur_m54.bits[0]): ", type(result_cur_m54.bits[0]))
        # print("result_cur_m54.bits[0]: ", result_cur_m54.bits[0])
        # print("type(cur_m53): ", type(cur_m53))
        # print("type(cur_m54): ", type(cur_m54))
        cur_m53, cur_m54 = result_cur_m53.bits[0], result_cur_m54.bits[0]
        m01 = result_m01.bits[0]
        m04 = result_m04.bits[0]
    except:
        logging.error(traceback.format_exc())
        pass
    show_m01_value(m01)
    show_cur_m53_value(cur_m53)
    show_cur_m54_value(cur_m54)
    show_m04_value(m04)
#리셋버튼 값 체크 및 표시 끝

######  tkinter  end   ######


#Start 버튼 수동 실행 시작
def startbtn():
    global m01, cur_m53, cur_m54, mem_m53, mem_m54, s_time, count, client
    if not(client.connected):
        client = ModbusTcpClient('192.168.102.20' ,502)
    result_m01 = client.read_coils(0x01)

    show_area_base("준비 중")
    show_mask_area("준비 중")
    if result_m01.bits[0] : # 1(True) 이면
        client.write_coils(0x01,0)
    else:
        client.write_coils(0x01,1)
#Start 버튼 수동 실행 끝


#manual_reset 시작
def manual_reset():
    global m01, cur_m53, cur_m54, mem_m53, mem_m54, s_time, count, client
    if not(client.connected):
        client = ModbusTcpClient('192.168.102.20' ,502)
    client.write_coils(0x01,0)
    client.write_coils(0x53,0)
    client.write_coils(0x54,0)

    # 화면에 현재 cable area 표시
    show_area_base("준비 중")
    show_mask_area("준비 중")

#manual_reset 끝

# Make folders if not exsist #
def makedirs(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        logging.error(traceback.format_exc())
        print("Error: Failed to create the directory.")
# Make folder end #


time1, time2, time3, time4, time5, time6 = 0, 0, 0, 0, 0, 0
######  Get cur_m53, cur_m54 Start   ######
m01, m04, cur_m53, cur_m54, s_time, count = False, False, False, False, 0, 0
# cur_m53, cur_m54 = False, False
mem_m53, mem_m54 = cur_m53, cur_m54
# count = 0
# s_time = 0
getm = 0
#20240908 생산중 확인 위해 현재_meter, 현재_cnt 추가
mem_meter, mem_cnt = 0, 0



######  Start button status check start   ######
def check_start():
    #20240908 생산중 확인 위해 현재_meter, 현재_cnt 추가
    global m04, mem_m53, mem_m54, s_time, count, mem_meter, mem_cnt
    start_btn_check()
    
    # resetbtn()

    # get_m()

    # 컴퓨터 키고, 광통신 start 버튼 안눌렀을때 -> cur_m53, cur_m54 = False, False
    # 광통신 start 버튼 처음 누름              -> cur_m53, cur_m54 = True, False
    # 광통신 start 버튼 두번째 누름            -> cur_m53, cur_m54 = False, True


    # 컴퓨터 부팅 후 물리적 Start 버튼이 아직 안눌린 상태이면
    if cur_m53 == False and cur_m54 == False:
        mem_m53, mem_m54 = cur_m53, cur_m54
        # print("   ", i," :화면 전송만 실행")
        # print(" cur_m53: " + str(cur_m53) + " cur_m54: " + str(cur_m54) + " mem_m53: " + str(mem_m53) + " mem_m54: " + str(mem_m54))
        show_camera()
    
    # 컴퓨터 부팅 후 물리적 Start 버튼이 아직 안눌린 상태이면
    elif m04:
        show_camera()

    # 방금 Start 버튼이 눌렸으면
    elif not((mem_m53 == cur_m53) & (mem_m54 == cur_m54)):
        count = 0
        #20240908 생산중 확인 위해 현재_meter, 현재_cnt 추가
        mem_meter, mem_cnt = 0, 0
        # 면적 DB 보관할 폴더 있는지 확인 후 없으면 생성
        path='C:/areaDB/'+date.get_date_in_yyyymm()+'/'+date.get_date_in_yyyymmdd()+'/'
        makedirs(path)

        # 시작 시간 가져오기
        s_time = int(date.get_date_time())
        show_stime(s_time)


        # print("   ", i," :50 프레임 이후 50프레임 평균 으로 밝기 측정, Exposure Time 변경")
        exposure_change()
        # print("   ", i," :10프레임 실행: Segmentation area 측정, 기준 넓이로 지정")
        mask_area_base_set()
        
        #SQL insert (시작시간)
        start.write_sql3(s_time, cable_area_base)
        
        # print("   ", i," :Detact 실행(Start 버튼 누른 후)")
        detect_camera()
        mem_m53, mem_m54 = cur_m53, cur_m54
    # Start 버튼 눌른 후 다음 Start 버튼 누르기 전인가?
    else:
        # print("   ", i," :Detact 실행")
        detect_camera()

######  Start button status check end   ######

def exposure_change():
    cams_bright_mean = []
    #20240908 제품 시작 후 50프래임 이후 50개 수집하여 밝기 계산 코드 추가
    for h in range (100):
        h = h + 1
        i = 0
        grabResults = []
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            
            #20240908 제품 시작 후 50프래임 이후 50개 수집하여 밝기 계산 코드 추가
            if grabResults[i].GrabSucceeded() & (h>50):

                cams_bright_mean.append(np.mean(converter.Convert(grabResults[i]).GetArray()))
                # print(np.mean(cams_bright_mean), cams_bright_mean)


    for i in range(len(cameras)):
        # Set Camera Exposure Time Start
        if (np.mean(cams_bright_mean) > 70):
            cameras[i].ExposureTimeAbs.SetValue(150)
        elif (np.mean(cams_bright_mean) < 35):
            cameras[i].ExposureTimeAbs.SetValue(300)
        # Set Camera Exposure Time End
    
    # print('camera bright:', int(np.mean(cams_bright_mean)), ', len:', len(cams_bright_mean))


mean_masks = []

def mask_area_base_set():
    # print('mask_area_base_set')
    masks = []
    global mask_area_base
    # Exposure Time 설정 후
    # 카메라 10번 실행해서 Cable의 area 기준 값 설정
    for h in range (10):
        h = h + 1
        grabResults = []
        images, results = [], []
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            try:
                if grabResults[i].GrabSucceeded():

                    images.append(converter.Convert(grabResults[i]))
                    images[i] = images[i].GetArray()
                    images[i] = cv2.resize(images[i], (imgsize,imgsize))

                    # Run YOLOv8 inference on the frame
                    # results1 = model(img1)
                    results.append(model.predict(images[i], save=False, imgsz=imgsize, conf=confidence))

                    # # Replace class names with custom labels in the results
                    # for result in results[i]:
                    #     for cls_id, custom_label in class_mapping.items():
                    #         if cls_id in result.names: # check if the class id is in the results
                    #             result.names[cls_id] = custom_label # replace the class name with the custom label

                    #### mask area start ####
                    # Detect가 되고, Detect 의 Class가 0 ("cable") 이면 Mask area 저장
                    if not(results[i][0].masks==None) and (int(results[i][0].boxes.cls[0]) == 0):
                        # Segmentation
                        data = results[i][0].masks.data      # masks, (N, H, W)

                        # generate mask
                        mask = data[0]  # torch.unique(mask) = [0., 1.]
                        # Convert the tensor to a NumPy array
                        mask = mask.cpu().numpy()*255 # np.unique(mask) = [0, 255]
                        mask_count = np.count_nonzero(mask == 255)
                        masks.append(mask_count)
                    #### mask area end ####
            except Exception as e:
                # print(f"===========ERROR==========: {e}")
                # traceback.print_exc(file=sys.stdout)
                logging.error(traceback.format_exc())
                continue

    # 케이블 기준 area 값 설정
    global cable_area_base
    if len(masks) > 1:
        cable_area_base = int(np.mean(masks))
        show_area_base(cable_area_base)
        mean_masks.append(int(np.mean(masks)))

    # 케이블 기준 area 값 DB저장 시작
    # insert 'cable_area_base'
    # 케이블 기준 area 값 DB저장 끝



def show_camera():
    grabResults = []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []

    if cam_on:
        try:
            for i in range(len(cameras)):
                grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
                try: 
                    print(i, '번째 카메라 Grap 결과: ', grabResults[i].GrabSucceeded())
                    if grabResults[i].GrabSucceeded():

                        # print('성공한 i 번째 카메라:', i)
                        # print('before append len(images) = ', len(images))
                        images.append(converter.Convert(grabResults[i]))

                        # print('after append len(images) = ', len(images))
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
                        # label_cameras[i].photo_image = photos[i]
                        
                        # Configure image in the label 
                        # label_cameras[i].configure(image=photos[i])

                        if i == 0:
                            label_camera1.photo_image = photos[i]
                            label_camera1.configure(image=photos[i])
                            # show_camera1(photos[i])
                        elif i == 1:
                            label_camera2.photo_image = photos[i]
                            label_camera2.configure(image=photos[i])
                            # show_camera2(photos[i])
                        elif i == 2:
                            label_camera3.photo_image = photos[i]
                            label_camera3.configure(image=photos[i])
                            # show_camera3(photos[i])



                except Exception as e:
                    # print(f"===========ERROR==========: {e}")
                    # traceback.print_exc(file=sys.stdout)
                    logging.error(traceback.format_exc())
                    continue
        except Exception as e:
            # print(f"===========ERROR==========: {e}")
            # traceback.print_exc(file=sys.stdout)
            logging.error(traceback.format_exc())
            
            win.destroy()
            # pass
        # Repeat the same process after every 10 milliseconds
        label_camera1.after(30, check_start)
                ######  tkinter  end   ###### 


def detect_camera():
    #20240908 생산중 확인 위해 현재_meter, 현재_cnt 추가
    global s_time, count, client, mem_meter, mem_cnt
    grabResults = []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []
    masks = []
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/box/'
    makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/Original/'
    makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/area_box/'
    makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/area_Original/'
    makedirs(path)

    # 제품번호 material_number 가져오기
    try:
        if not(client.connected):
            client = ModbusTcpClient('192.168.102.20' ,502)
        result_n0_1_2  = client.read_holding_registers(120)    # D120   제품번호
        result_n0_3_4  = client.read_holding_registers(121)
        result_n0_5_6  = client.read_holding_registers(122)
        result_n0_7_8  = client.read_holding_registers(123)
        result_n0_9_10  = client.read_holding_registers(124)
        ad=(result_n0_1_2.registers[0])
        bd=(result_n0_3_4.registers[0])
        cd=(result_n0_5_6.registers[0])
        dd=(result_n0_7_8.registers[0])
        ed=(result_n0_9_10.registers[0])
        c1 = (ad & 0x00ff)
        c2 = ad >> 8
        c3 = (bd & 0x00ff)
        c4 = bd >> 8
        c5 = (cd & 0x00ff)
        c6 = cd >> 8
        c7 = (dd & 0x00ff)
        c8 = dd >> 8
        c9  = (ed & 0x00ff)
        c10 = ed >> 8
        s_n = chr(c1)+chr(c2)+chr(c3)+chr(c4)+chr(c5)+chr(c6)+chr(c7)+chr(c8)+chr(c9)+chr(c10)
        show_sn(s_n)
        #20240908 생산중 확인 위해 현재_meter 추가
        result_d40 = client.read_holding_registers(40)    # D40 현재 미터수
        current_meter = result_d40.registers[0]
        show_meter(current_meter)        
        show_feet(current_meter*3.28084)
        result_cnt = client.read_holding_registers(0x0004)  # D4  총회전 카운터
        current_cnt = result_cnt.registers[0]
        show_cnt(current_cnt)


    except Exception as e:
        # print(f"===========ERROR==========: {e}")
        # traceback.print_exc(file=sys.stdout)
        logging.error(traceback.format_exc())
        pass


    if cam_on:
        try:
            for i in range(len(cameras)):
                grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
                try:
                    if grabResults[i].GrabSucceeded():

                        images.append(converter.Convert(grabResults[i]))
                        images[i] = images[i].GetArray()
                        images[i] = cv2.resize(images[i], (imgsize,imgsize))

                        # Run YOLOv8 inference on the frame
                        # results1 = model(img1)
                        results.append(model.predict(images[i], save=False, imgsz=imgsize, conf=confidence))

                        # # Replace class names with custom labels in the results
                        # for result in results[i]:
                        #     for cls_id, custom_label in class_mapping.items():
                        #         if cls_id in result.names: # check if the class id is in the results
                        #             result.names[cls_id] = custom_label # replace the class name with the custom label

                        # Visualize the results on the frame
                        annotated_imgs.append(cv2.resize(results[i][0].plot(), (330,330)))

                        ######  tkinter  start ######
                        # Capture the latest frame and transform to image
                        cap_imgs.append(Image.fromarray(annotated_imgs[i]))

                        # Convert captured image to photoimage 
                        photos.append(ImageTk.PhotoImage(image=cap_imgs[i]))

                        # Displaying photoimage in the label 
                        # label_cameras[i].photo_image = photos[i]
                        
                        # Configure image in the label 
                        # label_cameras[i].configure(image=photos[i])

                        if i == 0:
                            label_camera1.photo_image = photos[i]
                            label_camera1.configure(image=photos[i])
                            # show_camera1(photos[i])
                        elif i == 1:
                            label_camera2.photo_image = photos[i]
                            label_camera2.configure(image=photos[i])
                            # show_camera2(photos[i])
                        elif i == 2:
                            label_camera3.photo_image = photos[i]
                            label_camera3.configure(image=photos[i])
                            # show_camera3(photos[i])

                        #### mask area start ####

                        # Detact 된 항목중 Class가 0 ("cable") 인 항목을 찾기
                        c_num = 0
                        for j in range(len(results[i][0].boxes.cls)):
                            if int(results[i][0].boxes.cls[j]) == 0:
                                c_num = j
                                break
                            
                        # Detect가 되고, Detect 의 Class가 0 ("cable") 이면 Mask area 저장
                        if not(results[i][0].masks==None) and (int(results[i][0].boxes.cls[c_num]) == 0):
                            # Segmentation
                            data = results[i][0].masks.data      # masks, (N, H, W)

                            # generate mask
                            mask = data[c_num]  # torch.unique(mask) = [0., 1.]
                            # Convert the tensor to a NumPy array
                            mask = mask.cpu().numpy()*255 # np.unique(mask) = [0, 255]
                            mask_count = np.count_nonzero(mask == 255)
                            masks.append(mask_count)
                            
                        #### mask area end ####

                        # Detact 된 항목중 Class가 1 ("defact") 인 항목을 찾기
                        d_num = 0
                        for k in range(len(results[i][0].boxes.cls)):
                            if int(results[i][0].boxes.cls[k]) == 1:
                                d_num = k
                                break


                        # Defect가 감지 됐을 때
                        global time1, time2

                        if (int(results[i][0].boxes.cls[d_num]) == 1):
                            time1 = int(date.get_time_millisec())

                            # 20240908 현재 생산된 회전수가 기억된 회전수보다 클때 조건 추가
                            if int(results[i][0].boxes.cls[d_num]) == 1 & (time1 - time2 > 500000):# and (current_cnt > mem_cnt):
                                time2 = int(date.get_time_millisec())
                                detected_time = date.get_time_in_mmddss()
                                detected_date = date.get_date_in_yyyymmdd()
                                count = count + 1
                                
                                # meter, 회전수 메모리 변수 값을 현재 값으로 변경
                                mem_meter = current_meter
                                mem_cnt = current_cnt
                                
                                # 불량 검출 미터 PLC로 보내고 값 오류 m & ft읽어오기
                                client.write_coils(0x0020,1)
                                client.write_coils(0x0020,0)
                                m_m = count + 1000
                                ft_ft = count + 5000
                                d1000_m  = client.read_holding_registers(m_m)
                                d5000_ft = client.read_holding_registers(ft_ft)
                                d_meter = d1000_m.registers[0]
                                d_feet = d5000_ft.registers[0]
                                # area = 123
                                area = int(mean_masks[len(mean_masks)-1])

                                for l in range(len(cameras)):
                                    cv2.imwrite('C:/image/'+detected_date+'/box/'+ str(l) + '_' + detected_time+'.jpg', results[l][0].plot())
                                    cv2.imwrite('C:/image/'+detected_date+'/Original/'+ str(l) + '_' + detected_time+'.jpg', images[l])
                                    
                                    # s_time(제품 키값), material_number(제품번호), seq2(몇번쨰 생성), d_meter(몇미터에서 생성), type(오류 유형), d_time(감지 시간), image(이미지 위치), area(면적)

                                    # 오류 유형
                                    type = "defect"

                                    # 이미지 저장 위치
                                    image = "C:/image/"+detected_date+"/box/"+ str(l) + '_' + str(detected_time)+".jpg"

                                    detect.write_sql(s_time, s_n, count, d_meter, type, detected_time, image, area)
                                    # time.sleep(1)

                        # Detect가 되고, Detect 의 Class가 1 ("error") 이면 SQL 삽입

                        # # 면적이상 이벤트 코드 시작 #
                        # # 면적이상 이벤트 코드 시작 #
                        # # 면적이상 이벤트 코드 시작 #
                        # # 면적이상 이벤트 코드 시작 #

                        
                        # 면적이 기준면적보다 1.3배 클 때
                        global time3, time4
                        if (not (cable_area_base == 0)) and (int(np.mean(masks)) > cable_area_base*1.30) and (len(cameras)==i+1):
                            time3 = int(date.get_time_millisec())

                            # 불량 감지 코드 추가
                            # print("면적불량 감지 !!!")
                            # print("카메라 숫자: ", len(cameras))
                            # print("masks 에 담긴 숫자: ", len(masks))
                            # print("기준값: ", cable_area_base, "현재 케이블 면적: ", int(np.mean(masks)))
                            
                            # 20240908 현재 생산된 회전수가 기억된 회전수보다 클때 조건 추가
                            if (time3-time4 > 500000):# and (current_cnt > mem_cnt):
                                time4 = int(date.get_time_millisec())
                                detected_time = date.get_time_in_mmddss()
                                detected_date = date.get_date_in_yyyymmdd()
                                count = count + 1

                                # meter, 회전수 메모리 변수 값을 현재 값으로 변경
                                mem_meter = current_meter
                                mem_cnt = current_cnt
                                
                                # 불량 검출 미터 PLC로 보내고 값 오류 m & ft읽어오기
                                client.write_coils(0x0020,1)
                                client.write_coils(0x0020,0)
                                m_m = count + 1000
                                ft_ft = count + 5000
                                d1000_m  = client.read_holding_registers(m_m)
                                d5000_ft = client.read_holding_registers(ft_ft)
                                d_meter = d1000_m.registers[0]
                                d_feet = d5000_ft.registers[0]

                                type = "area"
                                
                                area = int(mean_masks[len(mean_masks)-1])
                                
                                for l in range(len(cameras)):
                                    print(l)
                                    cv2.imwrite('C:/image/'+detected_date+'/area_box/'+ str(l) + '_' + detected_time+'.jpg', results[l][0].plot())
                                    cv2.imwrite('C:/image/'+detected_date+'/area_Original/'+ str(l)+ '_' + detected_time+'.jpg', images[l])
                                    
                                    # 이미지 저장 위치
                                    image = "C:/image/"+detected_date+"/area_box/"+ str(l) + '_' + str(detected_time)+".jpg"
                                    
                                    detect.write_sql(s_time, s_n, count, d_meter, type, detected_time, image, area)
                            # print("")
                        # # 면적이상 이벤트 코드 끝 #
                        # # 면적이상 이벤트 코드 끝 #
                        # # 면적이상 이벤트 코드 끝 #
                        # # 면적이상 이벤트 코드 끝 #


                        #### mask area end ####
                except Exception as e:
                    # print(f"===========ERROR==========: {e}")
                    # traceback.print_exc(file=sys.stdout)
                    continue


            # 화면에 현재 cable area 표시
            if len(masks) > 2:
                show_mask_area(int(np.mean(masks)))

            # Mask Area에 값이 있으면 mean_masks에 append
            if len(masks) > 2:
                # mean_masks.append([date.get_time_in_all(), int(np.mean(masks))])
                mean_masks.append(int(np.mean(masks)))

            global time5, time6
            if len(mean_masks) >= 10:
                time5 = int(date.get_date_time())
                mean_masks.pop(0)
                if(time5-time6 > 1):# and (current_cnt > mem_cnt):
                    time6 = int(date.get_date_time())
                    # meter, 회전수 메모리 변수 값을 현재 값으로 변경
                    mem_meter = current_meter
                    mem_cnt = current_cnt
                    areadb.write_sql(s_time, s_n, int(np.mean(mean_masks)))
                    # print(len(mean_masks))
                    # SQL
            
            # Repeat the same process after every 10 milliseconds
            label_camera1.after(30, check_start)

                    ######  tkinter  end   ######

        except Exception as e:
            # print(f"===========ERROR==========: {e}")
            # traceback.print_exc(file=sys.stdout)
            logging.error(traceback.format_exc())
            
            win.destroy()

def start_cam():
    global cam_on
    # stop_cam()
    cam_on = True
    # open_camera()
    check_start()

def stop_cam():
    global cam_on
    # modbus.write_detected([1,0,0], client)
    # print("Sent modbus [1,0,0]")
    cam_on = False


######  tkinter  start   ######

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="Start Camera", command=start_cam) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=2, y=2)

# Create a button to close the camera in GUI app 
btn_stop = Button(win, text="Stop Camera", command=stop_cam) 
# btn_open.grid(row=0,column=0) 
# btn_close.pack()
btn_stop.place(x=92, y=2)

# Create a button to close the camera in GUI app 
btn_close = Button(win, text="Close Program", command=win.destroy) 
# btn_open.grid(row=0,column=0) 
# btn_close.pack()
btn_close.place(x=182, y=2)

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="Start Button", command=startbtn) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=840, y=450)

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="Reset Start button", command=manual_reset) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=840, y=490)


# Auto start
start_cam()
# Create an infinite loop for displaying app on screen 
win.mainloop() 

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
    # print("Sent modbus [1,0,0]")
    # print('fin')
######  tkinter  start   ######
  