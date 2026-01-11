import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

from pyaxidraw import axidraw
# from fake_ad import FakeAD

INK_POS = (12, 2)


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
OFFSET = (3, 3)
BRUSH_WIDTH_IN = 0.2


h, w = img.shape

width_in = 5

pix2in = width_in / w
height_in = h * pix2in

BRUSH_WIDTH_PX = int(BRUSH_WIDTH_IN / pix2in)


def followAllPoints():
    global edges
    h, w = edges.shape
    for y in range(h):
        for x in range(w):
            if edges[y, x] != 0:
                followPoints(x, y)


def followPoints(x, y):
    global edges
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
    dip()
    ad.goto(points[0][0] * pix2in + OFFSET[0], points[0][1] * pix2in + OFFSET[1])
   
    i = 0
    ad.pendown()
    cur = points[0]
    for p in points:
        if (p[0] - cur[0]) ** 2 + (p[1] - cur[1]) ** 2 > 2**2:
            cur = p
            ad.goto(p[0] * pix2in + OFFSET[0], p[1] * pix2in + OFFSET[1])

            i += 1
            if i % 40 == 0:
                ad.penup()
                dip()
                ad.goto(p[0] * pix2in + OFFSET[0], p[1] * pix2in + OFFSET[1])
                ad.pendown()
        # print(p)
    ad.penup()

    print(".")


ad = axidraw.AxiDraw()

ad.interactive()

connected = ad.connect()
ad.options.model = 2
ad.options.clip_to_page = False
ad.options.pen_pos_up = 100
ad.options.pen_pos_down = 0
ad.update()


def dip():
    ad.goto(INK_POS[0], INK_POS[1])
    ad.pendown()
    ad.penup()


testmask = brightness_bin_masks[-1]
component_masks = []
num_labels, labels_im = cv2.connectedComponents(testmask)
for label in range(1, num_labels):
    component_mask = np.uint8(labels_im == label) * 255
    component_masks.append(component_mask)
for i, comp_mask in enumerate(component_masks):
    cv2.imwrite(f"painting/component_{i}.png", comp_mask)
    edge_img = comp_mask - cv2.erode(comp_mask, np.ones((3,3), np.uint8), iterations=1)

    global edges
    edges = edge_img.copy()
    followAllPoints()
for x in np.arange(0, w, BRUSH_WIDTH_PX):
    runs = []
    in_run = False
    start_y = None

    for y in range(h):
        if testmask[y, int(x)] == 255:
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
        dip()
        ad.goto(x * pix2in + OFFSET[0], start_y * pix2in + OFFSET[1])
        ad.pendown()
        ad.goto(x * pix2in + OFFSET[0], end_y * pix2in + OFFSET[1])
        ad.penup()

ad.penup()
ad.goto(0, 0)
ad.disconnect()
import os

os.system("axi off")
print("Done!")
os.system('curl -d "done!!" ntfy.sh/jb_pp_109188f37776d45aee070634901e480c')
