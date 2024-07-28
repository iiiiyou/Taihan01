
import pypylon.pylon as pylon
import matplotlib.pyplot as plt
import numpy as np
import cv2

tlf = pylon.TlFactory.GetInstance()
devices = tlf.EnumerateDevices()

converter = pylon.ImageFormatConverter()
# converting to opencv bgr format
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

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

h = 0
grabResults, cams_bright_mean = [], []

def exposure():
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


exposure()