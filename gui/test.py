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
# import logging

# logging.basicConfig(filename='C:/source/test.log', level=logging.ERROR)

# Load the YOLOv8 model#
model = YOLO('C:/source/models/taihanfiber_2-1_best.pt')
imgsize, confidence = 640, 0.50
# 케이블 면적 기준 값
cable_area_base = 0

client = ModbusTcpClient('192.168.0.20' ,502)
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

# 케이블 기준 면적 출력 시작
# Create three labels
label_cable_base_area = tk.Label(root, text="케이블 기준 면적: ")
# Grid the labels in a 2x2 grid
label_cable_base_area.place(x=20, y=400)

# Create three labels
label_cable_base_area_value = tk.Label(root, text="측정 전")
# Grid the labels in a 2x2 grid
label_cable_base_area_value.place(x=120, y=400)
def show_area_value(mask_area_base):
    # Create three labels
    label_cable_base_area_value = tk.Label(root, text=mask_area_base)
    # Grid the labels in a 2x2 grid
    label_cable_base_area_value.place(x=120, y=400)
# 케이블 기준 면적 출력 끝


# 현재 케이블 면척 출력 시작
# Create three labels
label_cable_current_area = tk.Label(root, text="현재 케이블 면적: ")
# Grid the labels in a 2x2 grid
label_cable_current_area.place(x=20, y=420)


label_cable_current_area_value = tk.Label(root, text="측정 전")
# Grid the labels in a 2x2 grid
label_cable_current_area_value.place(x=120, y=420)

def show_current_mask_area(current_mask_area):
    # text_cma = current_mask_area, round(cable_area_base/current_mask_area*100, 2)
    label_cable_current_area_value = tk.Label(root, text=current_mask_area)
    # Grid the labels in a 2x2 grid
    label_cable_current_area_value.place(x=120, y=420)
# 현재 케이블 면척 출력 끝


#리셋버튼 값 체크 및 표시 시작
# Create three labels
m53_value_label = tk.Label(root, text="m53_value: ")
m54_value_label = tk.Label(root, text="m54_value: ")
m01_value_label = tk.Label(root, text="m01_value: ")
# Grid the labels in a 2x2 grid
m53_value_label.place(x=20, y=460)
m54_value_label.place(x=20, y=480)
m01_value_label.place(x=20, y=500)

def start_btn_check():
    try:
        global m01, m53, m54, m53m, m54m, s_time, count, client
        if not(client.connected):
            client = ModbusTcpClient('192.168.0.20' ,502)
        result_m53 = client.read_coils(0x53)
        result_m54 = client.read_coils(0x54)
        result_m01 = client.read_coils(0x01)
        # print("type(result_m53.bits[0]): ", type(result_m53.bits[0]))
        # print("result_m53.bits[0]: ", result_m53.bits[0])
        # print("type(result_m54.bits[0]): ", type(result_m54.bits[0]))
        # print("result_m54.bits[0]: ", result_m54.bits[0])
        # print("type(m53): ", type(m53))
        # print("type(m54): ", type(m54))
        m53, m54 = result_m53.bits[0], result_m54.bits[0]
        m01 = result_m01.bits[0]
    except:
        # logging.error(traceback.format_exc())
        pass
    # Create three labels
    m53_value_label = tk.Label(root, text=m53)
    m54_value_label = tk.Label(root, text=m54)
    m01_value_label = tk.Label(root, text=m01)
    # Grid the labels in a 2x2 grid
    m53_value_label.place(x=120, y=460)
    m54_value_label.place(x=120, y=480)
    m01_value_label.place(x=120, y=500)
#리셋버튼 값 체크 및 표시 끝

######  tkinter  end   ######


#Start 버튼 수동 실행 시작
def startbtn():
    global m01, m53, m54, m53m, m54m, s_time, count, client
    if not(client.connected):
        client = ModbusTcpClient('192.168.0.20' ,502)
    result_m01 = client.read_coils(0x01)

    show_area_value("준비 중")
    show_current_mask_area("준비 중")
    if result_m01.bits[0] : # 1(True) 이면
        client.write_coils(0x01,0)
    else:
        client.write_coils(0x01,1)
#Start 버튼 수동 실행 끝


#manual_reset 시작
def manual_reset():
    global m01, m53, m54, m53m, m54m, s_time, count, client
    if not(client.connected):
        client = ModbusTcpClient('192.168.0.20' ,502)
    client.write_coils(0x01,0)
    client.write_coils(0x53,0)
    client.write_coils(0x54,0)

    # 화면에 현재 cable area 표시
    show_current_mask_area("준비 중")

#manual_reset 끝

# Make folders if not exsist #
def makedirs(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        # logging.error(traceback.format_exc())
        print("Error: Failed to create the directory.")
# Make folder end #



######  Get m53, m54 Start   ######
m01, m53, m54, s_time, count = False, False, False, 0, 0
# m53, m54 = False, False
m53m, m54m = m53, m54
# count = 0
# s_time = 0
getm = 0



######  Start button status check start   ######
def check_start():
    global m53m, m54m, s_time
    start_btn_check()
    
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
        show_area_value("준비 중")
        show_camera()

    # 방금 Start 버튼이 눌렸으면
    elif not((m53m == m53) & (m54m == m54)):
        count = 0
        # 면적 DB 보관할 폴더 있는지 확인 후 없으면 생성
        path='C:/areaDB/'+date.get_date_in_yyyymm()+'/'
        makedirs(path)

        # 시작 시간 가져오기
        s_time = int(date.get_date_time())


        # print("   ", i," :10프레임 실행: 밝기 측정, Exposure Time 변경")
        exposure_change()
        # print("   ", i," :10프레임 실행: Segmentation area 측정, 기준 넓이로 지정")
        mask_area_base_set()
        
        #SQL insert (시작시간)
        start.write_sql3(s_time, cable_area_base)
        
        # print("   ", i," :Detact 실행(Start 버튼 누른 후)")
        detect_camera()
        m53m, m54m = m53, m54
    # Start 버튼 눌른 후 다음 Start 버튼 누르기 전인가?
    else:
        # print("   ", i," :Detact 실행")
        detect_camera()

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

                    # Replace class names with custom labels in the results
                    for result in results[i]:
                        for cls_id, custom_label in class_mapping.items():
                            if cls_id in result.names: # check if the class id is in the results
                                result.names[cls_id] = custom_label # replace the class name with the custom label

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
                print(f"===========ERROR==========: {e}")
                traceback.print_exc(file=sys.stdout)
                # logging.error(traceback.format_exc())
                continue

    # 케이블 기준 area 값 설정
    global cable_area_base
    cable_area_base = int(np.mean(masks))
    show_area_value(cable_area_base)

    # 케이블 기준 area 값 DB저장 시작
    # insert 'cable_area_base'
    # 케이블 기준 area 값 DB저장 끝



def show_camera():
    grabResults = []
    images, results, annotated_imgs = [], [], []
    cap_imgs, photos = [], []

    if cam_on:
        for i in range(len(cameras)):
            grabResults.append(cameras[i].RetrieveResult(5000, pylon.TimeoutHandling_ThrowException))
            try: 
                print(i, '번째 카메라 Grap 결과: ', grabResults[i].GrabSucceeded())
                if grabResults[i].GrabSucceeded():

                    print('성공한 i 번째 카메라:', i)
                    print('before append len(images) = ', len(images))
                    images.append(converter.Convert(grabResults[i]))

                    print('after append len(images) = ', len(images))
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
            except Exception as e:
                print(f"===========ERROR==========: {e}")
                traceback.print_exc(file=sys.stdout)
                # logging.error(traceback.format_exc())
                continue
                
        # Repeat the same process after every 10 milliseconds
        label_widgets[0].after(1, check_start)
                ######  tkinter  end   ###### 


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
    # 제품번호 material_number 가져오기
    try:
        if not(client.connected):
            client = ModbusTcpClient('192.168.0.20' ,502)
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

    except Exception as e:
        print(f"===========ERROR==========: {e}")
        traceback.print_exc(file=sys.stdout)
        # logging.error(traceback.format_exc())
        pass

    if cam_on:
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

                    # Detact 된 항목중 Class가 0 ("cable") 인 항목을 찾기
                    d_num = 0
                    for k in range(len(results[i][0].boxes.cls)):
                        if int(results[i][0].boxes.cls[k]) == 1:
                            d_num = k
                            break

                    if int(results[i][0].boxes.cls[d_num]) == 1:
                        detected_time = date.get_time_in_mmddss()
                        detected_date = date.get_date_in_yyyymmdd()
                        cv2.imwrite('C:/image/'+detected_date+'/box/'+detected_time+'.jpg', results[i][0].plot())
                        cv2.imwrite('C:/image/'+detected_date+'/Original/'+detected_time+'_Original.jpg', images[i])
                        count = count + 1

                        # s_time(제품 키값), material_number(제품번호), seq2(몇번쨰 생성), d_meter(몇미터에서 생성), type(오류 유형), d_time(감지 시간), image(이미지 위치), area(면적)

                        # 감지 시간 저장
                        d_time = int(detected_time)

                        # 불량 검출 미터 PLC로 보내고 값 오류 m & ft읽어오기
                        client.write_coils(0x0020,1)
                        client.write_coils(0x0020,0)
                        m_m = i + 1000
                        ft_ft = i + 5000
                        d1000_m  = client.read_holding_registers(m_m)
                        d5000_ft = client.read_holding_registers(ft_ft)
                        d_meter = d1000_m.registers[0]
                        d_feet = d5000_ft.registers[0]
                        
                        # 오류 유형
                        type = "detect"

                        # 이미지 저장 위치
                        image = "C:/image/"+detected_date+"/box/"+str(d_time)+".jpg"
                        # area = 123
                        area = int(mean_masks[len(mean_masks)-1])

                        detect.write_sql(s_time, s_n, count, d_meter, type, d_time, image, area)

                    # Detect가 되고, Detect 의 Class가 1 ("error") 이면 SQL 삽입

                    # # 면적이상 이벤트 코드 시작 #
                    # # 면적이상 이벤트 코드 시작 #
                    # # 면적이상 이벤트 코드 시작 #
                    # # 면적이상 이벤트 코드 시작 #
                    if (not (cable_area_base == 0)) and (int(np.mean(masks)) > cable_area_base*1.2) and (len(cameras)==i+1):
                        # 불량 감지 코드 추가
                        # print("면적불량 감지 !!!")
                        # print("카메라 숫자: ", len(cameras))
                        # print("masks 에 담긴 숫자: ", len(masks))
                        # print("기준값: ", cable_area_base, "현재 케이블 면적: ", int(np.mean(masks)))
                        for l in range(len(cameras)):
                            # print(l)
                            detected_time = date.get_time_in_mmddss()
                            detected_date = date.get_date_in_yyyymmdd()
                            cv2.imwrite('C:/image/'+detected_date+'/area_box/'+detected_time+'.jpg', results[l][0].plot())
                            cv2.imwrite('C:/image/'+detected_date+'/area_Original/'+detected_time+'_Original.jpg', images[l])
                            count = count + 1
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
            show_current_mask_area(int(np.mean(masks)))

        # Mask Area에 값이 있으면 mean_masks에 append
        if len(masks) > 2:
            # mean_masks.append([date.get_time_in_all(), int(np.mean(masks))])
            mean_masks.append(int(np.mean(masks)))

        if len(mean_masks) >= 10:
            areadb.write_sql(s_time, s_n, int(np.mean(mean_masks)))
            # mean_masks.pop(0)
            mean_masks.clear()
            # print(len(mean_masks))



        
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
    # print("Sent modbus [1,0,0]")
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

# Create a button to open the camera in GUI app 
btn_open = Button(root, text="Start Button", command=startbtn) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=840, y=450)

# Create a button to open the camera in GUI app 
btn_open = Button(root, text="Reset Start button", command=manual_reset) 
# btn_open.grid(row=0,column=0) 
# btn_open.pack()
btn_open.place(x=840, y=490)


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
    # print("Sent modbus [1,0,0]")
    # print('fin')
######  tkinter  start   ######
  