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

CELL_SIZE_IN = 0.7
GRID_W = 10
GRID_H = 10

HEX_SIZE_IN = CELL_SIZE_IN / math.sqrt(3)
GRID_RADIUS = min(GRID_W, GRID_H) // 2

PAGE_W_IN = 11.0
PAGE_H_IN = 8.5
PAGE_PADDING_IN = 0.25
ORIGIN_X_IN = 0.0
ORIGIN_Y_IN = 0.0


def hex_axial_coords(radius: int) -> list[tuple[int, int]]:
    coords: list[tuple[int, int]] = []
    for q in range(-radius, radius + 1):
        r_min = max(-radius, -q - radius)
        r_max = min(radius, -q + radius)
        for r in range(r_min, r_max + 1):
            coords.append((q, r))
    return coords


def axial_to_xy_in(q: int, r: int, size_in: float) -> tuple[float, float]:
    # Pointy-top hex axial coordinates (q, r)
    x = size_in * math.sqrt(3) * (q + r / 2)
    y = size_in * 1.5 * r
    return x, y


def hex_edge_midpoints(size_in: float) -> list[np.ndarray]:
    # Midpoints of the 6 edges, as vectors from the hex center (in inches).
    apothem = size_in * math.sqrt(3) / 2
    endpoints: list[np.ndarray] = []
    for k in range(6):
        a = math.radians(60 * k)
        endpoints.append(
            np.array([math.cos(a) * apothem, math.sin(a) * apothem], dtype=float)
        )
    return endpoints


def draw_cell(q: int, r: int):
    cx_off, cy_off = axial_to_xy_in(q, r, HEX_SIZE_IN)
    cx = OFFSET_X_IN + cx_off
    cy = OFFSET_Y_IN + cy_off

    ad.penup()
    ad.goto(cx, cy)

    endpoints = hex_edge_midpoints(HEX_SIZE_IN)
    M0 = 0.7

    i1, i2 = random.sample(range(len(endpoints)), 2)
    s1 = endpoints[i1]
    e1 = endpoints[i2]

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
            cx + p[0],
            cy + p[1],
        )
        points0.append(
            (
                cx + p[0],
                cy + p[1],
            )
        )
        if not down:
            ad.pendown()
            down = True
    ad.penup()

    remaining = [i for i in range(len(endpoints)) if i not in (i1, i2)]
    i3, i4 = random.sample(remaining, 2)
    s2 = endpoints[i3]
    e2 = endpoints[i4]

    v2 = M0 * s2
    v3 = -M0 * e2
    down = False
    points1 = []
    for t in np.linspace(0, 1, 100):
        p = (
            (1 - t) ** 3 * s2
            + 3 * (1 - t) ** 2 * t * v2
            + 3 * (1 - t) * t**2 * v3
            + t**3 * e2
        )

        pp = (
            cx + p[0],
            cy + p[1],
        )
        flag = False
        for prev in points0:
            if (pp[0] - prev[0]) ** 2 + (pp[1] - prev[1]) ** 2 < (0.1) ** 2:
                flag = True
                break

        if flag:
            ad.penup()
            down = False

        ad.goto(pp[0], pp[1])
        points1.append((pp[0], pp[1]))
        if not down:
            ad.pendown()
            down = True

    ad.penup()

    remaining = [i for i in range(len(endpoints)) if i not in (i1, i2, i3, i4)]
    i5, i6 = random.sample(remaining, 2)
    s3 = endpoints[i5]
    e3 = endpoints[i6]
    v4 = M0 * s3
    v5 = -M0 * e3

    down = False
    for t in np.linspace(0, 1, 100):
        p = (
            (1 - t) ** 3 * s3
            + 3 * (1 - t) ** 2 * t * v4
            + 3 * (1 - t) * t**2 * v5
            + t**3 * e3
        )
        pp = (
            cx + p[0],
            cy + p[1],
        )
        flag = False
        for prev in points0 + points1:
            if (pp[0] - prev[0]) ** 2 + (pp[1] - prev[1]) ** 2 < (0.1) ** 2:
                flag = True
                break
        if flag:
            ad.penup()
            down = False

        ad.goto(pp[0], pp[1])
        if not down:
            ad.pendown()
            down = True


coords = hex_axial_coords(GRID_RADIUS)
centers = [axial_to_xy_in(q, r, HEX_SIZE_IN) for (q, r) in coords]
min_x = min(x for x, _ in centers) if centers else 0.0
max_x = max(x for x, _ in centers) if centers else 0.0
min_y = min(y for _, y in centers) if centers else 0.0
max_y = max(y for _, y in centers) if centers else 0.0

apothem = HEX_SIZE_IN * math.sqrt(3) / 2
margin = apothem + PAGE_PADDING_IN
draw_center_x = (min_x - margin + max_x + margin) / 2
draw_center_y = (min_y - margin + max_y + margin) / 2

OFFSET_X_IN = PAGE_W_IN / 2 - draw_center_x + ORIGIN_X_IN
OFFSET_Y_IN = PAGE_H_IN / 2 - draw_center_y + ORIGIN_Y_IN

for q, r in coords:
    draw_cell(q, r)

ad.penup()
ad.goto(0, 0)
ad.disconnect()
