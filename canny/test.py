import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

from pyaxidraw import axidraw
# from fake_ad import FakeAD

img = cv2.imread("canny/portrait.png", cv2.IMREAD_GRAYSCALE)
WIDTH_PX = 200
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
# img = cv2.equalizeHist(img)

edges = cv2.Canny(img, 50, 200)

cv2.imwrite("canny/portrait_output.png", edges)

IMG_WIDTH_IN = 6
pix2in = IMG_WIDTH_IN / edges.shape[1]


h, w = img.shape


ad = axidraw.AxiDraw() #FakeAD()  # 
ad.interactive()
if not ad.connect():
    exit(1)
ad.penup()

OFFSET = (-IMG_WIDTH_IN / 2 + 4.25, -h * pix2in / 2 + 5.5 - 1)

grad_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)
grad_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)


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
        for dydx in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            dx, dy = dydx
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and edges[ny, nx] != 0:
                stack.append((nx, ny))
                break

    ad.goto(points[0][0] * pix2in + OFFSET[0], points[0][1] * pix2in + OFFSET[1])
    ad.pendown()
    cur = points[0]
    for p in points:
        if (p[0] - cur[0]) ** 2 + (p[1] - cur[1]) ** 2 > 2**2:
            cur = p
            ad.goto(p[0] * pix2in + OFFSET[0], p[1] * pix2in + OFFSET[1])
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

m = 3
for y in trange(h):
    for x in range(w):
        if m != 0 and np.random.rand() > 1 / m:
            continue
        if img[y, x] < np.percentile(img, 35):
            gx = grad_x[y, x]
            gy = grad_y[y, x]
            angle = math.atan2(gy, gx)  # + math.pi / 2
            x0 = x * pix2in
            y0 = y * pix2in
            length = 0.5 * pix2in
            x1 = x0 + length * math.cos(angle + math.pi / 2)
            y1 = y0 + length * math.sin(angle + math.pi / 2)
            x2 = x0 - length * math.cos(angle + math.pi / 2)
            y2 = y0 - length * math.sin(angle + math.pi / 2)
            ad.goto(x1 + OFFSET[0], y1 + OFFSET[1])
            ad.pendown()
            ad.goto(x2 + OFFSET[0], y2 + OFFSET[1])
            ad.penup()
ad.disconnect()
import os

os.system("axi off")
print("Done!")
