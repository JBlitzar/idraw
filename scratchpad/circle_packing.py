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
    # from pyaxidraw import axidraw
    from fake_ad import FakeAD

    # ad = axidraw.AxiDraw()
    ad = FakeAD()
    ad.interactive()
    if not ad.connect():
        return 1
    ad.options.speed_pendown = 80
    ad.options.speed_penup = 80
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    ad.penup()
    margin = 0.25

    W = 11
    H = 8.5

    SZ = 2
    exp = 2
    circle_centers = []
    circle_rs = []
    smaxr = 2
    rejections = 0
    rejections_thresh = 100
    absminr = 0.01
    for _ in trange(100_000):
        x = random.uniform(0, W)
        y = random.uniform(0, H)

        inside = False

        for idx, [cx, cy] in enumerate(circle_centers):
            cr = circle_rs[idx]
            if (x - cx) ** 2 + (y - cy) ** 2 < (cr) ** 2:
                inside = True
                break

        if not inside:
            # find max radius that doesn't collide
            closest = float("inf")
            for idx, [cx, cy] in enumerate(circle_centers):
                cr = circle_rs[idx]
                if (x - cx) ** 2 + (y - cy) ** 2 < (closest + cr) ** 2:
                    closest = math.sqrt((x - cx) ** 2 + (y - cy) ** 2) - cr

            closest = min(
                closest, x - margin, W - margin - x, y - margin, H - margin - y
            )
            r = closest

        if r < smaxr:
            rejections += 1

        if not inside and r > smaxr:
            circle_centers.append((x, y))
            circle_rs.append(r)

        if rejections > rejections_thresh:
            smaxr *= 0.99
            rejections = 0
            if smaxr < absminr:
                break
    for idx, [cx, cy] in enumerate(circle_centers):
        cr = circle_rs[idx]
        eps = 0.01
        steps = math.ceil(2 * math.pi * cr / eps)
        vertices = []
        for i in range(steps + 1):
            angle = 2 * math.pi * i / steps
            x = cx + cr * math.cos(angle)
            y = cy + cr * math.sin(angle)
            vertices.append((x, y))
        draw_polyline(ad, vertices)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
