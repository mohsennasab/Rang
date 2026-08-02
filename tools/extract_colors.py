"""Pull candidate colors out of an artwork photo.

Runs k-means in CIELAB, either over the whole image or over named regions you
mark out yourself. Region by region is almost always the better call. Large
areas such as a carpet field or a sky dominate a whole-image run and the
cluster centers drift into muddy averages, while small runs over the medallion,
the border or a figure recover the actual pigments.

Examples

  python tools/extract_colors.py --image https://images.metmuseum.org/CRDImages/is/original/DT5450.jpg
  python tools/extract_colors.py --image cache/DT5450.jpg -k 8 ^
      --region 900,1400,1700,2200,medallion --region 700,700,1900,1300,field ^
      --swatches cache/clusters.png

Coordinates are pixels in the full resolution image, x0,y0,x1,y1 with an
optional label. Open the photo in any viewer that shows cursor position to
read them off.
"""
import argparse

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from colorlib import fetch_image, lab_to_rgb, rgb_to_hex, rgb_to_lab


def parse_region(text):
    parts = text.split(",")
    if len(parts) not in (4, 5):
        raise argparse.ArgumentTypeError("expected x0,y0,x1,y1[,label]")
    box = tuple(int(v) for v in parts[:4])
    label = parts[4] if len(parts) == 5 else f"{box}"
    return label, box


def cluster(pixels, k):
    if k < 1:
        raise ValueError("k must be at least 1")
    if len(pixels) < k:
        raise ValueError(f"k={k} exceeds the {len(pixels)} sampled pixels")
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(rgb_to_lab(pixels))
    order = np.argsort(-np.bincount(km.labels_, minlength=k))
    rows = []
    for i in order:
        lab = km.cluster_centers_[i]
        rows.append((rgb_to_hex(lab_to_rgb(lab)), lab,
                     float((km.labels_ == i).mean() * 100)))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--image", required=True, help="path or URL of the photo")
    ap.add_argument("-k", type=int, default=8, help="clusters per region, default 8")
    ap.add_argument("--region", action="append", type=parse_region, default=[],
                    metavar="x0,y0,x1,y1[,label]",
                    help="crop to cluster separately, repeatable")
    ap.add_argument("--swatches", help="optional png of the clustered colors")
    args = ap.parse_args()

    path = fetch_image(args.image)
    full = Image.open(path).convert("RGB")
    print(f"image: {path}  size: {full.size[0]}x{full.size[1]}")

    regions = args.region or [("whole image", (0, 0, *full.size))]
    results = []
    for label, box in regions:
        x0, y0, x1, y1 = box
        if x0 < 0 or y0 < 0 or x1 > full.width or y1 > full.height:
            ap.error(f"region {label!r} lies outside the image")
        if x1 <= x0 or y1 <= y0:
            ap.error(f"region {label!r} has an empty or reversed extent")
        im = full.crop(box)
        im.thumbnail((400, 400))
        try:
            rows = cluster(np.asarray(im).reshape(-1, 3).astype(float), args.k)
        except ValueError as exc:
            ap.error(str(exc))
        results.append((label, rows))
        print(f"\n=== {label} {box} ===")
        for hexcode, lab, share in rows:
            print(f"  {hexcode}  L*={lab[0]:6.1f} a*={lab[1]:6.1f} "
                  f"b*={lab[2]:6.1f}  share={share:5.1f}%")

    if args.swatches:
        cw, ch = 110, 80
        img = Image.new("RGB", (cw * args.k, ch * len(results)), "white")
        for row, (label, rows) in enumerate(results):
            for col, (hexcode, _, _) in enumerate(rows):
                img.paste(Image.new("RGB", (cw, ch), hexcode), (col * cw, row * ch))
        img.save(args.swatches)
        print(f"\nwrote {args.swatches} (one row per region, largest cluster first)")


if __name__ == "__main__":
    main()
