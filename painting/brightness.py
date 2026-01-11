import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

from pyaxidraw import axidraw
# from fake_ad import FakeAD


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
OFFSET = (0, 0)
h, w = img.shape

width_in = 8

pix2in = width_in / w
height_in = h * pix2in


def followAllPoints(edges):
    h, w = edges.shape
    for y in range(h):
        for x in range(w):
            if edges[y, x] != 0:
                followPoints(x, y, edges)


def followPoints(x, y, edges):
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


# ad = axidraw.AxiDraw()
ad = FakeAD(speed=0)
ad.interactive()
if not ad.connect():
    exit(1)
ad.penup()

ad.options.speed_pendown = 100
ad.options.speed_penup = 100

ad.update()

testmask = brightness_bin_masks[-1]
component_masks = []
num_labels, labels_im = cv2.connectedComponents(testmask)
for label in range(1, num_labels):
    component_mask = np.uint8(labels_im == label) * 255
    component_masks.append(component_mask)
for i, comp_mask in enumerate(component_masks):
    cv2.imwrite(f"painting/component_{i}.png", comp_mask)
    edgePoints = cv2.findContours(
        comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )[0]
    edge_img = np.zeros_like(img)
    cv2.drawContours(edge_img, edgePoints, -1, 255, 1)
    followAllPoints(edge_img)


ad.penup()
ad.goto(0, 0)
ad.disconnect()
import os

os.system("axi off")
print("Done!")
