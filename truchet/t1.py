import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random
random.seed(1)

CELL_SIZE_IN = 0.5
GRID_W = 20
GRID_H = 20


def _rot90_ccw(v: np.ndarray) -> np.ndarray:
    return np.array([-v[1], v[0]], dtype=float)


def _bezier_points(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, n: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)[:, None]
    omt = 1.0 - t
    return (omt**3) * p0 + 3 * (omt**2) * t * p1 + 3 * omt * (t**2) * p2 + (t**3) * p3


def draw_cell(ad, x, y):
    ad.penup()
    ad.goto(x * CELL_SIZE_IN, y * CELL_SIZE_IN)

    n = 4
    endpoints = [(0, 1), (1, 0), (-1, 0), (0, -1)]
    handle = random.random() * 0.25

    s1 = np.array(random.choice(endpoints), dtype=float)
    e1 = np.array(random.choice(endpoints), dtype=float)
    while np.array_equal(e1, s1):
        e1 = np.array(random.choice(endpoints), dtype=float)

    # Control points must be offset along the EDGE tangent (perpendicular to the edge normal),
    # otherwise adjacent tiles won't meet smoothly at shared midpoints.
    t0 = _rot90_ccw(s1)
    t1 = _rot90_ccw(e1)
    p0 = s1
    p3 = e1
    p1 = s1 + t0 * handle
    p2 = e1 + t1 * handle
    down = False
    points0 = []
    for p in _bezier_points(p0, p1, p2, p3, 100):
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

    t2 = _rot90_ccw(s2)
    t3 = _rot90_ccw(e2)
    p0 = s2
    p3 = e2
    p1 = s2 + t2 * handle
    p2 = e2 + t3 * handle
    down = False
    for p in _bezier_points(p0, p1, p2, p3, 100):
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


def main():
    from pyaxidraw import axidraw
    # from fake_ad import FakeAD

    ad = axidraw.AxiDraw()
    # ad = FakeAD()
    ad.interactive()
    if not ad.connect():
        return 1
    ad.options.speed_pendown = 100
    ad.options.speed_penup = 100
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    ad.penup()

    for x in range(GRID_W):
        for y in range(GRID_H):
            draw_cell(ad, x, y)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
