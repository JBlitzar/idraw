import numpy as np
from PIL import Image
import os


def compose(colors):
    result = np.array([1.0, 1.0, 1.0])

    for color in colors:
        color = color.lstrip("#")
        rgb = np.array([int(color[i : i + 2], 16) for i in (0, 2, 4)]) / 255.0

        result *= rgb

    return tuple((result * 255).astype(np.uint8))


PALETTE = {
    "yellow": "#FEFF1B",
    "cyan": "#1ED4CE",
    "magenta": "#8e0db5",
    "black": "#000000",
}


combinations = []

values = list(PALETTE.values())

for i in range(1, 1 << len(values)):
    combo = [values[j] for j in range(len(values)) if i & (1 << j)]
    combinations.append(combo)


palette_colors = [compose(c) for c in combinations]

print(palette_colors)


flat_palette = []

for rgb in palette_colors:
    flat_palette.extend(rgb)


flat_palette += [0] * (256 * 3 - len(flat_palette))


palette_img = Image.new("P", (1, 1))
palette_img.putpalette(flat_palette)

img = (
    Image.open(os.path.join(os.path.dirname(__file__), "peppers.png"))
    .convert("RGB")
    .resize((100, 100))
)

result = img.quantize(
    palette=palette_img,
    dither=Image.FLOYDSTEINBERG,
)

result = result.convert("RGB")

result.save("out.png")
# generate a bitmask for each original color
masks = {name: np.zeros(result.size, dtype=bool) for name in PALETTE}
for name, hex_color in PALETTE.items():
    color = compose([hex_color])
    mask = np.all(np.array(result) == color, axis=-1)
    masks[name] = mask
# import cv2

# cv2.imwrite("mask_yellow.png", masks["cyan"].astype(np.uint8) * 255)
IMG_WIDTH_IN = 7
pix2in = IMG_WIDTH_IN / result.width
paper_size = (11, 8.5)
OFFSET = (
    paper_size[0] / 2 - (result.width * pix2in) / 2,
    paper_size[1] / 2 - (result.height * pix2in) / 2,
)


def main():
    from pyaxidraw import axidraw
    # from fake_ad import FakeAD

    ad = axidraw.AxiDraw()
    # ad = FakeAD()
    ad.interactive()
    ad.options.speed_pendown = 100
    ad.options.speed_penup = 100
    ad.options.pen_rate_lower = 100
    ad.options.pen_rate_raise = 100
    # ad.options.const_speed = True
    if not ad.connect():
        return 1

    ad.penup()
    for color in PALETTE:
        input(f"Load color {color}")
        mask = masks[color]
        for y in range(mask.shape[0]):
            for x in range(mask.shape[1]):
                if mask[y, x]:
                    ad.goto(x * pix2in + OFFSET[0], y * pix2in + OFFSET[1])
                    ad.pendown()
                    ad.penup()

    ad.penup()
    ad.goto(0, 0)
    ad.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
