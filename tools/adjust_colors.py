"""Nudge palette colors in LCh when a sampled color is not quite right.

Edits happen in lightness (L), chroma (C) and hue angle (H), which track how
people actually describe a color being off. Brighter or darker, more or less
saturated, leaning too orange. Position numbers are 1 based.

Examples

  python tools/adjust_colors.py --colors "#8a9463,#345f72" --edit "1:L+4"
  python tools/adjust_colors.py --colors "#7f3020,#ab4a47,#c07049" ^
      --edit "2:L-3,C+5" --edit "3:H+8" --png cache/before_after.png

Prints the edited hex codes and, with --png, writes a before and after strip
so you can judge the change against the original.
"""
import argparse
import re

from PIL import Image

from colorlib import hex_to_rgb, lab_to_lch, lab_to_rgb, lch_to_lab, rgb_to_hex, rgb_to_lab


def parse_edit(text):
    m = re.fullmatch(r"(\d+):(.+)", text.strip())
    if not m:
        raise argparse.ArgumentTypeError("expected position:changes, like 2:L+5,C-3")
    idx = int(m.group(1)) - 1
    changes = {}
    for part in m.group(2).split(","):
        pm = re.fullmatch(r"\s*([LCHlch])\s*([+-]\d+(?:\.\d+)?)\s*", part)
        if not pm:
            raise argparse.ArgumentTypeError(f"bad change '{part}', use L+5 C-3 H+10")
        changes[pm.group(1).upper()] = float(pm.group(2))
    return idx, changes


def apply_edit(hexcode, changes):
    lch = lab_to_lch(rgb_to_lab(hex_to_rgb(hexcode)))
    lch[0] = max(0, min(100, lch[0] + changes.get("L", 0)))
    lch[1] = max(0, lch[1] + changes.get("C", 0))
    lch[2] = (lch[2] + changes.get("H", 0)) % 360
    return rgb_to_hex(lab_to_rgb(lch_to_lab(lch)))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--colors", required=True, help="comma separated hex codes")
    ap.add_argument("--edit", action="append", type=parse_edit, default=[],
                    metavar="pos:changes", help="edit one color, repeatable")
    ap.add_argument("--png", help="optional before and after strip")
    args = ap.parse_args()

    before = [c.strip() for c in args.colors.split(",") if c.strip()]
    after = list(before)
    for idx, changes in args.edit:
        if not 0 <= idx < len(before):
            raise SystemExit(f"position {idx + 1} is outside the palette")
        after[idx] = apply_edit(after[idx], changes)

    print("before:", " ".join(before))
    print("after: ", " ".join(after))

    if args.png:
        cw, ch = 120, 90
        img = Image.new("RGB", (cw * len(before), ch * 2 + 8), "white")
        for i, (b, a) in enumerate(zip(before, after)):
            img.paste(Image.new("RGB", (cw, ch), b), (i * cw, 0))
            img.paste(Image.new("RGB", (cw, ch), a), (i * cw, ch + 8))
        img.save(args.png)
        print(f"wrote {args.png} (top row before, bottom row after)")


if __name__ == "__main__":
    main()
