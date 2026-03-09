from svgpathtools import svg2paths
import numpy as np

IS_FAKE = False
try:
    from pyaxidraw import axidraw
except ImportError:
    from fake_ad import FakeAD

    IS_FAKE = True

import math
import time

# from fake_ad import FakeAD
import os
import threading

INK_POS = (12, 2)

ad = None
if IS_FAKE:
    ad = FakeAD(speed=5, instant=True)
else:
    ad = axidraw.AxiDraw()  # FakeAD(speed=5, instant=True)

ad.interactive()

connected = ad.connect()
ad.options.model = 2
ad.options.clip_to_page = False
ad.options.pen_pos_up = 100
ad.options.pen_pos_down = 0
ad.options.speed_pendown = 100
ad.options.speed_penup = 100
ad.update()


def dip():
    ad.goto(INK_POS[0], INK_POS[1])
    ad.pendown()
    ad.penup()


SVG_DPI = 96.0  # SVG spec default


TIMELAPSE = True
out_dir = os.path.join(
    os.path.dirname(__file__), "timelapse", time.strftime("%Y%m%d_%H%M%S")
)


def start_timelapse(interval_ms=1000):
    if not TIMELAPSE:
        return

    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "frame%06d.jpg")
    cmd = f'(rpicam-still -n --timeout 0 --timelapse {interval_ms} -o "{out}" || libcamera-still -n --timeout 0 --timelapse {interval_ms} -o "{out}")'
    threading.Thread(target=lambda: os.system(cmd), daemon=True).start()


def stop_timelapse():
    if not TIMELAPSE:
        return
    os.system("pkill -INT rpicam-still")
    os.system("pkill -INT libcamera-still")
    os.system(
        f"ffmpeg -y -framerate 30 -pattern_type glob -i '{out_dir}/*.jpg' -c:v libx264 -pix_fmt yuv420p timelapse.mp4"
    )


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


paths = svg_to_rasterized_paths("wb.svg", points_per_inch=35)


if not connected:
    print("Could not connect to plotter!")
    exit(1)

ad.penup()

start_timelapse()


ad.options.clip_to_page = False

OFFSET = (0.6, 0)  # (2.25,2.5)
SCALE = 1.2
for i, path in enumerate(paths[::-1]):
    print(path)
    dip()
    ad.goto(path[0][0] * SCALE + OFFSET[0], path[0][1] * SCALE + OFFSET[1])
    ad.pendown()
    for x, y in path:
        ad.goto(x * SCALE + OFFSET[0], y * SCALE + OFFSET[1])
    ad.penup()

    # print(f"Path {i}: {len(path)} points")
    # print(f"  First point: {path[0]}")
    # print(f"  Last point:  {path[-1]}")

ad.penup()
ad.goto(0, 0)
ad.disconnect()

stop_timelapse()


os.system("axi off")
print("Done!")
os.system('curl -d "done!!" ntfy.sh/jb_pp_109188f37776d45aee070634901e480c')
