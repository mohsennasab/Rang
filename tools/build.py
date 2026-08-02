"""Turn palette definitions into everything the repo publishes.

Reads palettes/*.json, the single source of truth, and regenerates

  python/rang/_palettes.py       the Python package data
  r/R/palettes_data.R            the R package data
  arcgis/Rang.stylx              ArcGIS Pro style with every palette's colors
                                 and color schemes, one import in Catalog
  qgis/Rang.xml                  QGIS style file with every ramp, smooth and
                                 discrete, for the Style Manager
  qgis/<Name>.gpl                GIMP palette file QGIS imports as swatches
  hecras/<Name>.rasmap.xml       RAS Mapper surface fill blocks to paste into
                                 a project's .rasmap file
  docs/<name>/swatch.png         color strip
  docs/<name>/card.png           artwork beside the strip, for the gallery
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

import make_hecras_ramp
import make_preview
import make_samples
import make_stylx
from colorlib import (COLORBLIND_THRESHOLD, PALETTE_DIR, REPO_ROOT,
                      VISION_LABELS, VISION_TYPES, all_palettes, fetch_image,
                      greedy_order, hex_to_rgb, load_palette,
                      pairwise_min_mean, presence_in_image, worst_case)

GALLERY_START = "<!-- gallery:start -->"
GALLERY_END = "<!-- gallery:end -->"


def rgb_ints(hexcode):
    return tuple(int(v) for v in hex_to_rgb(hexcode))


def held_by(src):
    """Museum or site line, whichever the source has."""
    return src.get("museum") or src.get("site") or ""


# ------------------------------------------------------------ generated code

def write_python(pals):
    lines = ['"""Palette data. Built with tools/build.py, edit palettes/*.json instead."""',
             "", "PALETTES = {"]
    for p in pals:
        entry = {
            "colors": tuple(p["colors"]),
            "order": tuple(p["order"]),
            "colorblind": p["colorblind"],
            "persian": p.get("persian", ""),
            "pronunciation": p.get("pronunciation", ""),
            "source": p["source"],
        }
        lines.append(f'    "{p["name"]}": {entry!r},')
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
        cite = f'{src["title"]}, {src["date"]}, {held_by(src)}, {src["url"]}'
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


def qgis_ramp(name, colors, discrete):
    """One gradient colorramp element in QGIS style XML."""
    n = len(colors)
    if discrete:
        positions = [(i / n, colors[i]) for i in range(1, n)]
    else:
        positions = [(i / (n - 1), colors[i]) for i in range(1, n - 1)]
    stops = ":".join("{};{},{},{},255".format(round(pos, 6), *rgb_ints(c))
                     for pos, c in positions)
    first = "{},{},{},255".format(*rgb_ints(colors[0]))
    last = "{},{},{},255".format(*rgb_ints(colors[-1]))
    return "\n".join([
        f'    <colorramp type="gradient" name="{name}" tags="Rang">',
        f'      <prop k="color1" v="{first}"/>',
        f'      <prop k="color2" v="{last}"/>',
        f'      <prop k="discrete" v="{1 if discrete else 0}"/>',
        f'      <prop k="rampType" v="gradient"/>',
        f'      <prop k="stops" v="{stops}"/>',
        "    </colorramp>",
    ])


def write_qgis(pals):
    qdir = REPO_ROOT / "qgis"
    qdir.mkdir(exist_ok=True)

    ramps = []
    for p in pals:
        ramps.append(qgis_ramp(p["name"], p["colors"], discrete=False))
        ramps.append(qgis_ramp(f'{p["name"]} discrete', p["colors"], discrete=True))
    xml = "\n".join(['<!DOCTYPE qgis_style>',
                     '<qgis_style version="2">',
                     "  <symbols/>",
                     "  <colorramps>",
                     *ramps,
                     "  </colorramps>",
                     "</qgis_style>",
                     ""])
    (qdir / "Rang.xml").write_text(xml, encoding="utf-8")
    print(f"wrote {qdir / 'Rang.xml'}")

    for p in pals:
        lines = ["GIMP Palette", f'Name: Rang {p["name"]}', "Columns: 0", "#"]
        for i, c in enumerate(p["colors"], start=1):
            r, g, b = rgb_ints(c)
            lines.append(f'{r:3d} {g:3d} {b:3d} {p["name"]} {i}')
        (qdir / f'{p["name"]}.gpl').write_text("\n".join(lines) + "\n",
                                               encoding="utf-8")
        print(f'wrote {qdir / (p["name"] + ".gpl")}')


def write_hecras(pal):
    """Paste ready RAS Mapper surface fill blocks for one palette.

    The format matches what RAS Mapper itself writes into a project's .rasmap
    file. Shipped blocks let RAS Mapper stretch the ramp over the layer's own
    range, and tools/make_hecras_ramp.py generates blocks with fixed values.
    """
    hdir = REPO_ROOT / "hecras"
    hdir.mkdir(exist_ok=True)
    name = pal["name"]
    colors = pal["colors"]
    blocks = [
        f"<!-- Rang {name} for HEC-RAS RAS Mapper. Built with tools/build.py. -->",
        "<!-- Close HEC-RAS, open the project's .rasmap file in a text editor, and -->",
        "<!-- replace the target layer's Symbology block with one of these. For a -->",
        "<!-- fixed value range use tools/make_hecras_ramp.py instead. -->",
        "",
        f"<!-- {name}, first to last, stretched over the layer's range -->",
        make_hecras_ramp.surface_fill(colors, 0, 1, use_dataset_minmax=True),
        "",
        f"<!-- {name} reversed, for when the ramp should run the other way -->",
        make_hecras_ramp.surface_fill(colors[::-1], 0, 1, use_dataset_minmax=True),
    ]
    out = hdir / f"{name}.rasmap.xml"
    out.write_text("\n".join(blocks) + "\n", encoding="utf-8")
    print(f"wrote {out}")


# ------------------------------------------------------------- palette page

def cvd_table(colors):
    rows = ["| vision | min CIEDE2000 | mean |", "|---|---|---|"]
    for kind in VISION_TYPES:
        mn, mean = pairwise_min_mean(colors, kind)
        rows.append(f"| {VISION_LABELS[kind]} | {mn:.1f} | {mean:.1f} |")
    return "\n".join(rows)


def source_section(src):
    parts = [f'{src["title"]}, {src["date"]}. {src.get("geography", "")}.']
    if src.get("medium"):
        parts.append(f'{src["medium"]}.')
    line2 = held_by(src)
    if src.get("department"):
        line2 += f', {src["department"]}'
    if src.get("accession"):
        line2 += f', accession {src["accession"]}'
    if line2:
        parts.append(line2 + ".")
    if src.get("credit"):
        parts.append(src["credit"] + ".")
    text = "\n".join(parts)

    if src.get("public_domain"):
        photo_note = (f'[Object page]({src["url"]}) and '
                      f'[full resolution photo]({src["image"]}), released by '
                      "the museum under open access.")
    else:
        rights = src.get("rights", "photo used with permission").strip().rstrip(".")
        rights = rights[0].upper() + rights[1:]
        photo_note = f'[Reference page]({src["url"]}). {rights}.'
    return text + "\n\n" + photo_note


def context_block(pal):
    src = pal["source"]
    if not src.get("context_image"):
        return ""
    rel = "../../" + src["context_image"].replace("\\", "/")
    caption = src.get("context_caption", "The work in its setting")
    return f"\n## The setting\n\n![{caption}]({rel})\n\n{caption}.\n"


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
    bits = []
    if pal.get("persian"):
        bits.append(f'Persian: {pal["persian"]}')
    if pal.get("pronunciation"):
        bits.append(f'say it {pal["pronunciation"]}')
    say = f' ({", ".join(bits)})' if bits else ""
    about = f'\n{pal["about"]}\n' if pal.get("about") else ""

    if pal.get("samples") == "water":
        samples_note = (
            "Both panels are real data. The elevation panel is the USGS 100 year\n"
            "high flood profile for the creeks at Ithaca, New York, and the network\n"
            "is Fall Creek upstream of Ithaca from the USGS NLDI service.\n"
            f"Regenerate this page with `python tools/make_samples.py {name.lower()}`.")
    else:
        samples_note = (
            "The rainfall panel is real data, one day of NOAA AORC 1 km precipitation.\n"
            f"Regenerate this page with `python tools/make_samples.py {name.lower()}`, and\n"
            "pass `--dem your_dem.tif` to draw the elevation panel from your own raster.")

    body = f"""# {name}{say}

![{name} swatch](swatch.png)
{about}
## Source

{source_section(src)}
{context_block(pal)}
## Colors

{chr(10).join(hex_rows)}

The nearest pixel column is the CIEDE2000 distance from each palette color to
the closest pixel in the source photo. Small numbers mean the color is really
in the artwork.

## The palette beside the artwork

![{name} preview](preview.png)

## Sample plots

![{name} samples](samples.png)

{samples_note}

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

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/{name}.gpl](../../qgis/{name}.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS surface fills are in
[hecras/{name}.rasmap.xml](../../hecras/{name}.rasmap.xml), see the
[HEC-RAS guide](../../hecras/README.md).
"""
    out = REPO_ROOT / "docs" / name.lower() / "README.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(f"wrote {out}")


# ------------------------------------------------------------ README gallery

def gallery_entry(pal):
    src = pal["source"]
    name = pal["name"]
    say = ""
    if pal.get("persian"):
        say += f' Persian: {pal["persian"]}.'
    if pal.get("pronunciation"):
        say += f' Say it {pal["pronunciation"]}.'
    friendly = " Colorblind friendly." if pal["colorblind"] else ""
    line = f'{src["title"]}, {src["date"]}.'
    if held_by(src):
        line += f' {held_by(src)}.'
    if src.get("credit") and not src.get("museum"):
        line += f' {src["credit"]}.'
    about = f'\n{pal["about"]}\n' if pal.get("about") else ""
    return f"""### {name}

![{name}, the artwork and its palette](docs/{name.lower()}/card.png)

{line} [Reference]({src["url"]}){friendly}{say}
{about}
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
    if "position" not in pal:
        taken = [q.get("position", 0) for q in all_palettes()
                 if q["name"] != pal["name"]]
        pal["position"] = max(taken, default=0) + 1
        changed = True
        print(f"assigned gallery position {pal['position']} to {pal['name']}")
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
    write_qgis(pals)
    make_stylx.write_stylx(pals)
    for p in pals:
        write_hecras(p)

    for name in targets:
        if not args.skip_images:
            make_preview.main(name.lower())
            make_samples.main(name.lower())
        write_docs_page(load_palette(name.lower()))

    update_readme(pals)
    print("\nbuild finished")


if __name__ == "__main__":
    main()
