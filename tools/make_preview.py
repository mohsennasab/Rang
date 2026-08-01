"""Render the standard images every palette ships with.

  docs/<name>/swatch.png    the color strip with the palette name
  docs/<name>/card.png      the artwork beside the strip, used in the main
                            README gallery so the art and the palette read
                            together
  docs/<name>/preview.png   the artwork beside the palette under normal vision
                            and simulated protanopia, deuteranopia and
                            tritanopia

Run directly or let tools/build.py call it.

  python tools/make_preview.py kashan
"""
import argparse

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


def name_band(img, name, font_size):
    W, H = img.size
    d = ImageDraw.Draw(img)
    d.rectangle([0, H * 0.42, W, H * 0.58], fill=(255, 255, 255))
    font = get_font(font_size)
    box = d.textbbox((0, 0), name, font=font)
    d.text(((W - box[2]) / 2, (H - box[3]) / 2 - box[1]), name,
           fill="black", font=font)


def wrap_line(text, font, max_w):
    """Split an overlong caption line at commas so it fits the column."""
    parts = [p.strip() for p in text.split(",")]
    lines, current = [], ""
    for part in parts:
        candidate = f"{current}, {part}" if current else part
        if current and font.getlength(candidate) > max_w:
            lines.append(current)
            current = part
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def caption_lines(pal, font=None, max_w=580):
    src = pal["source"]
    line2 = src.get("geography", "")
    if src.get("accession"):
        line2 += f', accession {src["accession"]}'
    line3 = src.get("museum") or src.get("site") or ""
    lines = [f'{pal["name"]}, {src["title"]}, {src["date"]}', line2, line3]
    if src.get("credit") and not src.get("museum"):
        lines.append(src["credit"])
    lines = [ln for ln in lines if ln]
    if font is not None:
        lines = [w for ln in lines for w in wrap_line(ln, font, max_w)]
    return lines


def make_swatch(pal, out):
    img = strip(pal["colors"], 1400, 420)
    name_band(img, pal["name"], 78)
    img.save(out)


def make_card(pal, out):
    H = 380
    src = pal["source"]
    art_path = fetch_image(src.get("card_image") or src["image"])
    art = Image.open(art_path).convert("RGB")
    art.thumbnail((520, H))
    gap = 24
    W = art.width + gap + 1500 - 520
    card = Image.new("RGB", (W, H), "white")
    card.paste(art, (0, (H - art.height) // 2))
    sw = strip(pal["colors"], W - art.width - gap, H)
    name_band(sw, pal["name"], 64)
    card.paste(sw, (art.width + gap, 0))
    card.save(out)


def make_preview(pal, out):
    art = Image.open(fetch_image(pal["source"]["image"])).convert("RGB")
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
    for i, line in enumerate(caption_lines(pal, label_font, 1180 - x0 - 20)):
        d.text((x0, y + 10 + 30 * i), line, fill=(60, 60, 60), font=label_font)
    canvas.save(out)


def main(name):
    pal = load_palette(name)
    out_dir = REPO_ROOT / "docs" / pal["name"].lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    make_swatch(pal, out_dir / "swatch.png")
    make_card(pal, out_dir / "card.png")
    make_preview(pal, out_dir / "preview.png")
    print(f"wrote swatch.png, card.png and preview.png in {out_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("palette", help="name of a file in palettes/")
    main(ap.parse_args().palette)
