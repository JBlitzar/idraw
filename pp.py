import numpy as np


def greedy_linemerge_reorder_2opt(paths, epsilon=0.01):
    # Each path is a list of (x, y) points
    # We want to reorder the paths to minimize the total travel distance
    # can merge if endpoints are within eps of each other

    # returns: a list of merged paths
    def as_points(path):
        arr = np.asarray(path, dtype=float)
        if arr.size == 0:
            return arr.reshape(0, 2)
        arr = np.atleast_2d(arr)
        if arr.shape[1] != 2:
            raise ValueError("Each path must be a sequence of (x, y) points")
        return arr

    def d(a, b):
        return float(np.linalg.norm(a - b))

    clean = [as_points(p) for p in paths]
    clean = [p for p in clean if len(p) > 0]
    if not clean:
        return []

    # Greedy ordering by nearest endpoint, choosing orientation per path.
    remaining = list(range(len(clean)))
    origin = np.zeros(2, dtype=float)

    seed = min(
        remaining,
        key=lambda i: min(d(clean[i][0], origin), d(clean[i][-1], origin)),
    )
    first = clean[seed]
    if d(first[-1], origin) < d(first[0], origin):
        first = first[::-1].copy()

    ordered = [first]
    remaining.remove(seed)

    while remaining:
        end_pt = ordered[-1][-1]
        best_idx = None
        best_path = None
        best_cost = None

        for idx in remaining:
            path = clean[idx]
            cost_forward = d(end_pt, path[0])
            cost_reverse = d(end_pt, path[-1])
            if cost_reverse < cost_forward:
                oriented = path[::-1].copy()
                cost = cost_reverse
            else:
                oriented = path.copy()
                cost = cost_forward

            if best_cost is None or cost < best_cost - 1e-12:
                best_idx = idx
                best_path = oriented
                best_cost = cost

        ordered.append(best_path)
        remaining.remove(best_idx)

    # 2-opt improvement: reverse subsequences when it reduces travel distance.
    n = len(ordered)
    if n > 2:
        improved = True
        while improved:
            improved = False
            best_delta = 0.0
            best_i = None
            best_k = None

            for i in range(n - 1):
                for k in range(i + 1, n):
                    old_cost = 0.0
                    new_cost = 0.0

                    if i > 0:
                        old_cost += d(ordered[i - 1][-1], ordered[i][0])
                        new_cost += d(ordered[i - 1][-1], ordered[k][-1])

                    if k < n - 1:
                        old_cost += d(ordered[k][-1], ordered[k + 1][0])
                        new_cost += d(ordered[i][0], ordered[k + 1][0])

                    delta = new_cost - old_cost
                    if delta < best_delta - 1e-12:
                        best_delta = delta
                        best_i = i
                        best_k = k

            if best_i is not None:
                ordered[best_i : best_k + 1] = [
                    p[::-1].copy() for p in ordered[best_i : best_k + 1][::-1]
                ]
                improved = True

    # Merge adjacent paths whose endpoints are close enough.
    merged = []
    current = ordered[0].copy()
    for path in ordered[1:]:
        if d(current[-1], path[0]) <= epsilon:
            if len(path) > 1:
                current = np.vstack([current, path[1:]])
        else:
            merged.append(current)
            current = path.copy()
    merged.append(current)

    return [p.tolist() for p in merged]
