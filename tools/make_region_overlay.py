"""Draw saved extraction regions over the verified source photographs."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from colorlib import REPO_ROOT, all_palettes, palette_slug
from notebook_workflow import image_sha256, open_rgb, read_json


REGION_COLORS = [
    "#D64A3A",
    "#008A78",
    "#287FB8",
    "#9C4E97",
    "#C58B15",
    "#507A3A",
]


def arial(filename, size):
    path = Path(r"C:\Windows\Fonts") / filename
    if path.exists():
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


TITLE_FONT = arial("arialbd.ttf", 48)
SUBTITLE_FONT = arial("arial.ttf", 25)
LABEL_FONT = arial("arialbd.ttf", 25)
LEGEND_FONT = arial("arialbd.ttf", 27)
NOTE_FONT = arial("arial.ttf", 22)
SMALL_FONT = arial("arial.ttf", 18)


def save_documentation_png(image, destination):
    reduced = image.quantize(
        colors=256,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    )
    reduced.save(destination, optimize=True)


def label_box(draw, xy, text, color):
    x, y = xy
    bounds = draw.textbbox((0, 0), text, font=LABEL_FONT)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    pad_x = 10
    pad_y = 7
    draw.rounded_rectangle(
        (x, y, x + width + 2 * pad_x, y + height + 2 * pad_y),
        radius=5,
        fill=(255, 255, 255, 238),
        outline=color,
        width=3,
    )
    draw.text((x + pad_x, y + pad_y - bounds[1]), text,
              font=LABEL_FONT, fill="#15252A")


def source_for(recipe):
    value = recipe["source"]["image"]
    if value.startswith("https://") or value.startswith("http://"):
        raise ValueError("documentation region images require a local recipe source")
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def render_palette(slug, output=None):
    recipe_path = REPO_ROOT / "recipes" / f"{slug}.json"
    if not recipe_path.exists():
        raise FileNotFoundError(f"saved recipe not found: {recipe_path}")
    recipe = read_json(recipe_path)
    source = source_for(recipe)
    if image_sha256(source) != recipe["source"]["sha256"]:
        raise ValueError(f"{slug}: source checksum does not match the recipe")

    original = open_rgb(source)
    expected_size = (
        recipe["source"]["oriented_width"],
        recipe["source"]["oriented_height"],
    )
    if original.size != expected_size:
        raise ValueError(f"{slug}: source dimensions do not match the recipe")

    max_width = 1600
    max_height = 2300
    scale = min(max_width / original.width, max_height / original.height)
    shown_size = (
        max(1, round(original.width * scale)),
        max(1, round(original.height * scale)),
    )
    shown = original.resize(shown_size, Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", shown.size, (0, 0, 0, 0))
    drawing = ImageDraw.Draw(overlay, "RGBA")
    labels = []
    line_width = max(5, round(6 * min(1.0, scale)))

    for index, region in enumerate(recipe["regions"]):
        color = REGION_COLORS[index % len(REGION_COLORS)]
        rgb = tuple(int(color[position:position + 2], 16)
                    for position in (1, 3, 5))
        x0, y0, x1, y1 = region["box"]
        box = tuple(round(value * scale) for value in (x0, y0, x1, y1))
        drawing.rectangle(box, fill=rgb + (35,), outline=rgb + (255,),
                          width=line_width)
        text = f'{index + 1:02d}  {region["label"]}  k={region["k"]}'
        label_x = min(max(8, box[0] + 10), max(8, shown.width - 540))
        label_y = min(max(8, box[1] + 10), max(8, shown.height - 55))
        labels.append(((label_x, label_y), text, color))

    marked = Image.alpha_composite(shown.convert("RGBA"), overlay)
    drawing = ImageDraw.Draw(marked, "RGBA")
    for position, text, color in labels:
        label_box(drawing, position, text, color)

    header_height = 132
    row_height = 76
    legend_height = 44 + row_height * len(recipe["regions"]) + 55
    canvas_width = max(1600, shown.width)
    canvas_height = header_height + shown.height + legend_height
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)
    photo_x = (canvas_width - shown.width) // 2
    canvas.paste(marked.convert("RGB"), (photo_x, header_height))
    draw.text((36, 25), recipe["palette"], font=TITLE_FONT, fill="#15252A")
    draw.text((36, 82), "Saved extraction regions", font=SUBTITLE_FONT,
              fill="#657478")

    legend_y = header_height + shown.height + 28
    for index, region in enumerate(recipe["regions"]):
        color = REGION_COLORS[index % len(REGION_COLORS)]
        y = legend_y + index * row_height
        draw.rounded_rectangle((38, y + 4, 70, y + 36), radius=3,
                               fill=color)
        draw.text((88, y),
                  f'{index + 1:02d}  {region["label"]}  |  k={region["k"]}',
                  font=LEGEND_FONT, fill="#15252A")
        note = region.get("note", "").strip()
        if note:
            draw.text((88, y + 34), note, font=NOTE_FONT, fill="#657478")

    draw.text(
        (38, canvas_height - 35),
        f'Exact recipe coordinates on the verified {original.width} x {original.height} source image',
        font=SMALL_FONT,
        fill="#7A878A",
    )
    if output is None:
        output = REPO_ROOT / "docs" / slug / "regions.png"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    save_documentation_png(canvas, output)
    print(f"wrote {output}")
    return output


def write_overview(outputs, destination):
    columns = 2
    card_width = 760
    card_height = 900
    gap = 28
    margin = 42
    rows = (len(outputs) + columns - 1) // columns
    header = 110
    canvas = Image.new(
        "RGB",
        (margin * 2 + card_width * columns + gap,
         header + rows * card_height + max(0, rows - 1) * gap + margin),
        "white",
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((margin, 24), "Rang extraction regions", font=TITLE_FONT,
              fill="#15252A")
    for index, path in enumerate(outputs):
        with Image.open(path) as saved:
            image = saved.convert("RGB")
        image.thumbnail((card_width, card_height), Image.Resampling.LANCZOS)
        card = Image.new("RGB", (card_width, card_height), "#F3F5F4")
        card.paste(image, ((card_width - image.width) // 2,
                           (card_height - image.height) // 2))
        column = index % columns
        row = index // columns
        left = margin + column * (card_width + gap)
        top = header + row * (card_height + gap)
        canvas.paste(card, (left, top))
        draw.rectangle((left, top, left + card_width, top + card_height),
                       outline="#D9E0DE", width=2)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    save_documentation_png(canvas, destination)
    print(f"wrote {destination}")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("palette", nargs="?", help="palette name or slug")
    parser.add_argument("--all", action="store_true",
                        help="render every saved palette recipe")
    parser.add_argument("--output-dir",
                        help="write named overlays to this folder")
    parser.add_argument("--overview", action="store_true",
                        help="also write regions-overview.png")
    args = parser.parse_args()
    if not args.all and not args.palette:
        parser.error("give a palette name or use --all")

    slugs = ([palette_slug(item["name"]) for item in all_palettes()]
             if args.all else [palette_slug(args.palette)])
    outputs = []
    for slug in slugs:
        output = None
        if args.output_dir:
            output = Path(args.output_dir) / f"{slug}-regions.png"
        outputs.append(render_palette(slug, output))
    if args.overview:
        folder = Path(args.output_dir) if args.output_dir else REPO_ROOT / "docs"
        write_overview(outputs, folder / "regions-overview.png")


if __name__ == "__main__":
    main()
