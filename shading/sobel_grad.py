import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image

# from pyaxidraw import axidraw
from fake_ad import FakeAD


img = cv2.imread("shading/waves.png", cv2.IMREAD_GRAYSCALE)
WIDTH_PX = 350
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
img = cv2.equalizeHist(img)

dithered = np.array(Image.fromarray(img).convert("L"))

print(np.min(dithered), np.max(dithered))


h, w = img.shape

grad_x = cv2.Sobel(img, cv2.CV_64F, 1, 0, ksize=5)
grad_y = cv2.Sobel(img, cv2.CV_64F, 0, 1, ksize=5)

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

OFFSET = (-width_in / 2 + 5.5, -height_in / 2 + 4.25)

for y in trange(h):
    for x in range(w):
        if dithered[y, x] < 128:
            cell_size = pix2in

            r_offset = (
                (np.random.rand() - 0.5) * cell_size,
                (np.random.rand() - 0.5) * cell_size,
            )

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
            ad.goto(x1 + OFFSET[0] + r_offset[0], y1 + OFFSET[1] + r_offset[1])
            ad.pendown()
            ad.goto(x2 + OFFSET[0] + r_offset[0], y2 + OFFSET[1] + r_offset[1])
            ad.penup()

ad.penup()
ad.goto(0, 0)
ad.disconnect()
import os

os.system("axi off")
print("Done!")
os.system('curl -d "done!!" ntfy.sh/jb_pp_109188f37776d45aee070634901e480c')
