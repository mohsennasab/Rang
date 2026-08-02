"""Generate a RAS Mapper surface fill for a palette and a data range.

RAS Mapper stores layer symbology in the project's .rasmap file as a
SurfaceFill element with signed ARGB color integers and the values assigned to
each color. This script prints a Symbology block for any Rang palette scaled
to the range you give it. The structure is based on RAS Mapper 6.x project
files because HEC does not publish a schema for this part of `.rasmap`.

Examples

  python tools/make_hecras_ramp.py kashan --min 0 --max 30
  python tools/make_hecras_ramp.py golestan --min 0 --max 12 -n 12 --reverse
  python tools/make_hecras_ramp.py kashan --min 480 --max 520 --alpha 200 --out fill.xml

Close HEC-RAS, open the project's .rasmap file in a text editor, find the
layer's Symbology block and replace it with the generated one. The hecras
folder of the repo has the full walkthrough.
"""
import argparse

from colorlib import hex_to_argb_int, interpolate, load_palette


def surface_fill(colors, vmin, vmax, alpha=255, use_dataset_minmax=False):
    if not colors:
        raise ValueError("at least one color is required")
    if isinstance(alpha, bool) or not isinstance(alpha, int) or not 0 <= alpha <= 255:
        raise ValueError("alpha must be an integer from 0 to 255")
    n = len(colors)
    argb = ",".join(str(hex_to_argb_int(c, alpha)) for c in colors)
    if n == 1:
        values = str(vmin)
    else:
        step = (vmax - vmin) / (n - 1)
        values = ",".join(f"{vmin + i * step:g}" for i in range(n))
    flag = "True" if use_dataset_minmax else "False"
    return ("<Symbology>\n"
            f'  <SurfaceFill Colors="{argb}" Values="{values}" Stretched="True" '
            f'AlphaTag="{alpha}" UseDatasetMinMax="{flag}" '
            'RegenerateForScreen="True" />\n'
            "</Symbology>")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("palette", help="name of a file in palettes/")
    ap.add_argument("--min", type=float, default=0.0, help="value of the first color")
    ap.add_argument("--max", type=float, default=1.0, help="value of the last color")
    ap.add_argument("-n", type=int, help="number of colors, interpolated along "
                                         "the ramp when it differs from the "
                                         "palette size")
    ap.add_argument("--reverse", action="store_true",
                    help="run the ramp last to first, handy for depth maps "
                         "where light should mean shallow")
    ap.add_argument("--alpha", type=int, default=255,
                    help="opacity 0 to 255, default 255")
    ap.add_argument("--use-dataset-minmax", action="store_true",
                    help="let RAS Mapper stretch the ramp over the layer's own "
                         "range instead of the values given here")
    ap.add_argument("--out", help="write to a file instead of printing")
    args = ap.parse_args()
    if args.n is not None and args.n < 1:
        ap.error("-n must be at least 1")
    if not 0 <= args.alpha <= 255:
        ap.error("--alpha must be from 0 to 255")
    if args.max <= args.min:
        ap.error("--max must be greater than --min")

    pal = load_palette(args.palette)
    colors = pal["colors"]
    if args.n and args.n != len(colors):
        colors = interpolate(colors, args.n)
    if args.reverse:
        colors = colors[::-1]

    block = surface_fill(colors, args.min, args.max, args.alpha,
                         args.use_dataset_minmax)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(block + "\n")
        print(f"wrote {args.out}")
    else:
        print(block)


if __name__ == "__main__":
    main()
