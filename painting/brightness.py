import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

# from pyaxidraw import axidraw
from fake_ad import FakeAD


img = cv2.imread("painting/dali.png", cv2.IMREAD_GRAYSCALE)
WIDTH_PX = 350
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
img = cv2.GaussianBlur(img, (21, 21), 0)
# img = cv2.equalizeHist(img)
bin_num = 5
brightness_bin_threshes = np.linspace(0, 256, bin_num + 1).astype(int)
brightness_bin_masks = []
for i in range(bin_num - 1):
    lower = brightness_bin_threshes[i]
    upper = brightness_bin_threshes[i + 1]
    lower = int(lower)
    upper = int(upper)
    mask = cv2.inRange(img, lower, upper - 1)
    brightness_bin_masks.append(mask)
cv2.imwrite("painting/brightness_bins.png", np.hstack(brightness_bin_masks))

h, w = img.shape

width_in = 8

pix2in = width_in / w
height_in = h * pix2in


# ad = axidraw.AxiDraw()
ad = FakeAD(speed=0)
ad.interactive()
if not ad.connect():
    exit(1)
ad.penup()

ad.options.speed_pendown = 100
ad.options.speed_penup = 100

ad.update()


ad.penup()
ad.goto(0, 0)
ad.disconnect()
import os

os.system("axi off")
print("Done!")
