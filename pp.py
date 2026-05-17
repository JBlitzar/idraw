import numpy as np
from scipy.spatial import cKDTree
import heapq
from tqdm import tqdm, trange


def greedy_linemerge_reorder_kdtree(paths, epsilon=0.01):
    def as_points(path):
        arr = np.asarray(path, dtype=float)
        if arr.size == 0:
            return arr.reshape(0, 2)
        arr = np.atleast_2d(arr)
        if arr.shape[1] != 2:
            raise ValueError("Each path must be (x, y)")
        return arr

    def dist(a, b):
        return float(np.linalg.norm(a - b))

    clean = [as_points(p) for p in paths]
    clean = [p for p in clean if len(p) > 0]
    if not clean:
        return []

    n = len(clean)

    # endpoints
    endpoints = np.zeros((2 * n, 2), dtype=float)
    meta = []

    for i, p in enumerate(clean):
        endpoints[2 * i] = p[0]
        endpoints[2 * i + 1] = p[-1]
        meta.append((i, 0))
        meta.append((i, 1))

    tree = cKDTree(endpoints)

    used = np.zeros(n, dtype=bool)

    # seed
    origin = np.zeros(2)
    seed_idx = np.argmin(np.linalg.norm(endpoints - origin, axis=1))
    seed_path, seed_end = meta[seed_idx]
    used[seed_path] = True

    first = clean[seed_path]
    if seed_end == 1:
        first = first[::-1].copy()

    ordered = [first]
    last_point = ordered[-1][-1]

    print("setup done... building heap")

    # ---- build initial heap of ALL candidates for first step ----
    # heap entries: (distance, endpoint_index)
    heap = []

    for i, pt in enumerate(endpoints):
        heapq.heappush(heap, (dist(last_point, pt), i))

    for _ in trange(n - 1):
        found = None

        while heap:
            _, idx = heapq.heappop(heap)
            path_id, is_end = meta[idx]

            if used[path_id]:
                continue

            found = (path_id, is_end)
            break

        if found is None:
            raise RuntimeError("No unused paths left (logic error or empty dataset)")

        path_id, is_end = found
        used[path_id] = True

        path = clean[path_id]

        if is_end == 1:
            path = path[::-1].copy()

        ordered.append(path)
        last_point = path[-1]

        # IMPORTANT: refresh heap for new anchor (cheap incremental rebuild)
        heap = []
        for i, pt in enumerate(endpoints):
            if not used[meta[i][0]]:
                heapq.heappush(heap, (dist(last_point, pt), i))

    # merge
    merged = []
    current = ordered[0].copy()

    for path in tqdm(ordered[1:], desc="Merging lines"):
        if dist(current[-1], path[0]) <= epsilon:
            if len(path) > 1:
                current = np.vstack([current, path[1:]])
        else:
            merged.append(current)
            current = path.copy()

    merged.append(current)
    return [p.tolist() for p in merged]
