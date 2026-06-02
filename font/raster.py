from pathlib import Path

import freetype
import numpy as np

FONT_PATH = Path("GeistMono-Regular.ttf")
CELL_HEIGHT_PX = 20  # rasterize at this height; width derived from aspect ratio


def load_face(font_path: Path, cell_height_px: int) -> freetype.Face:
    """Load a FreeType face at the given pixel height."""
    face = freetype.Face(str(font_path))
    # Request monochrome/grayscale render at target height.
    # Width=0 → FreeType infers it from the font's own aspect ratio.
    face.set_pixel_sizes(0, cell_height_px)
    return face


def cell_dimensions(face: freetype.Face) -> tuple[int, int]:
    face.load_char("M", freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
    cell_w = face.glyph.advance.x >> 6
    metrics = face.size
    cell_h = (metrics.ascender - metrics.descender) >> 6  # descender is negative
    return cell_w, cell_h


def aspect_ratio(face: freetype.Face) -> float:
    """width / height of a single character cell."""
    w, h = cell_dimensions(face)
    return w / h


def rasterize_glyph(
    face: freetype.Face, char: str, cell_w: int, cell_h: int
) -> np.ndarray:
    """
    Render a single character into a (cell_h, cell_w) uint8 array.

    Uses FT_LOAD_RENDER with the default (anti-aliased) mode so the bitmap
    matches what a real renderer produces — important for SSIM matching.

    The glyph is placed at the correct baseline position; empty space
    (above ascender, below descender) is filled with 0 (black).
    """
    face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_NORMAL)
    glyph = face.glyph
    bitmap = glyph.bitmap

    canvas = np.zeros((cell_h, cell_w), dtype=np.uint8)

    if bitmap.width == 0 or bitmap.rows == 0:
        return canvas  # space / empty glyph

    # Baseline offset from top of cell
    ascender = face.size.ascender >> 6
    top = ascender - glyph.bitmap_top  # rows from top of cell to glyph top
    left = glyph.bitmap_left  # columns from left edge of cell

    src = np.array(bitmap.buffer, dtype=np.uint8).reshape(bitmap.rows, bitmap.width)

    # Clip to canvas bounds (some glyphs slightly exceed cell — rare but safe)
    src_r0 = max(0, -top)
    dst_r0 = max(0, top)
    src_c0 = max(0, -left)
    dst_c0 = max(0, left)
    rows = min(src.shape[0] - src_r0, cell_h - dst_r0)
    cols = min(src.shape[1] - src_c0, cell_w - dst_c0)

    if rows > 0 and cols > 0:
        canvas[dst_r0 : dst_r0 + rows, dst_c0 : dst_c0 + cols] = src[
            src_r0 : src_r0 + rows, src_c0 : src_c0 + cols
        ]

    return canvas


CODEPOINT_RANGES = [
    (0x0020, 0x007E),  # Basic ASCII printable
    # (0x2500, 0x257F),  # Box drawing
    # (0x2580, 0x259F),  # Block elements
    # (0x2800, 0x28FF),  # Braille patterns
]


def build_glyph_atlas(
    face: freetype.Face,
    cell_w: int,
    cell_h: int,
    codepoint_ranges=CODEPOINT_RANGES,
) -> dict[str, np.ndarray]:
    """
    Rasterize every character in the vocabulary that the font supports.

    Returns {char: uint8 array of shape (cell_h, cell_w)}.
    Characters not present in the font are silently skipped.
    """
    atlas: dict[str, np.ndarray] = {}
    for lo, hi in codepoint_ranges:
        for cp in range(lo, hi + 1):
            char = chr(cp)
            if face.get_char_index(cp) == 0 and cp != 0x0020:
                continue  # glyph not in font
            bmp = rasterize_glyph(face, char, cell_w, cell_h)
            atlas[char] = bmp
    return atlas


# ---------------------------------------------------------------------------
# Entry point / smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    face = load_face(FONT_PATH, CELL_HEIGHT_PX)
    cell_w, cell_h = cell_dimensions(face)
    ar = aspect_ratio(face)

    print(f"Cell size : {cell_w} × {cell_h} px")
    print(f"Aspect ratio (w/h): {ar:.4f}")

    atlas = build_glyph_atlas(face, cell_w, cell_h)
    print(f"Vocabulary size: {len(atlas)} glyphs")

    # Quick visual sanity check — print a few glyphs as ASCII shading
    for char in ["@", "#", "l", "q", " "]:
        if char not in atlas:
            print(f"  {repr(char):10s} — not in font")
            continue
        bmp = atlas[char]
        coverage = bmp.mean() / 255
        print(f"  {repr(char):10s}  coverage={coverage:.3f}  shape={bmp.shape}")
