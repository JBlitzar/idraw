import math
import random

# import matplotlib.pyplot as plt
from copy import deepcopy

import cv2
import numpy as np
import opensimplex
from PIL import Image
from tqdm import trange

random.seed(4)


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    if len(vertices) >= 2:
        ad.draw_path([[x, y] for (x, y) in vertices])
    elif len(vertices) == 1:
        ad.moveto(vertices[0][0], vertices[0][1])


# Initialize noise
opensimplex.seed(42)

# Create a grid of coordinates
width, height = 200, 200
scale = 0.01
noise_array = np.zeros((height, width))


def main():
    # from pyaxidraw import axidraw
    from fake_ad import FakeAD

    # ad = axidraw.AxiDraw()
    ad = FakeAD()
    ad.interactive()
    ad.options.speed_pendown = 80
    ad.options.speed_penup = 80
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    if not ad.connect():
        return 1

    ad.penup()

    for y in range(height):
        for x in range(width):
            noise_array[y][x] = opensimplex.noise2(x * scale, y * scale) / 2 + 0.5

    start = deepcopy([0] * width)
    ls = [start]
    for y in range(height):
        new = []
        for idx, item in enumerate(ls[-1]):
            new.append(item + noise_array[y][idx])
        ls.append(new)

    print(ls)

    W = 11
    H = 8.5
    sc = (W / width, W / width)
    pts = []
    for l in ls:
        pts.append([])
        for idx, item in enumerate(l):
            pts[-1].append((idx * sc[0], item * sc[1]))

    for pl in pts:
        draw_polyline(ad, pl)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# # Visualize the result
# plt.imshow(noise_array, cmap='gray')
# plt.show()
