from pyaxidraw import axidraw
import math
from PIL import Image
import cv2
import numpy as np


hatch_bins = 3

img = cv2.imread("portrait.jpg", cv2.IMREAD_GRAYSCALE)
img = cv2.equalizeHist(img)
WIDTH_PX = 100
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
img = cv2.GaussianBlur(img, (5, 5), 0)

WIDTH_IN = 5
pix2in = WIDTH_IN / img.shape[1]
in2pix = img.shape[1] / WIDTH_IN

hatch_masks = []
for bin_size in np.arange(256 // hatch_bins, 256 + 1, 256 // hatch_bins):
    _, thresh = cv2.threshold(img, bin_size, 255, cv2.THRESH_BINARY_INV)
    hatch_masks.append(thresh)

# hatch_masks = hatch_masks[::-1]
    

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

ad.penup()

if not connected:
    print("Could not connect to plotter!")
    exit(1)

def hatch_mask(mask, offset=0, spacing=0.2):
    h, w = mask.shape

    for y in np.arange(0, h, spacing * in2pix):

        runs = []
        in_run = False
        start_x = None
        
        for x in range(w):
            if mask[int(y), x] == 255:
                if not in_run:
                    start_x = x
                    in_run = True
            else:
                if in_run:
                    runs.append((start_x, x - 1))
                    in_run = False
        

        if in_run:
            runs.append((start_x, w - 1))
        

        for start_x, end_x in runs:
            ad.goto(start_x * pix2in + offset, y * pix2in + offset)
            ad.pendown()
            ad.goto(end_x * pix2in + offset, y * pix2in + offset)
            ad.penup()

    for x in np.arange(0, w, spacing * in2pix):

        runs = []
        in_run = False
        start_y = None
        
        for y in range(h):
            if mask[y, int(x)] == 255:
                if not in_run:
                    start_y = y
                    in_run = True
            else:
                if in_run:
                    runs.append((start_y, y - 1))
                    in_run = False
        

        if in_run:
            runs.append((start_y, h - 1))
        

        for start_y, end_y in runs:
            ad.goto(x * pix2in + offset, start_y * pix2in + offset)
            ad.pendown()
            ad.goto(x * pix2in + offset, end_y * pix2in + offset)
            ad.penup()

        
        


ad.penup()


ad.goto(0, 0)

for idx, mask in enumerate(hatch_masks[:-1]):
    hatch_mask(mask, offset=0.016237 * idx, spacing=0.1)

ad.penup()
ad.goto(0, 0)
ad.disconnect()
import os
os.system("axi off")
print("Done!")