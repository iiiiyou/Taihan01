'''
A simple Program for grabing video from basler camera and converting it to opencv img.
Tested on Basler acA1300-200uc (USB3, linux 64bit , python 3.5)

'''
from pypylon import pylon
from ultralytics import YOLO
import cv2
import numpy as np
import sys
sys.path.append('C:/source')
import util.format_date_time as date
import util.merge as imgmerge
import os
import traceback
import logging

file_path = "C:/source/basler/taihanfiber_14-1_20250409.txt"
# Load the YOLOv8 model#
model = YOLO('C:/source/models/taihanfiber_14-1_20250409_yolo11s-seg_best.pt')
# model = YOLO('yolov8s-seg.pt')


def makedirs(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        logging.error(traceback.format_exc())
        print("Error: Failed to create the directory.")

yymmddss = date.get_date_time()
path = f"C:/source/images/capture/{yymmddss}"
makedirs(path)
path = f"C:/source/images/capture/{yymmddss}/{yymmddss[0:12]}"
makedirs(path)
makedirs(f"{path}/original")
makedirs(f"{path}/box")
            # self.label_fps.config(text=f"FPS: {avg_fps:.2f}")

# conecting to the first available camera
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

# 연결된 장비 목록
# https://docs.baslerweb.com/pylonapi/cpp/class_pylon_1_1_c_tl_factory#function-enumeratedevices
# type(pylon.TlFactory.GetInstance().EnumerateDevices())
# <class 'tuple'>

# type(pylon.TlFactory.GetInstance().EnumerateDevices()[0])
# <class 'pypylon.pylon.DeviceInfo'>

# https://docs.baslerweb.com/pylonapi/cpp/class_pylon_1_1_c_device_info
# pylon.TlFactory.GetInstance().EnumerateDevices()[0].GetIpAddress()


# pylon.TlFactory.GetInstance().CreateDevice(pylon.TlFactory.GetInstance().EnumerateDevices()[0])
# <Swig Object of type 'Pylon::IPylonDevice *' at 0x000001F360040BA0>

for x in pylon.TlFactory.GetInstance().EnumerateDevices():
    print(x.GetSerialNumber())
    if x.GetSerialNumber() == "25002688":   # Upside A-24985755, 25002688
        print (x.GetIpAddress())
        camera1 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))
    elif x.GetSerialNumber() == "25002689": # Right A-25002690, 25002689
        print (x.GetIpAddress())
        camera2 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))
    elif x.GetSerialNumber() == "25002687": # Left A-25002686, 25002687
        print (x.GetIpAddress())
        camera3 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))

#---------------------------------------#
# start #

# conecting to the first available camera
# camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())

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

if camera1.IsGrabbing() & camera2.IsGrabbing() & camera3.IsGrabbing():
    images = []
    grabResult1 = camera1.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    grabResult2 = camera2.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    grabResult3 = camera3.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult1.GrabSucceeded() and grabResult2.GrabSucceeded() and grabResult3.GrabSucceeded():
        # Access the image data

        grabResult1_mean = np.mean(converter.Convert(grabResult1).GetArray())
        print(grabResult1_mean)
        if (grabResult1_mean > 70):
            camera1.ExposureTimeAbs.SetValue(150)
            camera2.ExposureTimeAbs.SetValue(150)
            camera3.ExposureTimeAbs.SetValue(150)

        elif (grabResult1_mean < 30):
            camera1.ExposureTimeAbs.SetValue(300)
            camera2.ExposureTimeAbs.SetValue(300)
            camera3.ExposureTimeAbs.SetValue(300)

# 이전 폴더 생성 시간 초기화
previous_minute = yymmddss[0:12]

while camera1.IsGrabbing() & camera2.IsGrabbing() & camera3.IsGrabbing():
    
    # 현재 시간 가져오기
    current_minute = date.get_date_time()[0:12]
    # 1분마다 새 폴더 생성
    if current_minute != previous_minute:

        # 폴더 경로 생성
        # path = f"C:/source/images/capture/{yymmddss}/{int(date.get_date_time())}"
        path = f"C:/source/images/capture/{yymmddss}/{current_minute}"

        # 폴더 생성
        makedirs(path)
        makedirs(f"{path}/original")
        makedirs(f"{path}/box")

        # 이전 폴더 생성 시간 업데이트
        previous_minute = current_minute
    
    images = []
    grabResult1 = camera1.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    grabResult2 = camera2.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    grabResult3 = camera3.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    imgsize, confidence = 640, 0.30
    if grabResult1.GrabSucceeded() and grabResult2.GrabSucceeded() and grabResult3.GrabSucceeded():
        # Access the image data

        image1 = converter.Convert(grabResult1)        
        image2 = converter.Convert(grabResult2)       
        image3 = converter.Convert(grabResult3)
      
######################################################################## 

     
        images.append(image1)
        images[0] = images[0].GetArray()
        images[0] = cv2.resize(images[0], (imgsize,imgsize))
   
        images.append(image2)
        images[1] = images[1].GetArray()
        images[1] = cv2.resize(images[1], (imgsize,imgsize))

        images.append(image3)
        images[2] = images[2].GetArray()
        images[2] = cv2.resize(images[2], (imgsize,imgsize))

        # 사진 3장 합치기
        channel = 3 if len(images[0].shape) == 3 else 2 # 채널 확인
        merge_img = imgmerge.merge(images, channel) # 합치기


        merge_img_resized = cv2.resize(merge_img, (640,640))   
        merge_result = model.predict(merge_img_resized, save=False, imgsz=imgsize, conf=confidence)
        annotated_merge_img = merge_result[0].plot()
######################################################################## 

        cv2.imshow('Camera', annotated_merge_img) # cv2.resize(annotated_img3, (330,330)))
        # merge_jpg = f"C:/image/capture/{yymmddss}_{date.get_time_millisec()}_merge_jpg_original.jpg"

        # with open(file_path, "a") as file:
        #     file.write(merge_jpg + "\n")

        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_merge_jpg_original.jpg', merge_img_resized)
        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera1_annotated.jpg', annotated_merge_img)
        mmddssss = date.get_time_millisec()
        cv2.imwrite(f"{path}/original/{mmddssss}_original.jpg", merge_img_resized)
        cv2.imwrite(f"{path}/box/{mmddssss}_annotated.jpg", annotated_merge_img)

        k = cv2.waitKey(1)
        # 캡쳐
        if k == ord('c'):
            catpure = cv2.imread('C:/source/ultralytics/capture.png')
            # cv2.imwrite(f"{path}/original/{date.get_time_millisec()}_original.jpg", merge_img_resized)
            # cv2.imwrite(f"{path}/box/{date.get_time_millisec()}_annotated.jpg", annotated_merge_img)
            cv2.imshow('Camera', catpure) # cv2.resize(catpure, (330,330)))
            cv2.waitKey(150)

        if (k == 27) or (cv2.getWindowProperty('Camera', cv2.WND_PROP_VISIBLE) < 1):
            break
    grabResult1.Release()
    grabResult2.Release()
    grabResult3.Release()
    
# Releasing the resource    
camera.StopGrabbing()

cv2.destroyAllWindows()