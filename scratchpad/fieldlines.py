import cv2
import numpy as np
from tqdm import trange
import math
from PIL import Image
import random
from pp import greedy_linemerge_reorder_kdtree


random.seed(43)


def draw_polyline(ad, vertices: list[tuple[float, float]]):
    if len(vertices) >= 2:
        ad.draw_path([[x, y] for (x, y) in vertices])


PAPER_WIDTH = 11
PAPER_HEIGHT = 8.5
MULT = 4
MARGIN = 0.25


def run(charges, strengths, angle_offsets):
    r = 0.1
    charges = np.asarray(charges, dtype=float)  # (M, 2)
    strengths = np.asarray(strengths, dtype=float)  # (M,)

    start_pts = []
    for idx in range(len(charges)):
        if strengths[idx] > 0:
            num = MULT * int(strengths[idx])
            offset = angle_offsets[idx]
            angs = np.arange(0, 2 * np.pi, 2 * np.pi / num) + offset
            pts = np.column_stack([
                charges[idx, 0] + r * np.cos(angs),
                charges[idx, 1] + r * np.sin(angs),
            ])
            start_pts.append(pts)

    if not start_pts:
        return []

    points = np.vstack(start_pts)  # (N, 2)
    N = len(points)

    active = np.ones(N, dtype=bool)
    deactivated_at = np.full(N, -1, dtype=int)
    all_positions = [points.copy()]

    max_steps = 1_000_000
    step = 0.005

    for step_idx in range(max_steps):
        if not active.any():
            break

        diff = points[:, None, :] - charges[None, :, :]  # (N, M, 2)
        r2 = (diff ** 2).sum(axis=2)  # (N, M)
        min_r2 = r2.min(axis=1)  # (N,)

        too_close = min_r2 < 0.005
        oob = ((points[:, 0] < MARGIN) | (points[:, 0] > PAPER_WIDTH - MARGIN) |
               (points[:, 1] < MARGIN) | (points[:, 1] > PAPER_HEIGHT - MARGIN))
        should_stop = too_close | oob

        newly_inactive = should_stop & active
        deactivated_at[newly_inactive] = step_idx
        active &= ~should_stop

        if not active.any():
            break

        r2_safe = np.maximum(r2, 1e-10)
        f = strengths[None, :] / r2_safe  # (N, M)
        vel = (f[..., None] * diff).sum(axis=1)  # (N, 2)
        speed = np.sqrt((vel ** 2).sum(axis=1))  # (N,)

        mask = active & (speed > 0)
        points[mask] += vel[mask] / speed[mask, None] * step

        all_positions.append(points.copy())

    all_positions = np.stack(all_positions)  # (n_steps+1, N, 2)
    n_total = len(all_positions)

    trails = []
    for i in range(N):
        end = deactivated_at[i] + 1 if deactivated_at[i] >= 0 else n_total
        trail = all_positions[:end, i]
        pts = [(float(p[0]), float(p[1])) for p in trail]
        while len(pts) > 1 and (pts[-1][0] < 0 or pts[-1][0] > PAPER_WIDTH or
                                pts[-1][1] < 0 or pts[-1][1] > PAPER_HEIGHT):
            pts.pop()
        trails.append(pts)

    return trails



def draw_circle(ad, cx, cy, radius, segments=36):
    pts = []
    for i in range(segments + 1):
        ang = 2 * math.pi * i / segments
        pts.append([cx + radius * math.cos(ang), cy + radius * math.sin(ang)])
    ad.draw_path(pts)


def count_endpoints(trails, charges):
    charges = np.asarray(charges, dtype=float)  # (M, 2)
    last_pts = np.array([t[-1] for t in trails if len(t) >= 2])  # (K, 2)
    if len(last_pts) == 0:
        return [0] * len(charges)
    diff = last_pts[:, None, :] - charges[None, :, :]  # (K, M, 2)
    r2 = (diff ** 2).sum(axis=2)  # (K, M)
    nearest = r2.argmin(axis=1)  # (K,)
    min_r2 = r2.min(axis=1)  # (K,)
    counts = np.zeros(len(charges), dtype=int)
    np.add.at(counts, nearest[min_r2 < 0.1], 1)
    return counts.tolist()


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


    charges = []
    num = 30

    for i in range(num):
        charges.append([random.random() * PAPER_WIDTH, random.random() * PAPER_HEIGHT])

    while True:
        strengths = [random.randint(-3, 3) for _ in range(num)]
        sum_pos = sum(s for s in strengths if s > 0)
        sum_neg = sum(abs(s) for s in strengths if s < 0)
        if sum_pos >= sum_neg:
            break

    # debug_r = 0.15
    # for idx, charge in enumerate(charges):
    #     # ad._color = "red" if strengths[idx] > 0 else "blue"
    #     draw_circle(ad, charge[0], charge[1], debug_r)
    # # ad._color = "black"

    best_trails = None
    best_score = float('inf')
    for attempt in trange(100):
        offsets = [random.uniform(0, 2*math.pi) for _ in charges]
        trails = run(charges, strengths, offsets)
        counts = count_endpoints(trails, charges)
        score = sum(abs(counts[j] - MULT * abs(strengths[j]))
                    for j in range(len(charges)) if strengths[j] < 0)
        if score < best_score:
            best_score = score
            best_trails = trails
        if score == 0:
            break

    print(f"Best score: {best_score}")
    for trail in best_trails:
        draw_polyline(ad, trail)






    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
