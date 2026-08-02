"""Score a palette before it goes into the collection.

Reports the pairwise CIEDE2000 separation under normal vision and under
simulated protanopia, deuteranopia and tritanopia, suggests the discrete pick
order, and, when the source photo is available, measures how close each color
sits to a sampled point in a reduced copy of the artwork.

Examples

  python tools/check_palette.py --palette kashan
  python tools/check_palette.py --colors "#7f3020,#ab4a47,#c07049,#1a3b45"
  python tools/check_palette.py --palette kashan --image cache/DT5450.jpg
"""
import argparse

from colorlib import (COLORBLIND_THRESHOLD, VISION_LABELS, VISION_TYPES,
                      discrete_subset, fetch_image, greedy_order, load_palette,
                      pairwise_min_mean, presence_in_image, worst_case, worst_pair)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--palette", help="name of a file in palettes/")
    group.add_argument("--colors", help="comma separated hex codes")
    ap.add_argument("--image", help="source photo, path or URL. Defaults to the "
                                    "palette's source image when --palette is used")
    args = ap.parse_args()

    image = args.image
    if args.palette:
        pal = load_palette(args.palette)
        colors = pal["colors"]
        name = pal["name"]
        if image is None:
            image = pal["source"].get("image")
    else:
        colors = [c.strip() for c in args.colors.split(",") if c.strip()]
        name = "palette"
    if len(colors) < 2:
        raise SystemExit("provide at least two colors")

    print(f"{name}: {len(colors)} colors")
    print("  " + " ".join(colors))

    print("\nPairwise CIEDE2000 (Machado 2009 simulation, severity 1.0)")
    for kind in VISION_TYPES:
        mn, mean = pairwise_min_mean(colors, kind)
        print(f"  {VISION_LABELS[kind]:14s} min = {mn:5.1f}   mean = {mean:5.1f}")

    wc = worst_case(colors)
    d, a, b, where = worst_pair(colors)
    verdict = "yes" if wc >= COLORBLIND_THRESHOLD else "no"
    print(f"\n  closest pair: {a} and {b} under {where}, CIEDE2000 = {d:.1f}")
    print(f"  passes project CVD check at {COLORBLIND_THRESHOLD}: {verdict}")

    order = greedy_order(colors)
    print(f"\nSuggested pick order: {order}")
    for n in range(2, len(colors) + 1):
        sub = discrete_subset(colors, order, n)
        print(f"  n={n}: {' '.join(sub)}   worst = {worst_case(sub):.1f}")

    if image:
        path = fetch_image(image)
        print(f"\nDistance to sampled points in the source photo ({path.name})")
        for h, (nearest, share) in presence_in_image(colors, path).items():
            flag = "" if nearest <= 3 else "   <- check this one"
            print(f"  {h}  nearest sample = {nearest:4.1f}   "
                  f"samples within 8.0 = {share:5.2f}%{flag}")


if __name__ == "__main__":
    main()
