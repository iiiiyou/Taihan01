import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

files = os.listdir()

jpg_files = []
files = os.listdir()
for file in files:
    if file.endswith(".jpg") or file.endswith(".JPG"):
        jpg_files.append( file)


images = []
for file in jpg_files:
    img = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
    height, width = img.shape

    # Calculate crop dimensions
    crop_height = 213
    crop_start = 214
    crop_end = 427

    # Crop the image
    cropped_img = img[crop_start:crop_end, :]

    cropped_img.shape

    images.append(cropped_img)

padding = [0] *640
images.append(padding)

# Stack the images vertically
stacked_image = np.vstack(images)

stacked_image.shape

plt.imshow(stacked_image, cmap='gray')

stacked_image.shape

# Save the stacked image
cv2.imwrite("stacked_image.jpg", stacked_image)


img = cv2.imread('stacked_image.jpg',0)
plt.imshow(img, cmap='gray')
height, width = img.shape
