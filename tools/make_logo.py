"""Generate a transparent 8-bit Rang logo as a PNG."""

import math
from pathlib import Path
from PIL import Image, ImageDraw

from colorlib import REPO_ROOT

OUTPUT_SIZE = 1024
PIXEL_SIZE = 128
OUTPUT_PATH = REPO_ROOT / "logo" / "rang.png"

TRANSPARENT = (255, 255, 255, 0)
CREAM = "#fffaf0"
NAVY = "#1a3b45"
GOLD = "#c59b46"
OUTER_COLORS = (
    "#7f3020",
    "#c07049",
    "#c59b46",
    "#cbb11c",
    "#45939c",
    "#333a80",
    "#345f72",
    "#9a9a68",
)


def point(cx, cy, radius, angle):
    """Return an integer point on a circle."""
    return (
        round(cx + radius * math.cos(angle)),
        round(cy + radius * math.sin(angle)),
    )


def star_points(cx, cy, outer_radius, inner_radius,
                count=8, rotation=-math.pi / 2):
    """Return alternating outer and inner vertices for a star."""
    return [
        point(
            cx,
            cy,
            outer_radius if index % 2 == 0 else inner_radius,
            rotation + index * math.pi / count,
        )
        for index in range(count * 2)
    ]


def petal_points(cx, cy, angle):
    """Return the five vertices of one outer petal."""
    return [
        point(cx, cy, 25, angle - math.pi / 8),
        point(cx, cy, 44, angle - math.pi / 16),
        point(cx, cy, 50, angle),
        point(cx, cy, 44, angle + math.pi / 16),
        point(cx, cy, 25, angle + math.pi / 8),
    ]


def draw_polygon(draw, coordinates, fill, outline=None, width=1):
    """Draw a filled polygon with a pixel-aligned outline."""
    if outline and width > 0:
        for dx in range(-width, width + 1):
            for dy in range(-width, width + 1):
                shifted = [(x + dx, y + dy) for x, y in coordinates]
                draw.polygon(shifted, fill=outline)

    draw.polygon(coordinates, fill=fill)


def draw_circle(draw, cx, cy, radius, fill, outline=None, width=1):
    """Draw a low-resolution circle with an optional outline."""
    bounds = (cx - radius, cy - radius, cx + radius, cy + radius)

    if outline and width > 0:
        draw.ellipse(bounds, fill=outline)
        inner = (
            cx - radius + width,
            cy - radius + width,
            cx + radius - width,
            cy + radius - width,
        )
        draw.ellipse(inner, fill=fill)
    else:
        draw.ellipse(bounds, fill=fill)


def render_logo(output_path=OUTPUT_PATH):
    """Render the logo at low resolution and enlarge it without smoothing."""
    center = PIXEL_SIZE // 2
    image = Image.new(
        "RGBA",
        (PIXEL_SIZE, PIXEL_SIZE),
        TRANSPARENT,
    )
    draw = ImageDraw.Draw(image)

    # Outer cream field with navy border.
    draw_circle(
        draw,
        center,
        center,
        radius=52,
        fill=CREAM,
        outline=NAVY,
        width=2,
    )

    # Original eight-color outer petals.
    for index, color in enumerate(OUTER_COLORS):
        angle = -math.pi / 2 + index * math.pi / 4
        draw_polygon(
            draw,
            petal_points(center, center, angle),
            fill=color,
            outline=CREAM,
            width=1,
        )

    # Detailed navy outer prongs.
    draw_polygon(
        draw,
        star_points(center, center, 33, 15),
        fill=NAVY,
        outline=CREAM,
        width=1,
    )

    # Rotated gold inner star.
    draw_polygon(
        draw,
        star_points(
            center,
            center,
            19,
            8,
            rotation=-math.pi / 2 + math.pi / 8,
        ),
        fill=GOLD,
        outline=CREAM,
        width=1,
    )

    # Navy center circle matching the outer prongs.
    draw_circle(
        draw,
        center,
        center,
        radius=5,
        fill=NAVY,
    )

    # Nearest-neighbor scaling preserves the visible 8-bit pixels.
    image = image.resize(
        (OUTPUT_SIZE, OUTPUT_SIZE),
        Image.Resampling.NEAREST,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, optimize=True, dpi=(300, 300))
    print(f"Wrote {output_path.resolve()}")


def main():
    """Build the repository logo through the standard tool entry point."""
    render_logo()


if __name__ == "__main__":
    main()
