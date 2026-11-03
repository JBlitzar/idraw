import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random
from pp import greedy_linemerge_reorder_kdtree


random.seed(4)


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    if len(vertices) >= 2:
        ad.draw_path([[x, y] for (x, y) in vertices])
    elif len(vertices) == 1:
        ad.moveto(vertices[0][0], vertices[0][1])

def rUV():
    z = random.random() * 2 - 1
    th = random.random() * 2 * math.pi
    r= math.sqrt(1-z*z)
    return (r*math.cos(th), z, r*math.sin(th))


def cross(a, b):
    return (a[1]*b[2] - a[2]*b[1],
            a[2]*b[0] - a[0]*b[2],
            a[0]*b[1] - a[1]*b[0])

def normalize(a):
    L = math.sqrt(a[0]**2 + a[1]**2 + a[2]**2)
    return (a[0]/L, a[1]/L, a[2]/L)

proj = lambda p, D, fov: (p[0] / ((D - p[2]) * math.tan(fov / 2)), p[1] / ((D - p[2]) * math.tan(fov / 2)))


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



    N = 100
    R = 4

    circles = []
    for i in range(N):
        c = rUV()
        c = (c[0], c[1], c[2])#abs(c[2]))
        ang = random.random() * 0.5
        circles.append([c, ang])

    points = []
    for c, ang in circles:

        ref = (0, 0, 1) if abs(c[2]) < 0.99 else (1, 0, 0)
        u = normalize(cross(c, ref))
        v = normalize(cross(c, u))

        points_3d = []
        segments = 100
        cosine = math.cos(ang)
        sine = math.sin(ang)

        for i in range(segments):
            phi = (i / segments) * 2 * math.pi
            cosPhi = math.cos(phi)
            sinPhi = math.sin(phi)

            x = cosine * c[0] + sine * (cosPhi * u[0] + sinPhi * v[0])
            y = cosine * c[1] + sine * (cosPhi * u[1] + sinPhi * v[1])
            z = cosine * c[2] + sine * (cosPhi * u[2] + sinPhi * v[2])


            points_3d.append((x * R, y * R, z * R))

        xy = [proj(p, D=10, fov=math.radians(10)) for p in points_3d]
        xy = [(a[0] + 11/2, a[1] + 8.5/2) for a in xy]
        points.append(xy)



    for p in points:
        draw_polyline(ad, p)




    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
