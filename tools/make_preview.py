"""Render the two standard images every palette ships with.

  docs/<name>/swatch.png    the color strip with the palette name, used in the
                            main README gallery
  docs/<name>/preview.png   the artwork beside the palette under normal vision
                            and simulated protanopia, deuteranopia and
                            tritanopia

Run directly or let tools/build.py call it.

  python tools/make_preview.py kashan
"""
import argparse
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from colorlib import (REPO_ROOT, VISION_LABELS, VISION_TYPES, fetch_image,
                      hex_to_rgb, load_palette, simulate)


def get_font(size):
    for candidate in ("times.ttf", "georgia.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def strip(colors, w, h, kind=None):
    img = Image.new("RGB", (w, h), "white")
    cw = w / len(colors)
    for i, c in enumerate(colors):
        rgb = tuple(np.round(np.clip(simulate(hex_to_rgb(c), kind), 0, 255)).astype(int))
        img.paste(Image.new("RGB", (int(cw) + 1, h), rgb), (int(i * cw), 0))
    return img


def make_swatch(pal, out):
    W, H = 1400, 420
    img = strip(pal["colors"], W, H)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H * 0.42, W, H * 0.58], fill=(255, 255, 255))
    font = get_font(78)
    box = d.textbbox((0, 0), pal["name"], font=font)
    d.text(((W - box[2]) / 2, (H - box[3]) / 2 - 8), pal["name"],
           fill="black", font=font)
    img.save(out)


def make_preview(pal, out):
    src = pal["source"]
    art = Image.open(fetch_image(src["image"])).convert("RGB")
    art.thumbnail((520, 780))
    canvas = Image.new("RGB", (1180, max(art.height + 40, 700)), "white")
    canvas.paste(art, (20, 20))
    d = ImageDraw.Draw(canvas)
    label_font = get_font(22)
    x0, y = 580, 40
    for kind in VISION_TYPES:
        d.text((x0, y), VISION_LABELS[kind], fill=(60, 60, 60), font=label_font)
        canvas.paste(strip(pal["colors"], 560, 70, kind), (x0, y + 30))
        y += 130
    line2 = src["geography"]
    if src.get("accession"):
        line2 += f', accession {src["accession"]}'
    lines = [f'{pal["name"]}, {src["title"]}, {src["date"]}', line2, src["museum"]]
    for i, line in enumerate(lines):
        d.text((x0, y + 10 + 30 * i), line, fill=(60, 60, 60), font=label_font)
    canvas.save(out)


def main(name):
    pal = load_palette(name)
    out_dir = REPO_ROOT / "docs" / pal["name"].lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    make_swatch(pal, out_dir / "swatch.png")
    make_preview(pal, out_dir / "preview.png")
    print(f"wrote {out_dir / 'swatch.png'} and {out_dir / 'preview.png'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("palette", help="name of a file in palettes/")
    main(ap.parse_args().palette)
