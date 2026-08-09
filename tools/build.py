"""Turn palette definitions into everything the repo publishes.

Reads palettes/*.json, the single source of truth, and regenerates

  python/rang/_palettes.py       the Python package data
  r/R/palettes_data.R            the R package data
  arcgis/Rang.stylx              ArcGIS Pro style with every palette's colors
                                 and color schemes, one import in Catalog
  qgis/Rang.xml                  QGIS style file with every ramp, smooth and
                                 discrete, for the Style Manager
  qgis/<Name>.gpl                GIMP palette file QGIS imports as swatches
  hecras/Rang-<Name>.xml         HEC-RAS custom color-ramp import for one palette
  hecras/Rang-All.xml            HEC-RAS custom color-ramp import for every palette
  geolibre/Rang.json             GeoLibre-ready color lists for scripts
  geolibre/Rang.txt              GeoLibre-ready color lists for copy and paste
  docs/<name>/swatch.png         color strip
  docs/<name>/card.png           artwork beside the strip, for the gallery
  docs/<name>/preview.png        artwork plus vision simulations
  docs/<name>/regions.png        saved extraction regions on the source photo
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
import make_logo
import make_preview
import make_region_overlay
import make_samples
import make_stylx
from colorlib import (COLORBLIND_THRESHOLD, PALETTE_DIR, REPO_ROOT,
                      VISION_LABELS, VISION_TYPES, all_palettes, fetch_image,
                      greedy_order, hex_to_rgb, interpolate, load_palette,
                      pairwise_min_mean, palette_slug, presence_in_image,
                      worst_case)

GALLERY_START = "<!-- gallery:start -->"
GALLERY_END = "<!-- gallery:end -->"


def rgb_ints(hexcode):
    return tuple(int(v) for v in hex_to_rgb(hexcode))


def held_by(src):
    """Museum or site line, whichever the source has."""
    return src.get("museum") or src.get("site") or ""


# ------------------------------------------------------------ generated code

def write_python(pals):
    lines = ['"""Palette data written by tools/build.py. Edit palettes/*.json instead."""',
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
    lines = ["# Palette data written by tools/build.py. Edit palettes/*.json instead.",
             "",
             "#' Complete list of Rang palettes",
             "#'",
             "#' Use names(rang_palettes) for the available names and rang() to build",
             "#' a palette. Each entry holds the colors, the discrete pick order and a",
             "#' project CVD separation flag.",
             "#'",
             "#' @export",
             "rang_palettes <- list("]
    for p in pals:
        cols = ", ".join(f'"{c}"' for c in p["colors"])
        order = ", ".join(str(v) for v in p["order"])
        flag = "TRUE" if p["colorblind"] else "FALSE"
        src = p["source"]
        cite = f'{src["title"]}, {src["date"]}, {held_by(src)}, {src["url"]}'
        cite = cite.replace("\\", "\\\\").replace('"', '\\"')
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


def write_hecras(pals):
    """Write individual and combined HEC-RAS interface import files."""
    make_hecras_ramp.write_files(pals, REPO_ROOT / "hecras")


def write_geolibre(pals):
    """Write color lists suited to GeoLibre's custom color controls.

    GeoLibre accepts pasted anchor colors for raster ramps. Vector class
    colors are edited as individual stops, so the bundle also includes the
    exact continuous samples and Rang's well separated categorical picks.
    """
    gdir = REPO_ROOT / "geolibre"
    gdir.mkdir(exist_ok=True)
    entries = {}
    text_lines = [
        "Rang color lists for GeoLibre",
        "",
        "Paste raster anchors into a raster Custom color ramp.",
        "Use graduated colors for ordered numeric classes.",
        "Use categorical colors for distinct classes.",
        "",
    ]
    for p in pals:
        name = p["name"]
        colors = p["colors"]
        categories = {
            str(n): [color for color, rank in zip(colors, p["order"]) if rank <= n]
            for n in range(2, len(colors) + 1)
        }
        graduated = {str(n): interpolate(colors, n) for n in range(2, 13)}
        entries[name] = {
            "raster_anchors": colors,
            "graduated": graduated,
            "categorical": categories,
        }
        text_lines.extend([
            name,
            f'  raster anchors: {", ".join(colors)}',
        ])
        for n, values in graduated.items():
            text_lines.append(f'  graduated {n}: {", ".join(values)}')
        for n, values in categories.items():
            text_lines.append(f'  categorical {n}: {", ".join(values)}')
        text_lines.append("")

    payload = {
        "format": "rang-geolibre-colors",
        "version": 1,
        "license": "CC0-1.0",
        "palettes": entries,
    }
    json_out = gdir / "Rang.json"
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {json_out}")
    text_out = gdir / "Rang.txt"
    text_out.write_text("\n".join(text_lines), encoding="utf-8")
    print(f"wrote {text_out}")


# ------------------------------------------------------------- palette page

def cvd_table(colors):
    rows = ["| vision | min CIEDE2000 | mean |", "|---|---|---|"]
    for kind in VISION_TYPES:
        mn, mean = pairwise_min_mean(colors, kind)
        rows.append(f"| {VISION_LABELS[kind]} | {mn:.1f} | {mean:.1f} |")
    return "\n".join(rows)


def source_section(src):
    citation = src.get("citation")
    if not citation:
        citation = f'{src["title"]}, {src["date"]}. {src.get("geography", "")}.'
    parts = [citation]
    if src.get("artist") and src.get("museum"):
        parts.append(src["artist"].strip().rstrip(".") + ".")
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
    if src.get("artist_url"):
        parts.append(f'[Artist biography]({src["artist_url"]}).')
    if src.get("note"):
        parts.append(src["note"].strip().rstrip(".") + ".")
    text = "\n".join(parts)

    if src.get("public_domain"):
        photo_url = src.get("download_url", src["image"])
        photo_note = (f'[Object page]({src["url"]}) and '
                      f'[full resolution photo]({photo_url}), released by '
                      "the museum under open access.")
    else:
        rights = src.get("rights", "photo used with permission").strip().rstrip(".")
        rights = rights[0].upper() + rights[1:]
        label = src.get("reference_label", "Reference page")
        photo_note = f'[{label}]({src["url"]}). {rights}.'
    return text + "\n\n" + photo_note


def context_block(pal):
    src = pal["source"]
    if not src.get("context_image"):
        return ""
    rel = "../../" + src["context_image"].replace("\\", "/")
    caption = src.get("context_caption", "The work in its setting")
    details = []
    if src.get("context_credit"):
        details.append(src["context_credit"].strip().rstrip(".") + ".")
    if src.get("context_url"):
        details.append(f'[Context photograph source]({src["context_url"]}).')
    if src.get("context_rights"):
        details.append(src["context_rights"].strip().rstrip(".") + ".")
    attribution = "\n\n" + " ".join(details) if details else ""
    return (f"\n## The setting\n\n![{caption}]({rel})\n\n{caption}."
            f"{attribution}\n")


def craft_block(pal):
    """Optional section on how the art form is made and where it comes from."""
    craft = pal.get("craft")
    if not craft:
        return ""
    if isinstance(craft, str):
        craft = [craft]
    return "\n## The craft\n\n" + "\n\n".join(craft) + "\n"


def story_block(pal):
    """Optional account of the scene or source text behind an artwork."""
    story = pal.get("story")
    if not story:
        return ""
    if isinstance(story, str):
        story = [story]
    return "\n## The story\n\n" + "\n\n".join(story) + "\n"


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

    hex_rows = ["| position | hex | drawn from |" + (" nearest sample |" if presence else ""),
                "|---|---|---|" + ("---|" if presence else "")]
    for i, (c, note) in enumerate(zip(colors, notes), start=1):
        row = f"| {i} | `{c}` | {note} |"
        if presence:
            row += f" {presence[c][0]:.1f} |"
        hex_rows.append(row)

    wc = worst_case(colors)
    if pal["colorblind"]:
        separation_note = (
            f"The lowest score is {wc:.1f}. Rang's cutoff is "
            f"{COLORBLIND_THRESHOLD:.0f}, so all pairwise scores are above it."
        )
        if 0 <= wc - COLORBLIND_THRESHOLD < 0.1:
            separation_note += (
                f" The difference is less than 0.1, so treat {name} as borderline."
            )
    else:
        separation_note = (
            f"The lowest score is {wc:.1f}, below Rang's cutoff of "
            f"{COLORBLIND_THRESHOLD:.0f}."
        )
    separation_note += (
        "\n\nWhen you ask for fewer colors, the stored pick order spreads them "
        "out. Check the finished figure when color distinction matters."
    )
    bits = []
    if pal.get("persian"):
        bits.append(f'Persian: {pal["persian"]}')
    if pal.get("pronunciation"):
        bits.append(f'say it {pal["pronunciation"]}')
    say = f' ({", ".join(bits)})' if bits else ""
    about = f'\n{pal["about"]}\n' if pal.get("about") else ""

    if pal.get("samples") == "water":
        samples_note = (
            "Both maps use USGS data. The first shows the 100 year high flood\n"
            "profile for the creeks at Ithaca, New York. The second follows Fall\n"
            "Creek, with stream widths drawn from NHDPlusV2 order in USGS Fabric.\n"
            "The watershed interior has no fill.\n"
            f"Run `python tools/make_samples.py {palette_slug(name)}` to remake them.")
    else:
        samples_note = (
            "The rainfall map uses one day of NOAA AORC precipitation on a roughly 1 km grid.\n"
            f"Run `python tools/make_samples.py {palette_slug(name)}` to remake the plots. Add\n"
            "`--dem your_dem.tif` to use your own elevation raster.")

    body = f"""# {name}{say}

![{name} swatch](swatch.png)
{about}
## Source

{source_section(src)}
{story_block(pal)}{context_block(pal)}{craft_block(pal)}
## Colors

{chr(10).join(hex_rows)}

The last column shows the CIEDE2000 distance to the closest sampled color in
the source photo. Lower numbers mean a closer match.

## The palette beside the artwork

![{name} preview](preview.png)

## Extraction regions

![{name} extraction regions](regions.png)

These are the saved sampling areas used for CIELAB k-means. The exact pixel
coordinates, normalized coordinates and k values are recorded in the
[{name} recipe](../../recipes/{palette_slug(name)}.json). The regions make the
extraction repeatable. Choosing and refining the final colors still depends
on the artwork and the contributor's eye.

## Sample plots

![{name} samples](samples.png)

{samples_note}

## Separation and color vision

{cvd_table(colors)}

{separation_note}

## Use it

Python

```python
import rang

rang.rang("{name}", 5)              # five well separated colors
rang.cmap("{name}")                 # smooth matplotlib colormap
rang.cmap("{name}", 6)              # six fixed steps for classified data

rang.register()                     # then use it anywhere by name
data.plot(cmap="rang:{name}")
```

R

```r
library(Rang)
library(ggplot2)

rang("{name}", 5)                   # five well separated colors

# categories
ggplot(df, aes(group, value, fill = group)) +
  geom_col() +
  scale_fill_rang_d("{name}")

# a numeric variable
ggplot(df, aes(x, y, color = value)) +
  geom_point() +
  scale_color_rang_c("{name}")
```

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/{name}.gpl](../../qgis/{name}.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS users can import
[hecras/Rang-{name}.xml](../../hecras/Rang-{name}.xml), see the
[HEC-RAS guide](../../hecras/README.md). GeoLibre users can copy colors from
[geolibre/Rang.txt](../../geolibre/Rang.txt), with steps for raster and vector
layers in the [GeoLibre guide](../../geolibre/README.md).
"""
    out = REPO_ROOT / "docs" / palette_slug(name) / "README.md"
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
    line = f'{src["title"]}, {src["date"]}.'
    if src.get("dimensions"):
        line = f'{src["title"]}, {src["date"]}, {src["dimensions"]}.'
    if held_by(src):
        line += f' {held_by(src)}.'
    if src.get("credit") and not src.get("museum"):
        line += f' {src["credit"]}.'
    about = f'\n{pal["about"]}\n' if pal.get("about") else ""
    return f"""### {name}

![{name}, the artwork and its palette](docs/{palette_slug(name)}/card.png)

{line} [Reference]({src["url"]}){say}
{about}
`{" ".join(pal["colors"])}`

[Sample plots and full details](docs/{palette_slug(name)}/README.md)
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
    path = PALETTE_DIR / f"{palette_slug(name)}.json"
    pal = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    if "order" not in pal or len(pal["order"]) != len(pal["colors"]):
        pal["order"] = greedy_order(pal["colors"])
        changed = True
        print(f"computed order for {pal['name']}: {pal['order']}")
    computed_flag = worst_case(pal["colors"]) >= COLORBLIND_THRESHOLD
    if pal.get("colorblind") is not computed_flag:
        pal["colorblind"] = computed_flag
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
    logo_path = make_logo.save_logo(
        make_logo.DEFAULT_OUTPUT_PATH, 1024, "transparent"
    )
    print(f"wrote {logo_path}")
    write_python(pals)
    write_r(pals)
    write_qgis(pals)
    stylx_written = make_stylx.write_stylx(pals)
    write_hecras(pals)
    write_geolibre(pals)

    for name in targets:
        if not args.skip_images:
            make_preview.main(palette_slug(name))
            make_region_overlay.render_palette(palette_slug(name))
            make_samples.main(palette_slug(name))
        write_docs_page(load_palette(palette_slug(name)))

    update_readme(pals)
    if not stylx_written:
        raise SystemExit("build incomplete because arcgis/Rang.stylx was locked")
    print("\nbuild finished")


if __name__ == "__main__":
    main()
