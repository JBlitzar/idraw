import numpy as np
from PIL import Image

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


img = Image.open("circle.jpg").convert("L")


IMG_WIDTH_CHARS = 50
IMG_HEIGHT_CHARS = int(img.size[1] / img.size[0] * IMG_WIDTH_CHARS * ar)
IMG_WIDTH_PX = IMG_WIDTH_CHARS * cell_w
IMG_HEIGHT_PX = IMG_HEIGHT_CHARS * cell_h
# print(IMG_WIDTH_CHARS, IMG_HEIGHT_CHARS)
img = img.resize((IMG_WIDTH_PX, IMG_HEIGHT_PX))

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
img = fmap(img, np.min(img), np.max(img), 100, 255)
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
