"""Generate the Rang repository logo as an 8-bit Persian-style central medallion.

This script recreates the chunky pixel medallion logo as deterministic pixel art.
It draws a 25x25 pixel matrix and enlarges it with nearest-neighbor scaling so
it stays crisp at any output size.

Examples
--------
python tools/make_logo.py
python tools/make_logo.py --output logo/rang_pixel_medallion_logo.png --size 1024
python tools/make_logo.py --output cache/rang_logo_preview.png --size 1024 --background gray
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageColor, ImageDraw

try:
    from colorlib import REPO_ROOT  # type: ignore
except Exception:  # pragma: no cover - fallback outside the repo
    REPO_ROOT = Path(__file__).resolve().parent

GRID = (
    ".........................",
    "......KKKKKKKKKKKKK......",
    ".....KYYYYBBBBBYYYYK.....",
    "....KYYYYBBBOBBBYYYYK....",
    "...KYGGGGGBOOOBGGGGGYK...",
    "..KYGGGDDGGBOBGGDDGGGYK..",
    ".KYYGGODDGGBPBGGDDOGGYYK.",
    ".KYYGOOODPPPPPPPDOOOGYYK.",
    ".KYYGGODYPPMMMPPYDOGGYYK.",
    ".KYBGGGPPPPMCMPPPPGGGBYK.",
    ".KBBBGGPPPMMCMMPPPGGBBBK.",
    ".KBBOBBPMMMMYMMMMPBBOBBK.",
    ".KBOOOPPMCCYYYCCMPPOOOBK.",
    ".KBBOBBPMMMMYMMMMPBBOBBK.",
    ".KBBBGGPPPMMCMMPPPGGBBBK.",
    ".KYBGGGPPPPMCMPPPPGGGBYK.",
    ".KYYGGODYPPMMMPPYDOGGYYK.",
    ".KYYGOOODPPPPPPPDOOOGYYK.",
    ".KYYGGODDGGBPBGGDDOGGYYK.",
    "..KYGGGDDGGBOBGGDDGGGYK..",
    "...KYGGGGGBOOOBGGGGGYK...",
    "....KYYYYBBBOBBBYYYYK....",
    ".....KYYYYBBBBBYYYYK.....",
    "......KKKKKKKKKKKKK......",
    ".........................",
)

PALETTE = {
    ".": (0, 0, 0, 0),
    "K": (0, 0, 0, 255),
    "Y": ImageColor.getrgb("#F5C431") + (255,),
    "B": ImageColor.getrgb("#243CC4") + (255,),
    "G": ImageColor.getrgb("#159358") + (255,),
    "D": ImageColor.getrgb("#0B6B3C") + (255,),
    "O": ImageColor.getrgb("#F55B0E") + (255,),
    "P": ImageColor.getrgb("#FF1E82") + (255,),
    "M": ImageColor.getrgb("#B3004C") + (255,),
    "C": ImageColor.getrgb("#21C1DC") + (255,),
}

DEFAULT_OUTPUT_PATH = Path(REPO_ROOT) / "logo" / "rang_pixel_medallion_logo.png"


def validate_grid(grid: Iterable[str]) -> None:
    """Validate that the pixel grid is rectangular and uses known symbols."""
    rows = list(grid)
    if not rows:
        raise ValueError("GRID cannot be empty")

    width = len(rows[0])
    for row in rows:
        if len(row) != width:
            raise ValueError("All rows in GRID must have the same width")
        unknown = set(row) - set(PALETTE)
        if unknown:
            raise ValueError(f"GRID contains unknown symbols: {sorted(unknown)}")


validate_grid(GRID)


def make_background(size: int, mode: str) -> Image.Image:
    """Create the requested background image."""
    if mode == "transparent":
        return Image.new("RGBA", (size, size), (255, 255, 255, 0))

    if mode == "gray":
        img = Image.new("RGBA", (size, size), ImageColor.getrgb("#6E6E6E") + (255,))
        draw = ImageDraw.Draw(img)
        # soft vignette with concentric translucent circles
        center = size / 2
        max_radius = size * 0.48
        for step in range(28, -1, -1):
            radius = max_radius * (step / 28)
            alpha = int(7 + (28 - step) * 2.4)
            box = (
                center - radius,
                center - radius,
                center + radius,
                center + radius,
            )
            draw.ellipse(box, fill=(50, 50, 50, alpha))
        return img

    raise ValueError("background must be 'transparent' or 'gray'")


def render_base_pixel_art() -> Image.Image:
    """Render the medallion as a low-resolution RGBA image."""
    height = len(GRID)
    width = len(GRID[0])
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    pixels = image.load()

    for y, row in enumerate(GRID):
        for x, symbol in enumerate(row):
            pixels[x, y] = PALETTE[symbol]

    return image


def upscale_logo(pixel_art: Image.Image, size: int) -> Image.Image:
    """Upscale the low-resolution pixel art while keeping crisp edges."""
    return pixel_art.resize((size, size), Image.Resampling.NEAREST)


def composite_logo(background: Image.Image, logo: Image.Image) -> Image.Image:
    """Center the logo onto the background image."""
    out = background.copy()
    out.alpha_composite(logo, (0, 0))
    return out


def save_logo(output_path: Path, size: int, background: str) -> Path:
    """Build and save the logo PNG."""
    pixel_art = render_base_pixel_art()
    logo = upscale_logo(pixel_art, size)
    canvas = make_background(size, background)
    final = composite_logo(canvas, logo)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final.save(output_path, optimize=True, dpi=(300, 300))
    return output_path.resolve()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"PNG output path. Default: {DEFAULT_OUTPUT_PATH}",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=1024,
        help="Output width and height in pixels. Default: 1024",
    )
    parser.add_argument(
        "--background",
        choices=("transparent", "gray"),
        default="transparent",
        help="Background mode. Default: transparent",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    if args.size < len(GRID):
        raise ValueError(
            f"--size must be at least {len(GRID)} pixels for a clean upscale"
        )

    output_path = save_logo(
        output_path=args.output,
        size=args.size,
        background=args.background,
    )
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
