
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
camera, i = [], 0
for d in devices:
    print(d.GetModelName(), d.GetSerialNumber())
    camera.append(pylon.InstantCamera(tlf.CreateDevice(devices[i])))

    # the features of the device are only accessable after Opening the device
    camera[i].Open()
    camera[i].ExposureTimeAbs.SetValue(300)
    i = i + 1

# grab one image with a timeout of 1s
# returns a GrabResult, which is the image plus metadata
res = camera[0].GrabOne(1000)
res = converter.Convert(res)
img = res.GetArray()
# plt.imshow(img)
brightness = np.mean(img)
print(brightness)
