"""Render the Rang logo from deterministic vector-like geometry."""
import math

from PIL import Image, ImageDraw

from colorlib import REPO_ROOT

SIZE = 1024
SCALE = 4
BACKGROUND = "#f5f0e6"
OUTER_COLORS = ("#7f3020", "#c07049", "#c59b46", "#cbb11c",
                "#45939c", "#333a80", "#345f72", "#9a9a68")


def point(cx, cy, radius, angle):
    return (cx + radius * math.cos(angle), cy + radius * math.sin(angle))


def star_points(cx, cy, outer, inner, count=8, rotation=-math.pi / 2):
    points = []
    for i in range(count * 2):
        radius = outer if i % 2 == 0 else inner
        points.append(point(cx, cy, radius, rotation + i * math.pi / count))
    return points


def main():
    size = SIZE * SCALE
    center = size / 2
    image = Image.new("RGB", (size, size), BACKGROUND)
    draw = ImageDraw.Draw(image)

    draw.ellipse((130 * SCALE, 130 * SCALE, 894 * SCALE, 894 * SCALE),
                 fill="#fffaf0", outline="#1a3b45", width=18 * SCALE)

    for i, color in enumerate(OUTER_COLORS):
        angle = -math.pi / 2 + i * math.pi / 4
        petal = [
            point(center, center, 205 * SCALE, angle - math.pi / 8),
            point(center, center, 360 * SCALE, angle - math.pi / 16),
            point(center, center, 405 * SCALE, angle),
            point(center, center, 360 * SCALE, angle + math.pi / 16),
            point(center, center, 205 * SCALE, angle + math.pi / 8),
        ]
        draw.polygon(petal, fill=color, outline="#fffaf0", width=12 * SCALE)

    draw.polygon(star_points(center, center, 260 * SCALE, 118 * SCALE),
                 fill="#1a3b45", outline="#fffaf0", width=14 * SCALE)
    draw.polygon(star_points(center, center, 150 * SCALE, 66 * SCALE,
                             rotation=-math.pi / 2 + math.pi / 8),
                 fill="#c59b46", outline="#fffaf0", width=10 * SCALE)
    draw.ellipse((center - 38 * SCALE, center - 38 * SCALE,
                  center + 38 * SCALE, center + 38 * SCALE), fill="#45939c")

    image = image.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    out = REPO_ROOT / "logo" / "rang.png"
    out.parent.mkdir(exist_ok=True)
    image.save(out, optimize=True, dpi=(96, 96))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
