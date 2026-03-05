from svgpathtools import svg2paths
import numpy as np

# from pyaxidraw import axidraw
import math
import time
from fake_ad import FakeAD
import os

INK_POS = (12, 2)


ad = FakeAD(speed=5, instant=False)  # axidraw.AxiDraw()

ad.interactive()

connected = ad.connect()
ad.options.model = 2
ad.options.clip_to_page = False
ad.options.pen_pos_up = 100
ad.options.pen_pos_down = 0
ad.update()


def dip():
    ad.goto(INK_POS[0], INK_POS[1])
    ad.pendown()
    ad.penup()


SVG_DPI = 96.0  # SVG spec default


# ai function btw
def svg_to_rasterized_paths(svg_file, points_per_inch=10):
    os.chdir(os.path.dirname(__file__))
    samples_per_unit = points_per_inch / SVG_DPI
    paths, _ = svg2paths(svg_file)

    rasterized = []
    for path in paths:
        length = path.length()
        if length == 0:
            continue
        num_samples = max(2, int(length * samples_per_unit))
        points = []
        for i in range(num_samples + 1):
            t = i / num_samples
            pt = path.point(t)
            x_inches = pt.real / SVG_DPI
            y_inches = pt.imag / SVG_DPI
            points.append((x_inches, y_inches))
        rasterized.append(points)
    return rasterized


paths = svg_to_rasterized_paths("kafka.svg", points_per_inch=35)


if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.penup()


ad.options.clip_to_page = False


for i, path in enumerate(paths):
    print(path)
    dip()
    ad.goto(path[0][0], path[0][1])
    ad.pendown()
    for x, y in path:
        ad.goto(x, y)
    ad.penup()

    # print(f"Path {i}: {len(path)} points")
    # print(f"  First point: {path[0]}")
    # print(f"  Last point:  {path[-1]}")

ad.penup()
ad.goto(0, 0)
ad.disconnect()


os.system("axi off")
print("Done!")
# os.system('curl -d "done!!" ntfy.sh/jb_pp_109188f37776d45aee070634901e480c')
