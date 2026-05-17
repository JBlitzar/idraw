import cv2
import random
import math
import fake_ad
import os
import numpy as np
from pp import greedy_linemerge_reorder_kdtree
from tqdm import tqdm


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return np.array(
        [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float32
    )


im = cv2.imread(os.path.join(os.path.dirname(__file__), "mountain.jpg"))
if im is None:
    raise FileNotFoundError("Image not found")

b, g, r = cv2.split(im)

IM_WIDTH_IN = 10
IM_HEIGHT_IN = IM_WIDTH_IN * im.shape[0] / im.shape[1]

PIX2IN = IM_WIDTH_IN / im.shape[1]

pen_width_in = 0.03
white_distance_in = 0.25


def value_to_distance(value):
    t = value / 255.0
    t = t**3
    return pen_width_in + t * (white_distance_in - pen_width_in)


def gaussian_blur(mask):
    return cv2.GaussianBlur(mask, (0, 0), 6)


def subtractive_masks(image, PALETTE):
    img = image.astype(np.float32)

    # OpenCV uses BGR, convert palette to BGR too
    palette = {name: hex_to_rgb(hex_color)[::-1] for name, hex_color in PALETTE.items()}

    h, w, _ = img.shape

    masks = {name: np.zeros((h, w), dtype=np.float32) for name in PALETTE}

    # compute distances to each palette color
    for name, color in palette.items():
        diff = img - color  # broadcast over image
        dist = np.linalg.norm(diff, axis=2)

        masks[name] = dist

    # convert distances → weights (inverse distance)
    inv = {k: 1.0 / (v + 1e-6) for k, v in masks.items()}
    total = sum(inv.values())

    for k in inv:
        inv[k] /= total  # normalize to sum=1

    # optional: scale to 0–255 masks
    for k in inv:
        inv[k] = (inv[k] * 255).astype(np.uint8)

    return inv


def poisson_sample(darkness_mask):
    # darkness_mask = gaussian_blur(darkness_mask)

    h, w = darkness_mask.shape
    cell_size = pen_width_in / PIX2IN
    grid_w = int(w / cell_size) + 1
    grid_h = int(h / cell_size) + 1
    grid = [[None for _ in range(grid_w)] for _ in range(grid_h)]

    def insert(px, py):
        gx = int(px / cell_size)
        gy = int(py / cell_size)
        grid[gy][gx] = (px, py)

    def neighbors(px, py):
        gx = int(px / cell_size)
        gy = int(py / cell_size)
        for j in range(max(0, gy - 2), min(grid_h, gy + 3)):
            for i in range(max(0, gx - 2), min(grid_w, gx + 3)):
                p = grid[j][i]
                if p is not None:
                    yield p

    points = []

    attempts = 0
    max_attempts = w * h * 2

    while attempts < max_attempts:
        x = random.uniform(0, w)
        y = random.uniform(0, h)
        value = darkness_mask[int(y), int(x)]
        distance = value_to_distance(value)

        ok = True
        for px, py in neighbors(x, y):
            if PIX2IN * math.hypot(px - x, py - y) < distance:
                ok = False
                break

        if ok:
            points.append((x, y))
            insert(x, y)

        attempts += 1

    return points


def relax_points(points, mask, iterations=10):
    h, w = mask.shape
    grad = cv2.Sobel(mask, cv2.CV_32F, 1, 1, ksize=3)

    for _ in range(iterations):
        if not points:
            return points

        subdiv = cv2.Subdiv2D((0, 0, w, h))
        for x, y in points:
            x = min(max(float(x), 1e-3), w - 1e-3)
            y = min(max(float(y), 1e-3), h - 1e-3)
            subdiv.insert((x, y))

        facets, centers = subdiv.getVoronoiFacetList([])

        new_points = []
        for i, facet in enumerate(facets):
            pts = np.array(facet, dtype=np.float32)
            c = np.mean(pts, axis=0)
            if 0 <= c[0] < w and 0 <= c[1] < h:
                mx, my = int(c[0]), int(c[1])
                g = grad[my, mx] if 0 <= mx < w and 0 <= my < h else 0
                alpha = max(0.2, 1.0 - g / 255.0)
                px, py = points[i]
                nx = px * (1 - alpha) + c[0] * alpha
                ny = py * (1 - alpha) + c[1] * alpha
                new_points.append((nx, ny))
            else:
                new_points.append(points[i])

        points = new_points

    return points


def draw_lattice(ad, points):
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

    seen = set()

    lines = []
    for t in triangles:
        pts = [(t[0], t[1]), (t[2], t[3]), (t[4], t[5])]
        if not all(in_bounds(px, py) for px, py in pts):
            continue

        for i in range(3):
            p1 = pts[i]
            p2 = pts[(i + 1) % 3]

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

            p1x, p1y = p1
            p2x, p2y = p2

            dx = (p1x - p2x) * PIX2IN
            dy = (p1y - p2y) * PIX2IN
            length = math.hypot(dx, dy)

            if length < 0.03 or length > 0.3:
                continue

            lines.append(
                ((p1[0] * PIX2IN, p1[1] * PIX2IN), (p2[0] * PIX2IN, p2[1] * PIX2IN))
            )

    return lines


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    if len(vertices) >= 2:
        ad.draw_path([[x, y] for (x, y) in vertices])
    elif len(vertices) == 1:
        ad.moveto(vertices[0][0], vertices[0][1])


def followCanny(x, y):
    points = []
    h, w = edges.shape
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if edges[cy, cx] == 0:
            continue
        edges[cy, cx] = 0
        points.append((cx, cy))
        for dydx in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            dx, dy = dydx
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and edges[ny, nx] != 0:
                stack.append((nx, ny))
                break

    pts = np.array(points, dtype=np.float32).reshape(-1, 1, 2)
    simplified = cv2.approxPolyDP(pts, epsilon=1.5, closed=False)
    simplified = simplified.reshape(-1, 2)

    ad.goto(
        simplified[0][0] * pix2in + OFFSET[0], simplified[0][1] * pix2in + OFFSET[1]
    )
    ad.pendown()
    for p in simplified[1:]:
        ad.goto(p[0] * pix2in + OFFSET[0], p[1] * pix2in + OFFSET[1])
    ad.penup()
    print(".")


def followAllCanny():
    h, w = edges.shape
    for y in range(h):
        for x in range(w):
            if edges[y, x] != 0:
                followCanny(x, y)


followAllCanny()


def main():
    from fake_ad import FakeAD

    ad = FakeAD()
    ad.interactive()
    ad.options.speed_pendown = 80
    ad.options.speed_penup = 80
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    if not ad.connect():
        return 1

    ad.penup()

    # PALETTE = {
    #     "yellow": "#FEFF1B",
    #     "cyan": "#1ED4CE",
    #     "magenta": "#8e0db5",
    #     "black": "#000000",
    # }

    # mask_colors = subtractive_masks(im, PALETTE)

    paper_w = 11
    paper_h = 8.5
    offset = (paper_w - IM_WIDTH_IN) / 2, (paper_h - IM_HEIGHT_IN) / 2

    mask_colors = {
        "black": cv2.convertScaleAbs(
            cv2.equalizeHist(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)), alpha=1.5, beta=0
        )
    }
    for color, mask in mask_colors.items():
        ad._color = color
        print(f"Processing {color} channel...")
        points = poisson_sample(mask)
        print(f"Sampled {len(points)} points. Relaxing...")
        points = relax_points(points, mask, iterations=10)
        print("Relaxed. Drawing lattice...")
        lines = draw_lattice(ad, points)
        print(f"Line sort/merging... ({len(lines)} lines)")
        lines = greedy_linemerge_reorder_kdtree(lines)
        print(f"Drawing polyline... {len(lines)} lines")
        # print(lines[:5])
        for l in tqdm(lines, desc=f"Drawing {color} lines"):
            l = [(x + offset[0], y + offset[1]) for (x, y) in l]
            draw_polyline(ad, l)
        print(f"Done {color} channel.")

    edges = cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 100, 200)

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
