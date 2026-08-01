"""Turn palette definitions into everything the repo publishes.

Reads palettes/*.json, the single source of truth, and regenerates

  python/rang/_palettes.py       the Python package data
  r/R/palettes_data.R            the R package data
  arcgis/<Name>.clr              discrete Esri colormap file
  arcgis/<Name>_continuous.clr   256 step ramp as an Esri colormap file
  docs/<name>/swatch.png         color strip for the gallery
  docs/<name>/preview.png        artwork plus vision simulations
  docs/<name>/samples.png        the six standard sample plots
  docs/<name>/README.md          the palette page
  README.md                      the gallery section between the markers

Contributors run one command after adding or editing a palette file

  python tools/build.py kashan      one palette's images and page, plus all
                                    generated code files
  python tools/build.py --all       everything

If a palette file has no "order" entry the build computes one and writes it
back into the json.
"""
import argparse
import json
import re

import make_preview
import make_samples
from colorlib import (COLORBLIND_THRESHOLD, PALETTE_DIR, REPO_ROOT,
                      VISION_LABELS, VISION_TYPES, all_palettes, fetch_image,
                      greedy_order, hex_to_rgb, interpolate, load_palette,
                      pairwise_min_mean, presence_in_image, worst_case)

GALLERY_START = "<!-- gallery:start -->"
GALLERY_END = "<!-- gallery:end -->"


# ------------------------------------------------------------ generated code

def write_python(pals):
    lines = ['"""Palette data. Built with tools/build.py, edit palettes/*.json instead."""',
             "", "PALETTES = {"]
    for p in pals:
        src = p["source"]
        lines += [
            f'    "{p["name"]}": {{',
            f'        "colors": {tuple(p["colors"])},',
            f'        "order": {tuple(p["order"])},',
            f'        "colorblind": {p["colorblind"]},',
            f'        "source": {{',
            f'            "title": {src["title"]!r},',
            f'            "date": {src["date"]!r},',
            f'            "geography": {src["geography"]!r},',
            f'            "museum": {src["museum"]!r},',
            f'            "accession": {src["accession"]!r},',
            f'            "url": {src["url"]!r},',
            f'        }},',
            f'    }},',
        ]
    lines += ["}", ""]
    out = REPO_ROOT / "python" / "rang" / "_palettes.py"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


def write_r(pals):
    lines = ["# Palette data. Built with tools/build.py, edit palettes/*.json instead.",
             "",
             "#' Complete list of Rang palettes",
             "#'",
             "#' Use names(rang_palettes) for the available names and rang() to build",
             "#' a palette. Each entry holds the colors, the discrete pick order and a",
             "#' colorblind friendliness flag.",
             "#'",
             "#' @export",
             "rang_palettes <- list("]
    for p in pals:
        cols = ", ".join(f'"{c}"' for c in p["colors"])
        order = ", ".join(str(v) for v in p["order"])
        flag = "TRUE" if p["colorblind"] else "FALSE"
        src = p["source"]
        cite = f'{src["title"]}, {src["date"]}, {src["museum"]}, {src["url"]}'
        lines.append(f'  {p["name"]} = list(')
        lines.append(f'    colors = c({cols}),')
        lines.append(f'    order = c({order}),')
        lines.append(f'    colorblind = {flag},')
        lines.append(f'    source = "{cite}"')
        lines.append("  ),")
    lines[-1] = lines[-1].rstrip(",")
    lines += [")", ""]
    out = REPO_ROOT / "r" / "R" / "palettes_data.R"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")


def write_clr(pal):
    arc = REPO_ROOT / "arcgis"
    arc.mkdir(exist_ok=True)
    disc = arc / f'{pal["name"]}.clr'
    with open(disc, "w", encoding="utf-8") as f:
        for i, c in enumerate(pal["colors"], start=1):
            r, g, b = (int(v) for v in hex_to_rgb(c))
            f.write(f"{i} {r} {g} {b}\n")
    cont = arc / f'{pal["name"]}_continuous.clr'
    with open(cont, "w", encoding="utf-8") as f:
        for i, c in enumerate(interpolate(pal["colors"], 256)):
            r, g, b = (int(v) for v in hex_to_rgb(c))
            f.write(f"{i} {r} {g} {b}\n")
    print(f"wrote {disc} and {cont}")


# ------------------------------------------------------------- palette page

def cvd_table(colors):
    rows = ["| vision | min CIEDE2000 | mean |", "|---|---|---|"]
    for kind in VISION_TYPES:
        mn, mean = pairwise_min_mean(colors, kind)
        rows.append(f"| {VISION_LABELS[kind]} | {mn:.1f} | {mean:.1f} |")
    return "\n".join(rows)


def write_docs_page(pal):
    src = pal["source"]
    name = pal["name"]
    colors = pal["colors"]
    notes = pal.get("notes", [""] * len(colors))

    presence = None
    try:
        presence = presence_in_image(colors, fetch_image(src["image"]))
    except Exception as e:
        print(f"presence check skipped: {e}")

    hex_rows = ["| position | hex | drawn from |" + (" nearest pixel |" if presence else ""),
                "|---|---|---|" + ("---|" if presence else "")]
    for i, (c, note) in enumerate(zip(colors, notes), start=1):
        row = f"| {i} | `{c}` | {note} |"
        if presence:
            row += f" {presence[c][0]:.1f} |"
        hex_rows.append(row)

    wc = worst_case(colors)
    verdict = ("passes" if pal["colorblind"] else "does not pass")

    body = f"""# {name}

![{name} swatch](swatch.png)

## Source

{src["title"]}, {src["date"]}. {src["geography"]}. {src["medium"]}.
{src["museum"]}, {src["department"]}, accession {src["accession"]}.
{src["credit"]}.

[Object page]({src["url"]}) and [full resolution photo]({src["image"]}), released
by the museum under open access.

## Colors

{chr(10).join(hex_rows)}

The nearest pixel column is the CIEDE2000 distance from each palette color to
the closest pixel in the museum photo. Small numbers mean the color is really
in the artwork.

## The palette beside the artwork

![{name} preview](preview.png)

## Sample plots

![{name} samples](samples.png)

Regenerate this page with `python tools/make_samples.py {name.lower()}`. Pass
`--dem your_dem.tif` to draw the elevation panel from your own raster.

## Separation and color vision

{cvd_table(colors)}

The worst case across the four vision types is {wc:.1f}, so this palette
{verdict} the collection's colorblind friendliness threshold of {COLORBLIND_THRESHOLD:.0f}.
Discrete picks use the stored order, which was chosen to keep the first few
colors as far apart as possible under every vision type.

## Use it

Python

```python
import rang
rang.rang("{name}", 5)
rang.cmap("{name}")
```

R

```r
library(Rang)
rang("{name}", 5)
```

ArcGIS Pro files are in [arcgis/{name}.clr](../../arcgis/{name}.clr) and
[arcgis/{name}_continuous.clr](../../arcgis/{name}_continuous.clr), with steps
in the [ArcGIS guide](../../arcgis/README.md).
"""
    out = REPO_ROOT / "docs" / name.lower() / "README.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out}")


# ------------------------------------------------------------ README gallery

def gallery_entry(pal):
    src = pal["source"]
    name = pal["name"]
    friendly = " Colorblind friendly." if pal["colorblind"] else ""
    return f"""### {name}

![{name}](docs/{name.lower()}/swatch.png)

{src["title"]}, {src["date"]}. {src["geography"]}.
{src["museum"]}, accession {src["accession"]}. [Object page]({src["url"]}){friendly}

`{" ".join(pal["colors"])}`

[Sample plots and full details](docs/{name.lower()}/README.md)
"""


def update_readme(pals):
    readme = REPO_ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if GALLERY_START not in text or GALLERY_END not in text:
        raise SystemExit("README.md is missing the gallery markers")
    block = GALLERY_START + "\n\n" + "\n***\n\n".join(gallery_entry(p) for p in pals) + "\n" + GALLERY_END
    text = re.sub(re.escape(GALLERY_START) + r".*?" + re.escape(GALLERY_END),
                  block, text, flags=re.S)
    readme.write_text(text, encoding="utf-8")
    print(f"updated gallery in {readme}")


# --------------------------------------------------------------------- build

def ensure_order(name):
    """Fill in the order vector when a palette file does not have one."""
    path = PALETTE_DIR / f"{name.lower()}.json"
    pal = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    if "order" not in pal or len(pal["order"]) != len(pal["colors"]):
        pal["order"] = greedy_order(pal["colors"])
        changed = True
        print(f"computed order for {pal['name']}: {pal['order']}")
    if "colorblind" not in pal:
        pal["colorblind"] = worst_case(pal["colors"]) >= COLORBLIND_THRESHOLD
        changed = True
        print(f"computed colorblind flag for {pal['name']}: {pal['colorblind']}")
    if changed:
        path.write_text(json.dumps(pal, indent=2) + "\n", encoding="utf-8")
    return pal


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("palette", nargs="?", help="name of a file in palettes/")
    ap.add_argument("--all", action="store_true", help="rebuild every palette")
    ap.add_argument("--skip-images", action="store_true",
                    help="regenerate code and pages only")
    args = ap.parse_args()

    if not args.all and not args.palette:
        ap.error("give a palette name or --all")

    targets = ([p["name"] for p in all_palettes()] if args.all
               else [load_palette(args.palette)["name"]])

    for name in targets:
        ensure_order(name)

    pals = all_palettes()
    write_python(pals)
    write_r(pals)
    for p in pals:
        write_clr(p)

    for name in targets:
        if not args.skip_images:
            make_preview.main(name.lower())
            make_samples.main(name.lower())
        write_docs_page(load_palette(name.lower()))

    update_readme(pals)
    print("\nbuild finished")


if __name__ == "__main__":
    main()
