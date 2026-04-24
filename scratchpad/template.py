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
    if not ad.connect():
        return 1
    ad.options.speed_pendown = 80
    ad.options.speed_penup = 80
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    ad.penup()

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
