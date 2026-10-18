from pathlib import Path

from PIL import Image


PAGE_WIDTH = 4.25
PAGE_HEIGHT = 5.5
IMAGE_HEIGHT = 5.0
SOURCE = Path(__file__).with_name("among.png")


def boundary_paths(image):
    image = image.convert("RGBA")
    background = Image.new("RGBA", image.size, "white")
    image = Image.alpha_composite(background, image).convert("RGB")
    pixels = image.load()
    width, height = image.size

    def color(x, y):
        if 0 <= x < width and 0 <= y < height:
            return pixels[x, y]
        return (255, 255, 255)

    paths = []
    for vertical in (False, True):
        across, along = (width, height) if vertical else (height, width)
        for fixed in range(across + 1):
            start = None
            for moving in range(along + 1):
                x, y = (fixed, moving) if vertical else (moving, fixed)
                edge = moving < along and (
                    color(x - 1, y) != color(x, y)
                    if vertical
                    else color(x, y - 1) != color(x, y)
                )
                if edge and start is None:
                    start = moving
                elif not edge and start is not None:
                    paths.append(
                        [(fixed, start), (fixed, moving)]
                        if vertical
                        else [(start, fixed), (moving, fixed)]
                    )
                    start = None
    return paths


def page_paths(image):
    width, height = image.size
    scale = IMAGE_HEIGHT / height
    left = (PAGE_WIDTH - width * scale) / 2
    top = (PAGE_HEIGHT - IMAGE_HEIGHT) / 2
    if left < 0 or top < 0:
        raise ValueError("Scaled image does not fit on the paper")
    return [
        [[left + x * scale + 4.25, top + y * scale + 5.5] for x, y in path]
        for path in boundary_paths(image)
    ]


def main():
    is_fake = False
    try:
        from pyaxidraw import axidraw
    except ImportError:
        from fake_ad import FakeAD

        is_fake = True

    with Image.open(SOURCE) as image:
        paths = page_paths(image)
        print(
            f"Canvas: {image.width} x {image.height} pixels, "
            f"{image.width * IMAGE_HEIGHT / image.height:g} x {IMAGE_HEIGHT:g} inches",
            flush=True,
        )
    print(f"Drawing {len(paths)} exact boundary segments.", flush=True)
    if is_fake:
        import turtle

        ad = FakeAD(screensize=(425, 550))
        ad.screen.setup(550, 700)
        ad.screen.setworldcoordinates(-35, -35, 460, 585)
        turtle.clear()
        ad._color = (0.7, 0.7, 0.7)
        ad.bbox(PAGE_WIDTH, PAGE_HEIGHT)
        ad._color = (0, 0, 0)
        print("FakeAD preview; gray rectangle is the paper.", flush=True)
    else:
        ad = axidraw.AxiDraw()
        print("Using real AxiDraw.", flush=True)
    ad.interactive()
    if not ad.connect():
        raise SystemExit("Could not connect to plotter!")
    for path in paths:
        ad.draw_path(path)
    ad.penup()
    ad.disconnect()


if __name__ == "__main__":
    main()
