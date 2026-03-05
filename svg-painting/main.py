import svgelements
import numpy as np

SVG_DPI = 96.0  # SVG spec default

# ai function btw
def svg_to_rasterized_paths(svg_file, points_per_inch=10):
    samples_per_unit = points_per_inch / SVG_DPI
    svg = svgelements.SVG.parse(svg_file)
    
    rasterized = []

    for element in svg.elements():
        if not isinstance(element, svgelements.Shape):
            continue

        path = svgelements.Path(element)
        if not path:
            continue


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



paths = svg_to_rasterized_paths("my_file.svg", samples_per_unit=20)
for i, path in enumerate(paths):
    print(f"Path {i}: {len(path)} points")
    print(f"  First point: {path[0]}")
    print(f"  Last point:  {path[-1]}")