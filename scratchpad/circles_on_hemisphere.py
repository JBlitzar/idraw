import numpy as np
from tqdm import trange
import math
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
    from pyaxidraw import axidraw
    # from fake_ad import FakeAD

    ad = axidraw.AxiDraw()
    # ad = FakeAD()
    ad.interactive()
    ad.options.speed_pendown = 80
    ad.options.speed_penup = 80
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    if not ad.connect():
        return 1

    ad.penup()



    N = 200
    R = 3

    circles = []
    for i in range(N):
        c = rUV()
        c = (c[0], c[1], c[2])#abs(c[2]))
        ang = random.random() * 0.3
        circles.append([c, ang])

    D, FOV = 10, math.radians(10)
    zmin = R * R / D

    points = []                 # list of visible polylines
    for c, ang in circles:
        ref = (0, 0, 1) if abs(c[2]) < 0.9 else (1, 0, 0)
        u = normalize(cross(c, ref))
        v = normalize(cross(c, u))
        cosine, sine = math.cos(ang), math.sin(ang)

        pts3, segments = [], 100
        for i in range(segments):
            phi = (i / segments) * 2 * math.pi
            cp, sp = math.cos(phi), math.sin(phi)
            pts3.append(tuple(R * (cosine * c[k] + sine * (cp * u[k] + sp * v[k]))
                              for k in range(3)))

        vis = [p[2] > zmin for p in pts3]
        xy = [proj(p, D, FOV) for p in pts3]
        xy = [(a[0] + 11 / 2, a[1] + 8.5 / 2) for a in xy]

        if all(vis):
            xy.append(xy[0]); vis.append(True)
        elif any(vis):
            k = vis.index(False)
            xy, vis = xy[k:] + xy[:k], vis[k:] + vis[:k]
        else:
            continue

        run = []
        for a, ok in zip(xy, vis):
            if ok:
                run.append(a)
            elif run:
                points.append(run); run = []
        if run:
            points.append(run)

    pts3, segments = [], 100
    for i in range(segments):
        phi = (i / segments) * 2 * math.pi
        cp, sp = math.cos(phi), math.sin(phi)
        pts3.append((R * cp, R * sp, zmin))

    xy = [proj(p, D, FOV) for p in pts3]
    xy.append(xy[0])
    xy = [(a[0] + 11 / 2, a[1] + 8.5 / 2) for a in xy]
    points.append(xy)



    for p in points:
        draw_polyline(ad, p)




    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
