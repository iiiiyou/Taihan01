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

file_path = "C:/source/basler/20240922_taihanfiber_5-2.txt"
# Load the YOLOv8 model#
model = YOLO('C:/source/models/20240922_taihanfiber_5-2_best_a.pt')
# model = YOLO('yolov8s-seg.pt')


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
# '192.168.1.101'
# pylon.TlFactory.GetInstance().EnumerateDevices()[1].GetIpAddress()
# '192.168.1.102'
# pylon.TlFactory.GetInstance().EnumerateDevices()[2].GetIpAddress()
# '192.168.1.103'
# pylon.TlFactory.GetInstance().EnumerateDevices()[0].GetSerialNumber()
# '24985755'
# pylon.TlFactory.GetInstance().EnumerateDevices()[1].GetSerialNumber()
# '25002686'
# pylon.TlFactory.GetInstance().EnumerateDevices()[2].GetSerialNumber()
# '25002690'

# pylon.TlFactory.GetInstance().CreateDevice(pylon.TlFactory.GetInstance().EnumerateDevices()[0])
# <Swig Object of type 'Pylon::IPylonDevice *' at 0x000001F360040BA0>

for x in pylon.TlFactory.GetInstance().EnumerateDevices():
    print(x.GetSerialNumber())
    if x.GetSerialNumber() == "24985755":   # Upside A-24985755, 25002688
        print (x.GetIpAddress())
        camera1 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))
    elif x.GetSerialNumber() == "25002690": # Right A-25002690, 25002689
        print (x.GetIpAddress())
        camera2 = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateDevice(x))
    elif x.GetSerialNumber() == "25002686": # Left A-25002686, 25002687
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

while camera1.IsGrabbing() & camera2.IsGrabbing() & camera3.IsGrabbing():
    grabResult1 = camera1.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    grabResult2 = camera2.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    grabResult3 = camera3.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    imgsize, confidence = 640, 0.30
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

        image1 = converter.Convert(grabResult1)
        img1 = image1.GetArray()
        img1r = cv2.resize(img1, (imgsize,imgsize))

        # Run YOLOv8 inference on the frame
        # results1 = model(img1)
        results1 = model.predict(img1r, save=False, imgsz=imgsize, conf=confidence)
        # Visualize the results on the frame
        annotated_img1 = results1[0].plot()
        
        image2 = converter.Convert(grabResult2)
        img2 = image2.GetArray()
        img2r = cv2.resize(img2, (imgsize,imgsize))

        # Run YOLOv8 inference on the frame
        # results2 = model(img2)
        results2 = model.predict(img2r, save=False, imgsz=imgsize, conf=confidence)
        # Visualize the results on the frame
        annotated_img2 = results2[0].plot()
        
        image3 = converter.Convert(grabResult3)
        img3 = image3.GetArray()
        img3r = cv2.resize(img3, (imgsize,imgsize))

        # Run YOLOv8 inference on the frame
        # results3 = model(img3)
        results3 = model.predict(img3r, save=False, imgsz=imgsize, conf=confidence)
        # Visualize the results on the frame
        annotated_img3 = results3[0].plot()
      
        # black_line = np.zeros((1, 640, 3), np.uint8)
        # purple_line = np.full((1, 640, 3), (255, 0, 255), dtype=np.uint8)
        # img = np.concatenate((img1, purple_line, img2, purple_line, img3), axis=0)

        # cv2.namedWindow('title', cv2.WINDOW_AUTOSIZE)
        # cv2.imshow('title', img)
        cv2.imshow('title1', annotated_img1) # cv2.resize(annotated_img1, (330,330)))
        cv2.imshow('title2', annotated_img2) # cv2.resize(annotated_img2, (330,330)))
        cv2.imshow('title3', annotated_img3) # cv2.resize(annotated_img3, (330,330)))

        camera1_jpg = 'images/capture/640_'+date.get_time_millisec()+'_Camera1_original.jpg'
        camera2_jpg = 'images/capture/640_'+date.get_time_millisec()+'_Camera2_original.jpg'
        camera3_jpg = 'images/capture/640_'+date.get_time_millisec()+'_Camera3_original.jpg'
        with open(file_path, "a") as file:
            file.write(camera1_jpg + "\n")
            file.write(camera2_jpg + "\n")
            file.write(camera3_jpg + "\n")

        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera1_original.jpg', img1r)
        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera2_original.jpg', img2r)
        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera3_original.jpg', img3r)
        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera1_annotated.jpg', annotated_img1)
        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera2_annotated.jpg', annotated_img2)
        # cv2.imwrite('images/capture/640_'+date.get_time_millisec()+'_Camera3_annotated.jpg', annotated_img3)    

        k = cv2.waitKey(1)
        # 캡쳐
        if k == ord('c'):
            catpure = cv2.imread('C:/source/ultralytics/capture.png')
            cv2.imwrite('images/capture/640_'+date.get_time_in_mmddss()+'_Camera1_original.jpg', img1r)
            cv2.imwrite('images/capture/640_'+date.get_time_in_mmddss()+'_Camera2_original.jpg', img2r)
            cv2.imwrite('images/capture/640_'+date.get_time_in_mmddss()+'_Camera3_original.jpg', img3r)
            cv2.imwrite('images/capture/640_'+date.get_time_in_mmddss()+'_Camera1_annotated.jpg', annotated_img1)
            cv2.imwrite('images/capture/640_'+date.get_time_in_mmddss()+'_Camera2_annotated.jpg', annotated_img2)
            cv2.imwrite('images/capture/640_'+date.get_time_in_mmddss()+'_Camera3_annotated.jpg', annotated_img3)            

            cv2.imshow('title1', catpure) # cv2.resize(catpure, (330,330)))
            cv2.imshow('title2', catpure) # cv2.resize(catpure, (330,330)))
            cv2.imshow('title3', catpure) # cv2.resize(catpure, (330,330)))
            cv2.waitKey(150)

        if k == 27:
            break
    grabResult1.Release()
    grabResult2.Release()
    grabResult3.Release()
    
# Releasing the resource    
camera.StopGrabbing()

cv2.destroyAllWindows()