from pyaxidraw import axidraw
import numpy as np
import cv2
from PIL import Image

ad = axidraw.AxiDraw()
ad.interactive()
connected = ad.connect()

img = cv2.imread("lisa_cropped.png", cv2.IMREAD_GRAYSCALE)
img = cv2.equalizeHist(img)
WIDTH_PX = 512
img = cv2.resize(img, (WIDTH_PX, int(img.shape[0] * WIDTH_PX / img.shape[1])))
WIDTH_IN = 5
pix2in = WIDTH_IN / img.shape[1]

dithered = Image.fromarray(img).convert("1")
dithered = np.array(dithered).astype(np.uint8) * 255

def gen_spiral_coords():
    center = (WIDTH_PX // 2, WIDTH_PX // 2)
    max_radius = WIDTH_PX // 2
    spacing = 5
    theta = 0
    radius = 0
    dtheta = 0.01
    while radius < max_radius:
        x = center[0] + radius * np.cos(theta)
        y = center[1] + radius * np.sin(theta)
        if 0 <= x < WIDTH_PX and 0 <= y < WIDTH_PX:
            yield (x, y)
        theta += dtheta
        radius += spacing * dtheta / (2 * np.pi)


if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.options.speed_pendown = 100
ad.options.speed_penup = 100
ad.plot_setup()

ad.goto(5.5, 4.25)
ad.pendown()

ad.penup()
offset = (0,0)

for x, y in gen_spiral_coords():
    black = dithered[int(y), int(x)] < 128
    if black:
        ad.goto(((x - WIDTH_PX // 2) * pix2in) + 5.5, ((y - WIDTH_PX // 2) * pix2in) + 4.25)
        ad.pendown()
    else:
        ad.penup()

    offset += (1 * pix2in, 1 * pix2in)
    
    


ad.goto(0, 0)


ad.disconnect()
print("Done!")