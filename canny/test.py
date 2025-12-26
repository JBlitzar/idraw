import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

from pyaxidraw import axidraw

img = cv2.imread("camera.png", cv2.IMREAD_GRAYSCALE)
WIDTH_PX = 200
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
img = cv2.equalizeHist(img)

edges = cv2.Canny(img, 200, 300)

cv2.imwrite("canny_output.png", edges)

IMG_WIDTH_IN = 3
pix2in = IMG_WIDTH_IN / edges.shape[1]





h, w = img.shape



ad = axidraw.AxiDraw()
ad.interactive()
if not ad.connect():
    exit(1)
ad.penup()

def followCanny(x, y):
    points = []
    h, w = edges.shape
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if edges[cy, cx] == 0:
            continue
        edges[cy, cx] = 0
        points.append((cx, cy))
        for dydx in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            dx, dy = dydx
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and edges[ny, nx] != 0:
                stack.append((nx, ny))
                break
       
    ad.goto(points[0][0] * pix2in, points[0][1] * pix2in)
    ad.pendown()
    cur = points[0]
    for p in points:
        
        if (p[0] - cur[0])**2 + (p[1] - cur[1])**2 > 5 ** 2:
            cur = p
            ad.goto(p[0] * pix2in, p[1] * pix2in)
        # print(p)
    ad.penup()
    print(".")
        

def followAllCanny():
    h, w = edges.shape
    for y in range(h):
        for x in range(w):
            if edges[y, x] != 0:
                followCanny(x, y)


followAllCanny()

ad.goto(0, 0)
ad.disconnect()
import os
os.system("axi off")
print("Done!")