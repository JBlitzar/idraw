import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random

random.seed(4)


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    if len(vertices) >= 2:
        ad.draw_path([[x, y] for (x, y) in vertices])
    elif len(vertices) == 1:
        ad.moveto(vertices[0][0], vertices[0][1])


def main():
    from pyaxidraw import axidraw
    # from fake_ad import FakeAD

    ad = axidraw.AxiDraw()
    # ad = FakeAD()

    ad.interactive()
    ad.options.speed_pendown = 2
    ad.options.speed_penup = 50
    # ad.options.const_speed = True
    if not ad.connect():
        return 1

    ad.penup()
    center = (1, 1)
    r = 0.5
    num_points = 100
    points = []
    for i in range(num_points):
        theta = 2 * math.pi * i / num_points
        x = center[0] + r * math.cos(theta)
        y = center[1] + r * math.sin(theta)
        points.append((x, y))
    draw_polyline(ad, points)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
