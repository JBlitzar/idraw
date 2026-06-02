import numpy as np
from PIL import Image, ImageOps

from raster import (
    CELL_HEIGHT_PX,
    FONT_PATH,
    aspect_ratio,
    build_glyph_atlas,
    cell_dimensions,
    load_face,
)

face = load_face(FONT_PATH, CELL_HEIGHT_PX)

cell_w, cell_h = cell_dimensions(face)
atlas = build_glyph_atlas(face, cell_w, cell_h)
atlas = {char: 255 - bmp for char, bmp in atlas.items()}
ar = aspect_ratio(face)

# print(cell_w, cell_h)


# img = Image.open("fingerprint.jpg").convert("L")
img = ImageOps.invert(Image.open("sg.png").convert("L"))


IMG_WIDTH_CHARS = 100
IMG_HEIGHT_CHARS = int(img.size[1] / img.size[0] * IMG_WIDTH_CHARS * ar)
IMG_WIDTH_PX = IMG_WIDTH_CHARS * cell_w
IMG_HEIGHT_PX = IMG_HEIGHT_CHARS * cell_h
# print(IMG_WIDTH_CHARS, IMG_HEIGHT_CHARS)
img = img.resize((IMG_WIDTH_PX, IMG_HEIGHT_PX))
img = ImageOps.equalize(img)

# Find the brightness range the atlas can represent
char_means = {char: atlas[char].mean() for char in atlas}
atlas_min = min(char_means.values())
atlas_max = max(char_means.values())
print(f"atlas min, max: {atlas_min}, {atlas_max}")
print("space:", char_means[" "])
print("@:", char_means["@"])


def fmap(v, vmin, vmax, out_min, out_max):
    return (v - vmin) / (vmax - vmin) * (out_max - out_min) + out_min


img = np.array(img).astype(np.float32)
img = fmap(img, np.min(img), np.max(img), 0, 255)
print(img)
img = Image.fromarray(img.astype(np.uint8))
print(np.array(img))


# img.save("mountain_atlas.jpg")


# print(
#     np.array(img.crop((cell_w * 200, cell_h * 200, cell_w * 201, cell_h * 201))).mean()
# )
# print(atlas[" "].mean())
# print(atlas["@"].mean())

# split into cells for size
cells = []
for y in range(IMG_HEIGHT_CHARS):
    for x in range(IMG_WIDTH_CHARS):
        cell = np.array(
            img.crop((x * cell_w, y * cell_h, (x + 1) * cell_w, (y + 1) * cell_h))
        )
        cells.append(cell)
    cells.append("<newline>")


def criterion(cell, atlas_char):
    diff = cell.astype(np.int32) - atlas_char.astype(np.int32)
    return np.mean(diff**2)


# def criterion(cell, atlas_char):
#     cell_norm = cell.astype(np.float32) - cell.mean()
#     atlas_norm = atlas_char.astype(np.float32) - atlas_char.mean()
#     diff = cell_norm - atlas_norm
#     return np.mean(diff**2)


rstr = ""
for cell in cells:
    if type(cell) == str and cell == "<newline>":
        rstr += "\n"
        continue

    # find atlas char with lowest error
    best_char = "?"
    best_error = float("inf")
    for atlas_char in atlas.keys():
        bitmap = atlas[atlas_char]

        error = criterion(cell, bitmap)
        if error < best_error:
            best_char = atlas_char
            best_error = error
    rstr += best_char

print(rstr)
rstr = rstr.replace("\n", "")
# render image
img = Image.new("L", (IMG_WIDTH_PX, IMG_HEIGHT_PX))
for y in range(IMG_HEIGHT_CHARS):
    for x in range(IMG_WIDTH_CHARS):
        cell = np.array(
            img.crop((x * cell_w, y * cell_h, (x + 1) * cell_w, (y + 1) * cell_h))
        )
        atlas_char = rstr[y * IMG_WIDTH_CHARS + x]
        bitmap = atlas[atlas_char]
        img.paste(Image.fromarray(bitmap), (x * cell_w, y * cell_h))
img.save("output.png")


import svgwrite
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

# --- SVG export ---
# 8.5x11 landscape in mm, converted to px at 96dpi
PAGE_W_MM = 279.4  # 11"
PAGE_H_MM = 215.9  # 8.5"
MM_PER_PX = 25.4 / 96

# Load font for vector outlines
tt_font = TTFont(FONT_PATH)
glyph_set = tt_font.getGlyphSet()
cmap = tt_font.getBestCmap()
units_per_em = tt_font["head"].unitsPerEm

# Scale factor: map font UPM to cell_h in px, then to mm
px_per_unit = cell_h / units_per_em
mm_per_unit = px_per_unit * MM_PER_PX * 0.8


# ASCII art dimensions in mm
art_w_mm = IMG_WIDTH_CHARS * cell_w * MM_PER_PX
art_h_mm = IMG_HEIGHT_CHARS * cell_h * MM_PER_PX

# Center on page
origin_x = (PAGE_W_MM - art_w_mm) / 2
origin_y = (PAGE_H_MM - art_h_mm) / 2

dwg = svgwrite.Drawing(
    "output.svg",
    size=(f"{PAGE_W_MM}mm", f"{PAGE_H_MM}mm"),
    viewBox=f"0 0 {PAGE_W_MM} {PAGE_H_MM}",
)

lines = rstr  # rstr still has newlines stripped; rebuild from grid
char_grid = [
    rstr[y * IMG_WIDTH_CHARS + x]
    for y in range(IMG_HEIGHT_CHARS)
    for x in range(IMG_WIDTH_CHARS)
]

for y in range(IMG_HEIGHT_CHARS):
    for x in range(IMG_WIDTH_CHARS):
        char = char_grid[y * IMG_WIDTH_CHARS + x]
        if char == " ":
            continue

        codepoint = ord(char)
        if codepoint not in cmap:
            continue
        glyph_name = cmap[codepoint]
        if glyph_name not in glyph_set:
            continue

        # Cell top-left in mm
        cell_x_mm = origin_x + x * cell_w * MM_PER_PX
        cell_y_mm = origin_y + y * cell_h * MM_PER_PX

        # Get glyph outline as SVG path
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        path_data = pen.getCommands()

        if not path_data:
            continue

        # Font coordinates: origin at baseline, y-up. SVG is y-down.
        # Translate so glyph sits in cell: baseline at cell bottom minus descender.
        metrics = glyph_set[glyph_name]
        baseline_y_mm = cell_y_mm + cell_h * MM_PER_PX  # bottom of cell

        # Transform: scale, flip y, translate to cell position
        transform = (
            f"translate({cell_x_mm},{baseline_y_mm}) "
            f"scale({mm_per_unit},{-mm_per_unit})"
        )

        dwg.add(
            dwg.path(
                d=path_data,
                transform=transform,
                fill="none",
                stroke="black",
                stroke_width="0.2mm",
            )
        )

dwg.save()
print("Saved output.svg")
