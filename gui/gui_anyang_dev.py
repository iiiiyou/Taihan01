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
import util.merge as imgmerge
import SQL.insert_sqllite_start as start
import SQL.insert_sqllite_detect as detect
import SQL.insert_sqllite_area as areadb
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import *
import time
import logging
import threading
import queue

logging.basicConfig(filename='C:/source/test.log', level=logging.ERROR)

# Load the YOLOv8 model#
# model = YOLO('C:/source/models/taihanfiber_13-1_20250325_yolo11m-seg_best.pt') # pruning 적용
model = YOLO('C:/source/models/taihanfiber_14-1_20250406_yolo11m-seg_best.pt') # pruning 적용
imgsize = 640
confidence = 0.48
reset_confidence = 0.48
# 케이블 면적 기준 값
cable_area_base = 0

client = ModbusTcpClient('192.168.102.20' ,502)
# Define a class mapping dictionary
class_mapping = {
    1: 'Defect', # The key is the class id, you may need to adjust according to your model
    # Add more mappings as needed
}

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
win.geometry("820x540+100+0")

# Create a label to display the video frames
# label = tk.Label(win)
# label.pack()

label_cameras = []

# Camera 0
label_camera1 = Label(win)
label_camera1.place(x=280, y=2)
# img = PhotoImage(file = "C:/source/tkinter/Daum_communication_logo.svg.png", master = win)
# img = img.subsample(3)
# lab_d.config(image = img)
# lab_d.pack()
def show_camera1(camera1):
    label_camera1.config(image = camera1)
# label_camera1.pack()

# 검사 상태 라벨
label_cable1 = Label(win)
label_cable1.config(text = "검사 상태: ")
label_cable1.place(x=20, y=60)
# label_cable1.pack()

# 검사 상태 값
value_cable1= Label(win)
value_cable1.config(text = "준비 중")
value_cable1.place(x=120, y=60)
def show_area_base(mask_area_base):
    value_cable1.config(text = mask_area_base)
# value_cable1.pack()

# Confidence 라벨
label_cable2 = Label(win)
label_cable2.config(text = "Confidence: ")
label_cable2.place(x=20, y=80)
# label_cable2.pack()

# Confidence 값
value_cable2 = Label(win)
value_cable2.config(text = "준비 중")
value_cable2.place(x=120, y=80)
def show_mask_area(current_mask_area):
    value_cable2.config(text = current_mask_area)
# value_cable2.pack()

# function to display user text when 
# button is clicked
def confidence_change():
    global confidence
    new_confidence = float(entry_confidence.get())
    confidence = new_confidence

def confidence_init():
    global reset_confidence
    entry_confidence.delete(0, END)
    entry_confidence.insert(0, reset_confidence) # 0.5를 기본값으로 설정  
    label_confidence3.place(x=20, y=100)

# Confidence 라벨
label_confidence3 = Label(win)
label_confidence3.config(text = "Confidence 변경: ")
label_confidence3.place(x=20, y=100)

# Confidence 입력 필드
entry_confidence = Entry(win, width = 10)
entry_confidence.insert(0, confidence) # 0.5를 기본값으로 설정
entry_confidence.place(x=120, y=100)
    
# Confidence 변경 버튼
btn_confidence = Button(win, text="Change", command=confidence_change) 
btn_confidence.place(x=200, y=100)

# 처리 속도 라벨
label_speed1 = Label(win)
label_speed1.config(text = "처리속도(ms): ")
label_speed1.place(x=20, y=120)
# label_cable2.pack()

# Confidence 값
value_speed1 = Label(win)
value_speed1.config(text = "준비 중")
value_speed1.place(x=120, y=120)
def show_speed1(speed):
    speed = speed / 1000
    speed = f"{speed:,.0f} ms"
    value_speed1.config(text = speed)
# value_cable2.pack()

# 처리 속도 라벨
label_speed2 = Label(win)
label_speed2.config(text = "처리속도(fps): ")
label_speed2.place(x=20, y=140)
# label_cable2.pack()

# Confidence 값
value_speed2 = Label(win)
value_speed2.config(text = "준비 중")
value_speed2.place(x=120, y=140)
def show_speed2(speed):
    speed = 1 / (speed / 1000000)
    speed = f"{speed:,.0f} fps"
    value_speed2.config(text = speed)
# value_cable2.pack()


# 처리 속도 라벨
label_speed3 = Label(win)
label_speed3.config(text = "최대처리(cm/s): ")
label_speed3.place(x=20, y=160)
# label_cable2.pack()

# Confidence 값
value_speed3 = Label(win)
value_speed3.config(text = "준비 중")
value_speed3.place(x=120, y=160)
def show_speed3(speed):
    speed = 1 / (speed / 1000000)
    speed = speed * 6
    speed = f"{speed:,.0f} cm/s"
    value_speed3.config(text = speed)
# value_cable2.pack()


# # Create a button to open the camera in GUI app 
# btn_open = Button(win, text="Reset Start button", command=manual_reset) 
# # btn_open.grid(row=0,column=0) 
# # btn_open.pack()
# btn_open.place(x=120, y=505)




# m01 라벨
label_m01 = Label(win)
label_m01.config(text = "m01_value: ")
label_m01.place(x=20, y=420)
# label_m01.pack()

# m01 값
value_m01 = Label(win)
value_m01.config(text = "측정 전")
value_m01.place(x=120, y=420)
def show_m01_value(m01_value):
    value_m01.config(text = m01_value)
# value_m01.pack()

# m53 라벨
label_m53 = Label(win)
label_m53.config(text = "m53_value: ")
label_m53.place(x=20, y=440)
# label_m53.pack()

# m53 값
value_m53 = Label(win)
value_m53.config(text = "측정 전")
value_m53.place(x=120, y=440)
def show_m53_value(m53_value):
    value_m53.config(text = m53_value)
# value_m53.pack()

# m54 라벨
label_m54 = Label(win)
label_m54.config(text = "m54_value: ")
label_m54.place(x=20, y=460)
# label_m54.pack()

# m54 값
value_m54 = Label(win)
value_m54.config(text = "측정 전")
value_m54.place(x=120, y=460)
def show_m54_value(m54_value):
    value_m54.config(text = m54_value)
# value_m54.pack()

# m04 라벨
label_m04 = Label(win)
label_m04.config(text = "m04_value: ")
label_m04.place(x=20, y=480)
# label_m54.pack()

# m54 값
value_m04 = Label(win)
value_m04.config(text = "측정 전")
value_m04.place(x=120, y=480)
def show_m04_value(m04_value):
    value_m04.config(text = m04_value)
# value_m54.pack()

# Threading image save
def save_image(filename, frame):
    cv2.imwrite(filename, frame)

# Threading save SQL
def write_detected_sql(mmddhhnnss, serial_number, err_cnt_array, d_meter, type, d_time, image, area):
    detect.write_sql(mmddhhnnss, serial_number, err_cnt_array, d_meter, type, d_time, image, area)

# Threading image save
def write_start_sql(mmddhhnnss, cable_area_base):
    start.write_sql3(mmddhhnnss, cable_area_base)


# image gamma_correction
def gamma_correction(image, gamma):
    lookUpTable = np.empty((1, 256), np.uint8)
    for i in range(256):
        lookUpTable[0, i] = np.clip(pow(i / 255.0, gamma) * 255.0, 0, 255)
    gamma_image = cv2.LUT(image, lookUpTable)
    return gamma_image

# PLC readcoil status
def plc_status(client):
    try:
        if not(client.connected):
            client = ModbusTcpClient('192.168.102.20' ,502)
        result_m53 = client.read_coils(0x53)
        result_m54 = client.read_coils(0x54)
        result_m01 = client.read_coils(0x01)
        result_m04 = client.read_coils(0x04)
        # print("type(result_m53.bits[0]): ", type(result_m53.bits[0]))
        # print("result_m53.bits[0]: ", result_m53.bits[0])
        # print("type(result_m54.bits[0]): ", type(result_m54.bits[0]))
        # print("result_m54.bits[0]: ", result_m54.bits[0])
        # print("type(m53): ", type(m53))
        # print("type(m54): ", type(m54))
        m53, m54 = result_m53.bits[0], result_m54.bits[0]
        m01 = result_m01.bits[0]
        m04 = result_m04.bits[0]
        return m01, m04, m53, m54
    except:
        logging.error(traceback.format_exc())
        pass

# PLC readcoil starttime
def plc_starttime(client):
    try:
        if not(client.connected):
            client = ModbusTcpClient('192.168.102.20' ,502)
        # 제품 시작시간 가져오기
        result_d632 = client.read_holding_registers(632)    # D632 시작 년도 4자리
        result_d621 = client.read_holding_registers(621)    # D621 시작 월 2자리
        result_d622 = client.read_holding_registers(622)    # D622 시작 일 2자리
        result_d623 = client.read_holding_registers(623)    # D623 시작 시 2자리
        result_d624 = client.read_holding_registers(624)    # D624 시작 분 2자리
        result_d625 = client.read_holding_registers(625)    # D625 시작 초 2자리
        yyyy = result_d632.registers[0]
        mm = result_d621.registers[0]
        dd = result_d622.registers[0]
        hh = result_d623.registers[0]
        nn = result_d624.registers[0]
        ss = result_d625.registers[0]
        mm = str(mm).zfill(2)
        dd = str(dd).zfill(2)
        hh = str(hh).zfill(2)
        nn = str(nn).zfill(2)
        ss = str(ss).zfill(2)
        mmddhhnnss = f"{yyyy}{mm}{dd}{hh}{nn}{ss}"
        return mmddhhnnss
    
    except:
        logging.error(traceback.format_exc())
        pass


# plc readcoil getserial
def plc_getserial(client):
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

        return s_n

    except Exception as e:
        # print(f"===========ERROR==========: {e}")
        # traceback.print_exc(file=sys.stdout)
        logging.error(traceback.format_exc())
        pass

def start_btn_check():
    global m01, m04, m53, m54, m53m, m54m, s_time, count, client
    try:
        if not(client.connected):
            client = ModbusTcpClient('192.168.102.20' ,502)
        result_m53 = client.read_coils(0x53)
        result_m54 = client.read_coils(0x54)
        result_m01 = client.read_coils(0x01)
        result_m04 = client.read_coils(0x04)
        # print("type(result_m53.bits[0]): ", type(result_m53.bits[0]))
        # print("result_m53.bits[0]: ", result_m53.bits[0])
        # print("type(result_m54.bits[0]): ", type(result_m54.bits[0]))
        # print("result_m54.bits[0]: ", result_m54.bits[0])
        # print("type(m53): ", type(m53))
        # print("type(m54): ", type(m54))
        m53, m54 = result_m53.bits[0], result_m54.bits[0]
        m01 = result_m01.bits[0]
        m04 = result_m04.bits[0]
    except:
        logging.error(traceback.format_exc())
        pass
    show_m01_value(m01)
    show_m53_value(m53)
    show_m54_value(m54)
    show_m04_value(m04)
#리셋버튼 값 체크 및 표시 끝

######  tkinter  end   ######

#areabaseset 버튼 수동 실행 시작
def areabaseset():
    exposure_change()
    # mask_area_base_set()
#Start 버튼 수동 실행 끝


#Start 버튼 수동 실행 시작
def startbtn():
    global m01, client
    if not(client.connected):
        client = ModbusTcpClient('192.168.102.20' ,502)
    result_m01 = client.read_coils(0x01)

    show_area_base("준비 중")
    show_mask_area("준비 중")
    if result_m01.bits[0] : # 1(True) 이면
        client.write_coils(0x01,0)
    else:
        client.write_coils(0x01,1)
    start_cam()
#Start 버튼 수동 실행 끝


#manual_reset 시작
def manual_reset():   
    global client
    if not(client.connected):
        client = ModbusTcpClient('192.168.102.20' ,502)
    client.write_coils(0x01,0)
    client.write_coils(0x53,0)
    client.write_coils(0x54,0)

    # 화면에 현재 cable area 표시 
    start_btn_check()
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

time1, time2 = 0, 0
time3, time4 = 0, 0
time5, time6 = 0, 0
######  Get m53, m54 Start   ######
m01, m04, m53, m54, s_time, count, mmddhhnnss = False, False, False, False, 0, 0, 0
# m53, m54 = False, False
m53m, m54m = m53, m54
# count = 0
# s_time = 0
getm = 0

detected = []

# 이전과 현재가 바뀌었나 확인
def is_detected(x):
    if (x in detected):
        file_path = "C:/source/log/"+str(date.get_date_in_yyyymmdd())+"_detected.txt"
        # duplicated = str(date.get_date_time()) + ": " + str(x) + ", "
        duplicated = str(x) + ", "
        # with open(file_path, "a") as file:
        #     # file.write(duplicated + "\n")
        #     file.write(duplicated)
        return False
    else:
        if len(detected) >= 30:
            detected.pop(0)
        detected.append(x)
        return True

######  Start button status check start   ######
def check_start():
    global m04, m53m, m54m, s_time, count, detected, mmddhhnnss, check_status
        
    if(check_status%10==0):
        start_btn_check()
    elif(check_status==30000):
        check_status=1
    else:
        print("")
        
    check_status+=1
    
    # resetbtn()

    # get_m()

    # 컴퓨터 키고, 광통신 start 버튼 안눌렀을때 -> m53, M54 = False, False
    # 광통신 start 버튼 처음 누름              -> m53, M54 = True, False
    # 광통신 start 버튼 두번째 누름            -> m53, M54 = False, True


    # 컴퓨터 부팅 후 물리적 Start 버튼이 아직 안눌린 상태이면
    if m53 == False and m54 == False:
        m53m, m54m = m53, m54
        # print("   ", i," :화면 전송만 실행")
        # print(" m53: " + str(m53) + " m54: " + str(m54) + " m53m: " + str(m53m) + " m54m: " + str(m54m))
        show_camera()
    
    # 컴퓨터 부팅 후 물리적 Start 버튼이 아직 안눌린 상태이면
    elif m04:
        show_camera()

    # 방금 Start 버튼이 눌렸으면
    elif not((m53m == m53) & (m54m == m54)):
        count = 0
        # 면적 DB 보관할 폴더 있는지 확인 후 없으면 생성
        path='C:/areaDB/'+date.get_date_in_yyyymm()+'/'+date.get_date_in_yyyymmdd()+'/'
        makedirs(path)

        # 시작 시간 가져오기
        # s_time = int(date.get_date_time())
        
        # # 제품 시작시간 가져오기
        # result_d632 = client.read_holding_registers(632)    # D632 시작 년도 4자리
        # result_d621 = client.read_holding_registers(621)    # D621 시작 월 2자리
        # result_d622 = client.read_holding_registers(622)    # D622 시작 일 2자리
        # result_d623 = client.read_holding_registers(623)    # D623 시작 시 2자리
        # result_d624 = client.read_holding_registers(624)    # D624 시작 분 2자리
        # result_d625 = client.read_holding_registers(625)    # D625 시작 초 2자리
        # yyyy = result_d632.registers[0]
        # mm = result_d621.registers[0]
        # dd = result_d622.registers[0]
        # hh = result_d623.registers[0]
        # nn = result_d624.registers[0]
        # ss = result_d625.registers[0]
        # mm = str(mm).zfill(2)
        # dd = str(dd).zfill(2)
        # hh = str(hh).zfill(2)
        # nn = str(nn).zfill(2)
        # ss = str(ss).zfill(2)
        # mmddhhnnss = f"{yyyy}{mm}{dd}{hh}{nn}{ss}"

        mmddhhnnss = plc_starttime(client)


        # print("   ", i," :10프레임 실행: 밝기 측정, Exposure Time 변경")
        exposure_change()
        # print("   ", i," :10프레임 실행: Segmentation area 측정, 기준 넓이로 지정")
        # mask_area_base_set()
        
        #SQL insert (시작시간)
        
        start_sql_thread = threading.Thread(target=write_start_sql, args=(mmddhhnnss, cable_area_base))
        start_sql_thread.start()
        start_sql_thread.join()
        # start.write_sql3(mmddhhnnss, cable_area_base)
        
        # print("   ", i," :Detact 실행(Start 버튼 누른 후)")

        # confidence_init() 
        detect_camera()

        
        file_path = "C:/source/log/"+str(date.get_date_in_yyyymmdd())+"_detected.txt"
        x = sorted(detected)
        txt_detected = str(date.get_date_time()) + ": " + str(len(detected)) + ": " + str(x)
        with open(file_path, "a") as file:
            file.write("\n" + txt_detected + "\n")

        detected = []
        m53m, m54m = m53, m54
    # Start 버튼 눌른 후 다음 Start 버튼 누르기 전인가?
    else:
        # print("   ", i," :Detact 실행")
        detect_camera()

######  Start button status check end   ######

def exposure_change():
    cams_bright_mean = []
    for h in range(100):
        h = h + 1
        i = 0
        grabResults = []
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
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


q= queue.Queue()

def camara_img_merge():
    grabResults = []
    images, results, annotated_imgs = [], [], []
    try:
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            try: 
                print(i, '번째 카메라 Grap 결과: ', grabResults[i].GrabSucceeded())
                if grabResults[i].GrabSucceeded():

                    images.append(converter.Convert(grabResults[i]))
                    images[i] = images[i].GetArray()
                    images[i] = cv2.resize(images[i], (imgsize,imgsize))

            except Exception as e:
                # print(f"===========ERROR==========: {e}")
                # traceback.print_exc(file=sys.stdout)
                logging.error(traceback.format_exc())
                pass
                    
        # 사진 3장 합치기
        channel = 3 if len(images[0].shape) == 3 else 2 # 채널 확인
        merge_img = imgmerge.merge(images, channel) # 합치기
        q.put(merge_img)
        
    except Exception as e:
        # print(f"===========ERROR==========: {e}")
        # traceback.print_exc(file=sys.stdout)
        logging.error(traceback.format_exc())
        pass


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

                        images.append(converter.Convert(grabResults[i]))
                        images[i] = images[i].GetArray()
                        images[i] = cv2.resize(images[i], (imgsize,imgsize))

                except Exception as e:
                    # print(f"===========ERROR==========: {e}")
                    # traceback.print_exc(file=sys.stdout)
                    logging.error(traceback.format_exc())
                    continue
            
                       
            # 사진 3장 합치기
            channel = 3 if len(images[0].shape) == 3 else 2 # 채널 확인
            merge_img = imgmerge.merge(images, channel) # 합치기

            # camara threading
            # merge_start = threading.Thread(target=camara_img_merge,args=())
            # merge_start.start()
            # merge_start.join()

            # merge_img = q.get()
            # camara threading end

            # cv2.imshow('title1', merge_img)# cv2.resize(img1r, (330,330)))
            # cv2.waitKey(0)

            merge_img_resized = cv2.resize(merge_img, (530,530))

            ######  tkinter  start ######
            # Capture the latest frame and transform to image
            cap_img = Image.fromarray(merge_img_resized)

            # Convert captured image to photoimage 
            photo = ImageTk.PhotoImage(image=cap_img)
            label_camera1.photo_image = photo
            label_camera1.configure(image=photo)

        except Exception as e:
            # print(f"===========ERROR==========: {e}")
            # traceback.print_exc(file=sys.stdout)
            logging.error(traceback.format_exc())
            pass
            win.destroy()
            # pass
        # Repeat the same process after every 10 milliseconds
        label_camera1.after(30, check_start)
                ######  tkinter  end   ###### 

def difference(before, after):
    diff = after - before
    return diff

camera_log_start_time = date.get_time_millisec()
def camera_frame_log(ctime, detected, confi):
    file_path = "C:/source/log/camera_"+camera_log_start_time+".txt"
    with open(file_path, "a") as file:
        file.write(ctime + "__" + detected + "__" + str(confi) + "\n")

def detect_camera():
    global s_time, count, client
    grabResults = []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []
    masks = []
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/box/'
    makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/Original/'
    makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'_under50/box/'
    makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'_under50/Original/'
    makedirs(path)
    # path = 'C:/image/'+date.get_date_in_yyyymmdd()+'_notdetected/box/'
    # makedirs(path)
    path = 'C:/image/'+date.get_date_in_yyyymmdd()+'_notdetected/Original/'
    makedirs(path)
    # path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/area_box/'
    # makedirs(path)
    # path = 'C:/image/'+date.get_date_in_yyyymmdd()+'/area_Original/'
    # makedirs(path)


    global time3, time4
    time3 = int(date.get_time_millisec())

    # # 제품번호 material_number 가져오기
    
    # try:
    #     if not(client.connected):
    #         client = ModbusTcpClient('192.168.102.20' ,502)
    #     result_n0_1_2  = client.read_holding_registers(120)    # D120   제품번호
    #     result_n0_3_4  = client.read_holding_registers(121)
    #     result_n0_5_6  = client.read_holding_registers(122)
    #     result_n0_7_8  = client.read_holding_registers(123)
    #     result_n0_9_10  = client.read_holding_registers(124)
    #     ad=(result_n0_1_2.registers[0])
    #     bd=(result_n0_3_4.registers[0])
    #     cd=(result_n0_5_6.registers[0])
    #     dd=(result_n0_7_8.registers[0])
    #     ed=(result_n0_9_10.registers[0])
    #     c1 = (ad & 0x00ff)
    #     c2 = ad >> 8
    #     c3 = (bd & 0x00ff)
    #     c4 = bd >> 8
    #     c5 = (cd & 0x00ff)
    #     c6 = cd >> 8
    #     c7 = (dd & 0x00ff)
    #     c8 = dd >> 8
    #     c9  = (ed & 0x00ff)
    #     c10 = ed >> 8
    #     s_n = chr(c1)+chr(c2)+chr(c3)+chr(c4)+chr(c5)+chr(c6)+chr(c7)+chr(c8)+chr(c9)+chr(c10)

    # except Exception as e:
    #     # print(f"===========ERROR==========: {e}")
    #     # traceback.print_exc(file=sys.stdout)
    #     logging.error(traceback.format_exc())
    #     pass


    if cam_on:
        try:
            for i in range(len(cameras)):
                grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
                try:
                    if grabResults[i].GrabSucceeded():

                        images.append(converter.Convert(grabResults[i]))
                        images[i] = images[i].GetArray()
                        images[i] = cv2.resize(images[i], (imgsize,imgsize))


                        #### mask area end ####
                except Exception as e:
                    # print(f"===========ERROR==========: {e}")
                    # traceback.print_exc(file=sys.stdout)
                    continue


            try:
                # 사진 3장 합치기
                channel = 3 if len(images[0].shape) == 3 else 2 # 채널 확인
                merge_img = imgmerge.merge(images, channel) # 합치기
                # merge_start = threading.Thread(target=camara_img_merge,args=())
                # merge_start.start()
                # merge_start.join()

                # merge_img = q.get()
                # cv2.imshow('title1', merge_img)# cv2.resize(img1r, (330,330)))
                # cv2.waitKey(0)
                

                show_area_base("검사 중")
                show_mask_area(confidence)   

                # Run YOLOv8 inference on the frame
                # results1 = model(img1)
                result = model.predict(merge_img, save=False, imgsz=imgsize, conf=confidence, half=True)

                # Visualize the results on the frame
                annotated_img = cv2.resize(result[0].plot(), (530,530))

                ######  tkinter  start ######
                # Capture the latest frame and transform to image
                cap_img = Image.fromarray(annotated_img)

                # Convert captured image to photoimage 
                photo = ImageTk.PhotoImage(image=cap_img)

                label_camera1.photo_image = photo
                label_camera1.configure(image=photo)

                global time1, time2
                time1 = int(date.get_time_millisec())
                conf_max=0

                gamma_value = 0.6

                if (result[0].boxes.shape[0] > 0) and True :
                # if (result[0].boxes.shape[0] > 0) and (time1 - time2 > (100000*1)) : # 0.1초 * 5

                    conf_max = max(result[0].boxes.conf)

                    # 같은 위치인가 아닌가 확인하기 위해 detect 된 object 위치 파악
                    # 여러 object가 발견되도 첫번째 detect 된 항목만 체크
                    x1, y1, w1, h1 = result[0].boxes.xywh[0]
                    # Convert to integers for drawing
                    x1, y1, w1, h1 = int(x1), int(y1), int(w1), int(h1)
                    if True: # 이미 발견되지 않았으면(detected list에 없으면)
                    # if is_detected(x1)== True: # 이미 발견되지 않았으면(detected list에 없으면)
                        if(conf_max>=0.50):
                            time2 = int(date.get_time_millisec())
                            s_n = plc_getserial(client)
                            detected_time = date.get_time_millisec()[0:16]
                            detected_date = date.get_date_in_yyyymmdd()
                            save_thread1 = threading.Thread(target=save_image, args=('C:/image/' + detected_date + '/box/' + detected_time + '.jpg', gamma_correction(result[0].plot(), gamma_value)))
                            save_thread1.start()
                            save_thread1.join()
                            # cv2.imwrite('C:/image/' + detected_date + '/box/' + detected_time + '.jpg', result[0].plot())
                            save_thread2 = threading.Thread(target=save_image, args=('C:/image/' + detected_date + '/Original/' + detected_time + '.jpg', gamma_correction(merge_img, gamma_value)))
                            save_thread2.start()
                            save_thread2.join()
                            # cv2.imwrite('C:/image/' + detected_date + '/Original/' + detected_time + '.jpg', merge_img)
                            count = count + 1

                            # PLC에서 제품 에러 수 가져오기
                            result_err_cnt= client.read_holding_registers(0x0008)
                            err_cnt_array = int(result_err_cnt.registers[0])+1

                            # s_time(제품 키값), material_number(제품번호), seq2(몇번쨰 생성), d_meter(몇미터에서 생성), type(오류 유형), d_time(감지 시간), image(이미지 위치), area(면적)

                            # 감지 시간 저장
                            d_time = int(date.get_time_in_mmddss())

                            # 불량 검출 미터 PLC로 보내고 값 오류 m & ft읽어오기
                            client.write_coils(0x0020,1)
                            client.write_coils(0x0020,0)
                            # m_m = count + 1000
                            # ft_ft = count + 5000
                            m_m = err_cnt_array + 1000
                            # ft_ft = err_cnt_array + 5000
                            d1000_m  = client.read_holding_registers(m_m)
                            # d5000_ft = client.read_holding_registers(ft_ft)
                            d_meter = d1000_m.registers[0]
                            # d_feet = d5000_ft.registers[0]
                            
                            # 오류 유형
                            type = "defect"

                            # 이미지 저장 위치
                            image = "C:/image/"+detected_date+"/box/"+str(detected_time)+".jpg"
                            area = 0
                            # area = int(mean_masks[len(mean_masks)-1])

                            save_sql_thread = threading.Thread(target=write_detected_sql, args=(mmddhhnnss, s_n, err_cnt_array, d_meter, type, d_time, image, area))
                            save_sql_thread.start()
                            save_sql_thread.join()

                            # detect.write_sql(mmddhhnnss, s_n, err_cnt_array, d_meter, type, d_time, image, area)
                            # time.sleep(1)
                        else:
                            detected_time = date.get_time_millisec()[0:16]
                            detected_date = date.get_date_in_yyyymmdd()
                            save_thread3 = threading.Thread(target=save_image, args=('C:/image/' + detected_date + '_under50/box/' + detected_time + '.jpg', gamma_correction(result[0].plot(),gamma_value)))
                            save_thread3.start()
                            save_thread3.join()
                            # cv2.imwrite('C:/image/' + detected_date + '_under70/box/' + detected_time + '.jpg', result[0].plot())
                            save_thread4 = threading.Thread(target=save_image, args=('C:/image/' + detected_date + '_under50/Original/' + detected_time + '.jpg', gamma_correction(merge_img,gamma_value)))
                            save_thread4.start()
                            save_thread4.join()
                            # cv2.imwrite('C:/image/' + detected_date + '_under70/Original/' + detected_time + '.jpg', merge_img)
                else:
                    detected_time = date.get_time_millisec()[0:16]
                    detected_date = date.get_date_in_yyyymmdd()
                    # save_thread3 = threading.Thread(target=save_image, args=('C:/image/' + detected_date + '_notdetected/box/' + detected_time + '.jpg', result[0].plot()))
                    # save_thread3.start()
                    # save_thread3.join()
                    # cv2.imwrite('C:/image/' + detected_date + '_under70/box/' + detected_time + '.jpg', result[0].plot())
                    save_thread4 = threading.Thread(target=save_image, args=('C:/image/' + detected_date + '_notdetected/Original/' + detected_time + '.jpg', gamma_correction(merge_img,gamma_value)))
                    save_thread4.start()
                    save_thread4.join()

                time4 = int(date.get_time_millisec())
                diff = difference(time3, time4)
                show_speed1(diff)
                show_speed2(diff)
                show_speed3(diff)

                # Repeat the same process after every 10 milliseconds
                label_camera1.after(30, check_start)

                        ######  tkinter  end   ######
                        
            except AttributeError as e:
                print(f"===========ERROR==========76: {e}")
                # traceback.print_exc(file=sys.stdout)
                logging.error(traceback.format_exc())
                pass
            except Exception as e:
                print(f"===========ERROR==========763: {e}")
                # traceback.print_exc(file=sys.stdout)
                logging.error(traceback.format_exc())
                pass
        except Exception as e:
            # print(f"===========ERROR==========: {e}")
            # traceback.print_exc(file=sys.stdout)
            logging.error(traceback.format_exc())
            pass
            win.destroy()

check_status = 1

def start_cam():
    global cam_on, check_status
    start_btn_check()
    
    if cam_on == False :
        # stop_cam()
        cam_on = True
        # open_camera()
        if m53 + m54 == 1 :
            show_area_base("검사 중")
        else :
            show_area_base("준비 중")
        check_start()

def stop_cam():
    global cam_on
    # modbus.write_detected([1,0,0], client)
    # print("Sent modbus [1,0,0]")
    cam_on = False
    show_area_base("일시정지")


######  tkinter  start   ######

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="일시정지 해제", command=start_cam) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=2, y=2)

# Create a button to close the camera in GUI app 
btn_stop = Button(win, text="   일시정지   ", command=stop_cam) 
# btn_open.grid(row=0,column=0) 
# btn_close.pack()
btn_stop.place(x=92, y=2)

# Create a button to close the camera in GUI app 
btn_close = Button(win, text="프로그램 종료", command=win.destroy) 
# btn_open.grid(row=0,column=0) 
# btn_close.pack()
btn_close.place(x=182, y=2)

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="면적 초기화", command=areabaseset) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
# btn_open.place(x=840, y=410)

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="Start Button", command=startbtn) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=20, y=505)

# Create a button to open the camera in GUI app 
btn_open = Button(win, text="Reset Start button", command=manual_reset) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=120, y=505)


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