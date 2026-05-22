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


def _mises(k, alpha):
    # t = np.random.uniform(0, 2 * np.pi)
    # return np.e ** (k * np.cos(t - alpha))
    theta = np.random.vonmises(mu=alpha, kappa=k)
    theta %= 2 * np.pi
    return theta


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    if len(vertices) >= 2:
        ad.draw_path([[x, y] for (x, y) in vertices])
    elif len(vertices) == 1:
        ad.moveto(vertices[0][0], vertices[0][1])


opensimplex.seed(42)


width, height = int(10.5 * 10), int(8 * 10)
scale = 0.1
WIDTH_IN = 10.5
paper_size = (11, 8.5)
PIX2IN = WIDTH_IN / width
OFFSET = (
    0.125 / 2 + (paper_size[0] - width * PIX2IN) / 2,
    0.125 / 4 + (paper_size[1] - height * PIX2IN) / 2,
)


noise_array = np.zeros((height, width))
# populate
for y in range(height):
    for x in range(width):
        noise_array[y][x] = (
            (opensimplex.noise2(x * scale, y * scale) / 2 + 0.5) ** 1.3 * 0.2 / PIX2IN
        )


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

    pos = (0, 0)
    i = 0
    max_i = 100_000
    ad.goto(pos[0] * PIX2IN + OFFSET[0], pos[1] * PIX2IN + OFFSET[1])
    # ad.pendown()
    path = []
    last_angle = 0
    while True:
        x = pos[0] * PIX2IN + OFFSET[0]
        y = pos[1] * PIX2IN + OFFSET[1]
        # ad.goto(x, y)
        path.append((x, y))
        print(f"noise: {noise_array[int(pos[1])][int(pos[0])]}")
        ang = _mises(0.7, last_angle)

        last_angle = ang
        new_pos = (
            pos[0] + math.cos(ang) * noise_array[int(pos[1])][int(pos[0])],
            pos[1] + math.sin(ang) * noise_array[int(pos[1])][int(pos[0])],
        )
        new_pos = (
            max(0, min(width - 1, new_pos[0])),
            max(0, min(height - 1, new_pos[1])),
        )
        pos = new_pos

        i += 1
        if i % 100 == 0:
            print(f"Step {i}, position: {pos}")
        if i >= max_i:
            break

    ad.penup()
    ad.polyline(path)
    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# # Visualize the result
# plt.imshow(noise_array, cmap='gray')
# plt.show()
