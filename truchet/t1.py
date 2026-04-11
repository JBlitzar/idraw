import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random

# from pyaxidraw import axidraw
from fake_ad import FakeAD

# ad = axidraw.AxiDraw()
ad = FakeAD()
ad.interactive()
if not ad.connect():
    exit(1)
ad.options.speed_pendown = 100
ad.options.speed_penup = 100
ad.options.pen_rate_lower = 100
ad.options.pen_rate_raise = 100
# ad.options.const_speed = True
ad.penup()

CELL_SIZE_IN = 0.5
GRID_W = 20
GRID_H = 20


def draw_cell(x, y):
    ad.penup()
    ad.goto(x * CELL_SIZE_IN, y * CELL_SIZE_IN)

    n = 4
    endpoints = [(0, 1), (1, 0), (-1, 0), (0, -1)]
    M0 = random.random() * 0.25

    s1 = np.array(random.choice(endpoints), dtype=float)
    e1 = np.array(random.choice(endpoints), dtype=float)
    while np.array_equal(e1, s1):
        e1 = np.array(random.choice(endpoints), dtype=float)

    v0 = M0 * s1
    v1 = -M0 * e1
    down = False
    points0 = []
    for t in np.linspace(0, 1, 100):
        p = (
            (1 - t) ** 3 * s1
            + 3 * (1 - t) ** 2 * t * v0
            + 3 * (1 - t) * t**2 * v1
            + t**3 * e1
        )
        ad.goto(
            x * CELL_SIZE_IN + p[0] * CELL_SIZE_IN / 2,
            y * CELL_SIZE_IN + p[1] * CELL_SIZE_IN / 2,
        )
        points0.append(
            (
                x * CELL_SIZE_IN + p[0] * CELL_SIZE_IN / 2,
                y * CELL_SIZE_IN + p[1] * CELL_SIZE_IN / 2,
            )
        )
        if not down:
            ad.pendown()
            down = True
    ad.penup()

    used = {tuple(s1.tolist()), tuple(e1.tolist())}
    remaining = [p for p in endpoints if p not in used]
    s2_t, e2_t = random.sample(remaining, 2)
    s2 = np.array(s2_t, dtype=float)
    e2 = np.array(e2_t, dtype=float)

    v2 = M0 * s2
    v3 = -M0 * e2
    down = False
    for t in np.linspace(0, 1, 100):
        p = (
            (1 - t) ** 3 * s2
            + 3 * (1 - t) ** 2 * t * v2
            + 3 * (1 - t) * t**2 * v3
            + t**3 * e2
        )

        pp = (
            x * CELL_SIZE_IN + p[0] * CELL_SIZE_IN / 2,
            y * CELL_SIZE_IN + p[1] * CELL_SIZE_IN / 2,
        )
        flag = False
        for prev in points0:
            if (pp[0] - prev[0]) ** 2 + (pp[1] - prev[1]) ** 2 < (
                CELL_SIZE_IN / 4
            ) ** 2:
                flag = True
                break

        if flag:
            ad.penup()
            down = False

        ad.goto(pp[0], pp[1])
        if not down:
            ad.pendown()
            down = True


for x in range(GRID_W):
    for y in range(GRID_H):
        draw_cell(x, y)

ad.penup()
ad.goto(0, 0)
ad.disconnect()
