import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random
random.seed(4)

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


def _rot90_ccw(v: np.ndarray) -> np.ndarray:
    return np.array([-v[1], v[0]], dtype=float)


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n == 0.0:
        return v.astype(float)
    return v / n


def _bezier_points(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, n: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, n)[:, None]
    omt = 1.0 - t
    return (omt**3) * p0 + 3 * (omt**2) * t * p1 + 3 * omt * (t**2) * p2 + (t**3) * p3


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


def draw_cell(ad, q: int, r: int, offset_x_in: float, offset_y_in: float):
    cx_off, cy_off = axial_to_xy_in(q, r, HEX_SIZE_IN)
    cx = offset_x_in + cx_off
    cy = offset_y_in + cy_off

    ad.penup()
    ad.moveto(cx, cy)

    def draw_polyline(vertices: list[tuple[float, float]]):
        if len(vertices) >= 2:
            ad.draw_path([[x, y] for (x, y) in vertices])
        elif len(vertices) == 1:
            ad.moveto(vertices[0][0], vertices[0][1])

    endpoints = hex_edge_midpoints(HEX_SIZE_IN)
    handle = 0.7
    apothem = HEX_SIZE_IN * math.sqrt(3) / 2
    handle_len = handle * apothem

    i1, i2 = random.sample(range(len(endpoints)), 2)
    s1 = endpoints[i1]
    e1 = endpoints[i2]

    points0 = []
    t0 = _unit(_rot90_ccw(s1))
    t1 = _unit(_rot90_ccw(e1))
    p0 = s1
    p3 = e1
    p1 = s1 + t0 * handle_len
    p2 = e1 + t1 * handle_len
    for p in _bezier_points(p0, p1, p2, p3, 100):
        points0.append(
            (
                cx + p[0],
                cy + p[1],
            )
        )
    draw_polyline(points0)

    remaining = [i for i in range(len(endpoints)) if i not in (i1, i2)]
    i3, i4 = random.sample(remaining, 2)
    s2 = endpoints[i3]
    e2 = endpoints[i4]

    points1 = []
    seg: list[tuple[float, float]] = []
    t2 = _unit(_rot90_ccw(s2))
    t3 = _unit(_rot90_ccw(e2))
    p0 = s2
    p3 = e2
    p1 = s2 + t2 * handle_len
    p2 = e2 + t3 * handle_len
    for p in _bezier_points(p0, p1, p2, p3, 100):
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
            draw_polyline(seg)
            seg = []
        else:
            seg.append((pp[0], pp[1]))

        points1.append((pp[0], pp[1]))
    draw_polyline(seg)

    remaining = [i for i in range(len(endpoints)) if i not in (i1, i2, i3, i4)]
    i5, i6 = random.sample(remaining, 2)
    s3 = endpoints[i5]
    e3 = endpoints[i6]

    seg = []
    t4 = _unit(_rot90_ccw(s3))
    t5 = _unit(_rot90_ccw(e3))
    p0 = s3
    p3 = e3
    p1 = s3 + t4 * handle_len
    p2 = e3 + t5 * handle_len
    for p in _bezier_points(p0, p1, p2, p3, 100):
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
            draw_polyline(seg)
            seg = []
        else:
            seg.append((pp[0], pp[1]))
    draw_polyline(seg)


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

    offset_x_in = PAGE_W_IN / 2 - draw_center_x + ORIGIN_X_IN
    offset_y_in = PAGE_H_IN / 2 - draw_center_y + ORIGIN_Y_IN

    for q, r in coords:
        draw_cell(ad, q, r, offset_x_in, offset_y_in)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
