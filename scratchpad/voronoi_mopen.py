import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random

random.seed(4)


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    eps = 0.01
    if len(vertices) >= 2:
        # ad.draw_path([[x, y] for (x, y) in vertices])
        ad.goto(vertices[0][0], vertices[0][1])
        ad.pendown()
        last = vertices[0]
        for x, y in vertices[1:]:
            if (x - last[0]) ** 2 + (y - last[1]) ** 2 > eps**2:
                ad.goto(x, y)
                last = (x, y)
        ad.penup()
    elif len(vertices) == 1:
        ad.moveto(vertices[0][0], vertices[0][1])


def main():
    from pyaxidraw import axidraw
    # from fake_ad import FakeAD

    ad = axidraw.AxiDraw()
    # ad = FakeAD()
    ad.interactive()
    ad.options.speed_pendown = 1
    ad.options.speed_penup = 50
    # ad.options.const_speed = True
    if not ad.connect():
        return 1

    ad.penup()

    R = 1.9
    W = 4.5
    H = 4.5
    center = (W / 2, H / 2)

    num_seeds = 30
    seeds = []
    while len(seeds) < num_seeds:
        x = random.uniform(0, W)
        y = random.uniform(0, H)
        if (x - center[0]) ** 2 + (
            y - center[1]
        ) ** 2 < R**2:  # later add poisson rejection if I want them spaced
            seeds.append((x, y))

    seeds = np.array(seeds)
    # voronoi fracture
    # for each voronoi mask, perform morpho open on it, and then draw the contours of the result with polyline
    px_per_in = 220
    img_w = int(W * px_per_in)
    img_h = int(H * px_per_in)

    x_coords = (np.arange(img_w) + 0.5) / px_per_in
    labels = np.empty((img_h, img_w), dtype=np.uint16)

    for py in trange(img_h, desc="Raster Voronoi"):
        y = (py + 0.5) / px_per_in
        dx2 = (seeds[:, 0, None] - x_coords[None, :]) ** 2
        dy2 = (seeds[:, 1] - y) ** 2
        labels[py, :] = np.argmin(dx2 + dy2[:, None], axis=0)

    domain = np.zeros((img_h, img_w), dtype=np.uint8)
    cv2.circle(
        domain,
        (int(center[0] * px_per_in), int(center[1] * px_per_in)),
        int(R * px_per_in),
        255,
        -1,
    )

    k = max(3, int(0.2 * px_per_in))
    if k % 2 == 0:
        k += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

    for i in trange(len(seeds), desc="Open + draw contours"):
        mask = np.where(labels == i, 255, 0).astype(np.uint8)
        mask = cv2.bitwise_and(mask, domain)
        opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(
            opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for c in contours:
            if len(c) < 2:
                continue

            pts = [(p[0][0] / px_per_in, p[0][1] / px_per_in) for p in c]
            if len(pts) >= 3:
                pts.append(pts[0])  # close loop

            draw_polyline(ad, pts)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
