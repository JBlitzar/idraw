import cv2
import random
import math
import fake_ad
import os

im = cv2.imread(os.path.join(os.path.dirname(__file__), "picture.png"))
if im is None:
    raise FileNotFoundError("Image not found")

# rgb decompose
# in the future do subtractive decomposition onto arbitrary palette
b, g, r = cv2.split(im)


IM_WIDTH_IN = 5
IM_HEIGHT_IN = IM_WIDTH_IN * im.shape[0] / im.shape[1]

PIX2IN = IM_WIDTH_IN / im.shape[1]

pen_width_in = 0.01  # this means that max darkness is this distance. Max lightness is infinite distance, can be estimated as 1 inch tho
white_distance_in = 0.08


def value_to_distance(value):
    t = value / 255.0
    t = t**3  # gamma
    return pen_width_in + t * (white_distance_in - pen_width_in)


def poisson_sample(darkness_mask):
    # get a random point on the image in imagespace
    # get distance from value in mask
    # See if any of the other points are within that distance, if so reject and try again
    # repeat until convergence
    # can use the law of large numbers: If thirty points are rejected in a row, we're probably done
    last_rejections = 0
    points = []
    i = 0
    while last_rejections < 30 and i < 10_000:
        x = random.uniform(0, im.shape[1])
        y = random.uniform(0, im.shape[0])
        value = darkness_mask[int(y), int(x)]
        distance = value_to_distance(value)
        if all(PIX2IN * math.hypot(px - x, py - y) >= distance for px, py in points):
            points.append((x, y))
            last_rejections = 0
        else:
            last_rejections += 1
        i += 1
        if i % 100 == 0:
            print(
                f"Poisson sampling: {len(points)} points, {last_rejections} rejections in a row"
            )

    return points


def draw_lattice(ad, points):
    # for all points that are voronoi neighbors, draw a line between them
    # aka delunay triangulation
    if not points:
        return

    rect = (0, 0, int(im.shape[1]), int(im.shape[0]))
    subdiv = cv2.Subdiv2D(rect)

    for x, y in points:
        try:
            subdiv.insert((float(x), float(y)))
        except cv2.error:
            continue

    triangles = subdiv.getTriangleList()

    def in_bounds(px, py):
        return 0 <= px < im.shape[1] and 0 <= py < im.shape[0]

    def near_point(px, py, eps=1.0):
        for x, y in points:
            if abs(px - x) <= eps and abs(py - y) <= eps:
                return True
        return False

    seen = set()

    lines = []
    for t in triangles:
        pts = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        if not all(in_bounds(px, py) for px, py in pts):
            continue

        for i in range(3):
            p1 = pts[i]
            p2 = pts[(i + 1) % 3]
            if not (near_point(p1[0], p1[1]) and near_point(p2[0], p2[1])):
                continue

            key = tuple(
                sorted(
                    (
                        (round(p1[0], 3), round(p1[1], 3)),
                        (round(p2[0], 3), round(p2[1], 3)),
                    )
                )
            )
            if key in seen:
                continue
            seen.add(key)

            lines.append(
                ((p1[0] * PIX2IN, p1[1] * PIX2IN), (p2[0] * PIX2IN, p2[1] * PIX2IN))
            )

    return lines


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
    ad.options.speed_pendown = 80
    ad.options.speed_penup = 80
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    if not ad.connect():
        return 1

    ad.penup()

    # mask_colors = {"blue": b, "green": g, "red": r}
    mask_colors = {"black": cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)}
    for color, mask in mask_colors.items():
        ad._color = color
        print(f"Processing {color} channel...")
        points = poisson_sample(mask)
        lines = draw_lattice(ad, points)
        for p1, p2 in lines:
            draw_polyline(ad, [p1, p2])

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
