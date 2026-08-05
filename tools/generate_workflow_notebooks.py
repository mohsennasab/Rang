"""Regenerate the complete upload-based Colab workflow notebooks.

Created by Mohsen Tahmasebi Nasab, PhD
https://hydromohsen.com

Copyright (c) 2026 Mohsen Tahmasebi Nasab
Licensed under the MIT License in the repository root.
"""
import base64
import json
import pathlib
import zlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAIN_NOTEBOOK = pathlib.Path("tools/notebooks/rang_palette_workflow.ipynb")
EXAMPLE_NOTEBOOK = pathlib.Path("tools/example/kashan_palette_workflow.ipynb")


def _source(text):
    return text.strip("\n").splitlines(keepends=True)


def markdown(text):
    return {"cell_type": "markdown", "metadata": {}, "source": _source(text)}


def code(text, tag=None, hidden=False):
    metadata = {"tags": [tag]} if tag else {}
    if hidden:
        metadata.update({
            "cellView": "form",
            "jupyter": {"source_hidden": True},
        })
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": metadata,
        "outputs": [],
        "source": _source(text),
    }


def banner(kind, text):
    color = "#fff3cd" if kind == "YOUR INPUT" else "#d9edf7"
    return markdown(
        f'<div style="font-family:Arial,sans-serif;background:{color};padding:14px">'
        f"<strong>{kind}</strong><br>{text}</div>"
    )


def title(path, example):
    url_path = path.as_posix()
    heading = "Kashan palette workflow" if example else "Rang palette workflow"
    introduction = (
        "This completed example reproduces the published Kashan palette. "
        "You can keep the saved decisions or change them as you work."
        if example else
        "This notebook takes one artwork image through region drawing, "
        "color extraction, curation, adjustment, checking, file preparation, "
        "and replay."
    )
    return markdown(f"""
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/{url_path})

<div style="font-family:Arial,sans-serif">

# {heading}

{introduction}

Upload the artwork once. All seven stages run in this notebook, and the final
workflow ZIP downloads after verification.

Created by **Mohsen Tahmasebi Nasab, PhD**<br>
[hydromohsen.com](https://hydromohsen.com)

Copyright and license holder: Mohsen Tahmasebi Nasab. Notebook code is
licensed under the repository's MIT License. Rang palette data follows the
CC0 dedication described in the licensing guide. Source images keep their own
rights and reuse terms.

</div>
""")


def section(number, name, summary):
    return markdown(f"""
<div style="font-family:Arial,sans-serif">

## {number}. {name}

{summary}

</div>
""")


def embedded_runtime():
    sources = {}
    for name in ("colorlib", "adjust_colors", "notebook_workflow"):
        sources[name] = (ROOT / "tools" / f"{name}.py").read_text(encoding="utf-8")
    encoded = json.dumps(sources, ensure_ascii=False).encode("utf-8")
    packed = base64.b85encode(zlib.compress(encoded, level=9)).decode("ascii")
    return code(f'''#@title Set up this notebook
import base64
import json
import subprocess
import sys
import types
import zlib
from pathlib import Path

IN_COLAB = False
try:
    from google.colab import files
    IN_COLAB = True
except ImportError:
    pass

try:
    import matplotlib
    import numpy
    import PIL
    import sklearn
except ImportError:
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q",
        "numpy", "pillow", "scikit-learn", "matplotlib"
    ], check=True)

PACKED_MODULE_SOURCES = {json.dumps(packed)}
MODULE_SOURCES = json.loads(zlib.decompress(
    base64.b85decode(PACKED_MODULE_SOURCES)).decode("utf-8"))
for module_name in ("colorlib", "adjust_colors", "notebook_workflow"):
    module = types.ModuleType(module_name)
    module.__file__ = f"{{module_name}}.py"
    sys.modules[module_name] = module
    exec(compile(MODULE_SOURCES[module_name], module.__file__, "exec"),
         module.__dict__)

from notebook_workflow import *

PALETTE_SLUG = palette_slug(PALETTE_SLUG)
if IN_COLAB:
    WORK_DIR = Path("/content/rang-workflow") / PALETTE_SLUG
else:
    WORK_DIR = Path.cwd() / "cache" / "notebook-upload" / PALETTE_SLUG
WORK_DIR.mkdir(parents=True, exist_ok=True)
RECIPE_PATH = WORK_DIR / f"{{PALETTE_SLUG}}-recipe.json"
use_arial()

def receive_source(local_path):
    if IN_COLAB:
        print("Choose the artwork image from your computer")
        uploaded = files.upload()
        if len(uploaded) != 1:
            raise ValueError("Upload exactly one image")
        filename, data = next(iter(uploaded.items()))
        original_name = Path(filename).name
        suffix = Path(original_name).suffix.lower()
        if not suffix:
            raise ValueError("The uploaded image needs a filename extension")
        output = WORK_DIR / f"source{{suffix}}"
        output.write_bytes(data)
        return output, original_name
    if not local_path:
        raise ValueError("Enter a local path for the artwork image")
    path = Path(local_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if not path.suffix:
        raise ValueError("The source image needs a filename extension")
    output = WORK_DIR / f"source{{path.suffix.lower()}}"
    if path != output.resolve():
        output.write_bytes(path.read_bytes())
    return output, path.name

def make_final_zip():
    archive = WORK_DIR / f"{{PALETTE_SLUG}}-workflow.zip"
    return make_workflow_archive(RECIPE_PATH, WORK_DIR, archive)

def offer_download(path):
    print("Saved:", path)
    if IN_COLAB:
        files.download(str(path))

print("Working folder:", WORK_DIR)
''', tag="setup", hidden=True)


def setup_cells(path, example):
    slug = "kashan" if example else "your-palette"
    return [
        title(path, example),
        markdown("""
### Contents

01. Upload the image and define regions
02. Extract colors with k-means
03. Curate the palette
04. Adjust colors
05. Check the palette
06. Prepare the palette files
07. Replay, verify, and download
"""),
        banner("YOUR INPUT", "Give the palette a short filename. You enter it once for the complete workflow."),
        code(f'''PALETTE_SLUG = "{slug}" #@param {{type:"string"}}
DOWNLOAD_FINAL_ZIP = True #@param {{type:"boolean"}}''', "user-input"),
        embedded_runtime(),
    ]


def step_01_cells(example):
    if example:
        palette_name = "Kashan"
        local_image = "cache/DT5450.jpg"
        reference = "https://www.metmuseum.org/art/collection/search/451470"
        interactive_default = "False"
        starting_default = "True"
        regions = '''[
    {"id": "top-border", "label": "Top border", "box": [200, 100, 2350, 650], "k": 8,
     "note": "Warm border ground and floral outlines"},
    {"id": "upper-inner-field", "label": "Upper inner field", "box": [550, 600, 2000, 1350], "k": 8,
     "note": "Rose field and surrounding motifs"},
    {"id": "central-medallion", "label": "Central medallion", "box": [650, 1650, 1900, 2700], "k": 8,
     "note": "Indigo, blue, ivory, gold, and red details"},
    {"id": "lower-inner-field", "label": "Lower inner field", "box": [550, 2700, 2000, 3300], "k": 8,
     "note": "Field colors away from the medallion"},
    {"id": "left-guard-borders", "label": "Left guard borders", "box": [40, 650, 500, 3150], "k": 8,
     "note": "Sage, blue, and warm border colors"},
]'''
    else:
        palette_name = "Your palette name"
        local_image = ""
        reference = "PASTE THE OBJECT PAGE URL HERE"
        interactive_default = "True"
        starting_default = "False"
        regions = '''[
    {"id": "main-detail", "label": "Main detail", "box": [100, 100, 600, 600], "k": 8,
     "note": "Say why this part of the artwork matters"},
]'''
    return [
        section("01", "Upload the image and define regions",
                "Upload one artwork image and draw the regions that matter to you."),
        banner("YOUR INPUT", "Upload the artwork. Also enter its name and object page."),
        code(f'''PALETTE_NAME = "{palette_name}" #@param {{type:"string"}}
LOCAL_IMAGE_PATH = "{local_image}" #@param {{type:"string"}}
SOURCE_REFERENCE = "{reference}" #@param {{type:"string"}}

source_path, original_filename = receive_source(LOCAL_IMAGE_PATH)
source_image = open_rgb(source_path)
print("Image size:", source_image.size)''', "user-input"),
        markdown("""
Drag boxes directly over the image in Colab. Each box gets an ID, name, k
value, and note. Use Undo or Delete when a box does not feel right, then click
**Use these regions**. The drawer converts each box to original image pixels.
"""),
        banner("YOUR DECISION", "Draw the sampling regions. The Kashan example can use its saved boxes for an exact replay."),
        code(f'''DRAW_REGIONS_INTERACTIVELY = {interactive_default} #@param {{type:"boolean"}}
START_WITH_TEMPLATE_BOXES = {starting_default} #@param {{type:"boolean"}}

REGION_TEMPLATE = {regions}

if DRAW_REGIONS_INTERACTIVELY:
    if not IN_COLAB:
        raise RuntimeError(
            "Use the interactive drawer in Colab or edit REGION_TEMPLATE locally"
        )
    starting_regions = REGION_TEMPLATE if START_WITH_TEMPLATE_BOXES else []
    region_drawer = globals()["draw_regions_interactively"]
    REGIONS = region_drawer(source_path, starting_regions)
else:
    REGIONS = REGION_TEMPLATE
    source_figure = show_source(source_path, PALETTE_NAME)

print(f"{{len(REGIONS)}} regions ready")
for number, region in enumerate(REGIONS, start=1):
    print(f'{{number}}. {{region["label"]}}, k={{region["k"]}}')''', "user-decision"),
        code('''recipe = create_recipe(
    PALETTE_NAME, source_path.name, source_path, REGIONS, RECIPE_PATH
)
recipe["source"]["reference"] = SOURCE_REFERENCE
recipe["source"]["original_filename"] = original_filename
write_json(RECIPE_PATH, recipe)
overlay_path = WORK_DIR / "regions.png"
overlay_figure = region_overlay(RECIPE_PATH, WORK_DIR, overlay_path)
print("Saved recipe:", RECIPE_PATH)
print("Saved region overlay:", overlay_path)'''),
        markdown("""
Look at the overlay before moving on. If a box includes a frame, caption,
glare, or unwanted background, redraw it and rerun the recipe cell.
"""),
    ]


def step_02_cells():
    return [
        section("02", "Extract colors with k-means",
                "Run k-means in CIELAB within every saved region."),
        markdown("""
The candidate sheet orders clusters by their pixel share within each region.
The rows are evidence for your decision, not a finished palette.
"""),
        banner("YOUR DECISION", "Choose whether this extraction should become the accepted candidate snapshot."),
        code('''ACCEPT_THIS_RUN = True #@param {type:"boolean"}

candidates = save_candidates(RECIPE_PATH, WORK_DIR, accept=ACCEPT_THIS_RUN)
recipe = read_json(RECIPE_PATH)
print(f"Extracted {len(candidates)} candidates")
for candidate in candidates:
    print(candidate["id"], candidate["hex"], f'{candidate["share"]:.1f}%')''',
             "user-decision"),
    ]


def step_03_cells(example):
    if example:
        selections = '''SELECTIONS = [
    {"candidate": "lower-inner-field:c03", "note": "dark red, corner cartouche outlines"},
    {"candidate": "upper-inner-field:c01", "note": "rose red of the field"},
    {"candidate": "upper-inner-field:c03", "note": "terracotta"},
    {"candidate": "central-medallion:c06", "note": "golden ochre, medallion palmettes"},
    {"candidate": "upper-inner-field:c02", "note": "tan of the border ground"},
    {"candidate": "left-guard-borders:c07", "note": "ivory, medallion star and cartouches"},
    {"candidate": "top-border:c03", "note": "sage green, guard border"},
    {"candidate": "upper-inner-field:c08", "note": "mid blue, medallion lobes"},
    {"candidate": "central-medallion:c04", "note": "indigo, medallion ground"},
]'''
    else:
        selections = '''# Copy candidate IDs from the list above. Keep 5 to 12 rows.
# The row order becomes the continuous palette order.
SELECTIONS = [
    {"candidate": "PASTE_ID_HERE", "note": "say where this color appears"},
    {"candidate": "PASTE_ID_HERE", "note": "say where this color appears"},
    {"candidate": "PASTE_ID_HERE", "note": "say where this color appears"},
    {"candidate": "PASTE_ID_HERE", "note": "say where this color appears"},
    {"candidate": "PASTE_ID_HERE", "note": "say where this color appears"},
]'''
    return [
        section("03", "Curate the palette",
                "Choose five to twelve candidates and arrange the ramp yourself."),
        code('''candidates = recipe.get("accepted_candidates", [])
if not candidates:
    raise ValueError("Accept the extraction in step 02 first")
candidate_figure = candidate_sheet(candidates, WORK_DIR / "candidates.png")'''),
        markdown("""
The small cell below lists the exact region IDs and candidate numbers available
in this run. The region ID comes from the name saved in step 01. The candidate
number, such as `c04`, appears below its color in the candidate sheet.

A complete candidate ID joins those two parts with a colon and no space. For
example:

```python
{"candidate": "region-01:c04", "note": "deep blue in the central tiles"}
```

Copy the region ID and candidate number exactly. The note should say where the
color appears in the artwork. The order of the rows becomes the palette order.
You can choose more than one candidate from a region, but do not repeat the
same candidate ID.
"""),
        code('''for region in recipe["regions"]:
    region_candidates = [
        item for item in candidates if item["region"] == region["id"]
    ]
    numbers = ", ".join(item["id"].split(":")[1]
                        for item in region_candidates)
    print(f'{region["id"]} ({region["label"]}): {numbers}')'''),
        banner("YOUR DECISION", "Fill in the list with candidate IDs from above. Write where each color appears and arrange the rows in your preferred ramp order."),
        code(selections, "user-decision"),
        code('''recipe = save_curation(RECIPE_PATH, SELECTIONS)
colors = recipe["expected"]["colors"]
curated_figure = before_after_sheet(colors, colors)
for item in recipe["curation"]["colors"]:
    print(item["id"], item["from"], item["current"], item["note"])'''),
    ]


def step_04_cells(example):
    if example:
        adjustments = '''[
    {"target": "p01", "delta": {"L": -9.74945, "C": -8.81872, "H": 7.53507},
     "reason": "brings the red back to the dark cartouche outlines"},
    {"target": "p02", "delta": {"L": -1.40996, "C": -2.34678, "H": 3.58930},
     "reason": "keeps the rose close to the woven field"},
    {"target": "p03", "delta": {"L": 6.24557, "C": 6.05730, "H": 18.64681},
     "reason": "recovers the warmer terracotta details"},
    {"target": "p04", "delta": {"L": 1.94535, "C": -2.98656, "H": 1.00765},
     "reason": "softens the medallion gold"},
    {"target": "p05", "delta": {"L": -0.76169, "C": 2.65010, "H": -5.67352},
     "reason": "matches the tan border ground"},
    {"target": "p06", "delta": {"L": -6.84131, "C": 0.77734, "H": -3.80701},
     "reason": "moves the pale cluster toward the carpet ivory"},
    {"target": "p07", "delta": {"L": 9.11474, "C": 6.13820, "H": 13.36896},
     "reason": "lifts the muted guard-border green"},
    {"target": "p08", "delta": {"L": 2.79122, "C": 8.50177, "H": 3.67200},
     "reason": "restores the blue in the medallion lobes"},
    {"target": "p09", "delta": {"L": -3.80180, "C": 0.86484, "H": -5.66345},
     "reason": "deepens the indigo medallion ground"},
]'''
    else:
        adjustments = '''[
    # Example:
    # {"target": "p01", "delta": {"L": 2, "C": 0, "H": 0},
    #  "reason": "say what changed and where you see it in the artwork"},
]'''
    return [
        section("04", "Adjust colors",
                "Make deliberate LCh changes and record every reason."),
        markdown("""
Each selected color receives a palette ID in step 03. `p01` is the first row
in `SELECTIONS`, `p02` is the second row, and the numbering continues in that
order.

- `L` changes lightness. Positive values make the color lighter and negative
  values make it darker.
- `C` changes chroma, or color intensity. Positive values make it more vivid
  and negative values make it more muted.
- `H` rotates the hue in degrees. Positive and negative values move around the
  color wheel in opposite directions.

To change several palette colors, add one dictionary for each target inside
the list:

```python
ADJUSTMENTS = [
    {"target": "p01", "delta": {"L": 8, "C": 4, "H": 0},
     "reason": "lightened the blue to match the central tiles"},
    {"target": "p02", "delta": {"L": 0, "C": -6, "H": 3},
     "reason": "softened the green found in the border"},
]
```

Every row needs `L`, `C`, and `H`, even when one of them is zero. Include only
colors that need a change. Use `ADJUSTMENTS = []` when the sampled colors
already feel right.
"""),
        banner("YOUR DECISION", "Add only the adjustments that improve the palette."),
        code(f'''REPLACE_SAVED_ADJUSTMENTS = True #@param {{type:"boolean"}}

ADJUSTMENTS = {adjustments}''', "user-decision"),
        code('''adjusted = apply_adjustments(
    RECIPE_PATH, ADJUSTMENTS, WORK_DIR / "adjustments.png",
    reset=REPLACE_SAVED_ADJUSTMENTS
)
for item in adjusted["curation"]["colors"]:
    print(item["id"], item["source_hex"], "to", item["current"])'''),
    ]


def step_05_cells():
    return [
        section("05", "Check the palette",
                "Review source distance, color separation, and pick order."),
        code('''report = check_recipe(
    RECIPE_PATH, WORK_DIR, WORK_DIR / "check-report.json"
)
print(report["palette"], *report["colors"])
print("Suggested pick order:", report["suggested_pick_order"])
print("Color vision flag:", report["colorblind"])
print()
for view, values in report["viewing"].items():
    print(f'{view:14s} min={values["minimum"]:.1f} mean={values["mean"]:.1f}')
print()
for color, values in report["source_presence"].items():
    marker = "check" if values["nearest"] > 3 else ""
    print(color, f'nearest={values["nearest"]:.1f}',
          f'share within 8={values["share_within_8"]:.2f}%', marker)'''),
        markdown("""
### How to read the report

- **Minimum** is the distance between the closest pair of palette colors for
  each viewing condition. A larger number means the closest pair is easier to
  tell apart. Rang uses 8 as a practical separation check.
- **Mean** describes the average separation across all pairs. It can look good
  even when one pair is too close, so read it together with the minimum.
- **Color vision flag** is `True` when every pair stays at or above 8 under
  normal vision and the three simulated color vision conditions. `False`
  points to a pair worth reviewing. It does not automatically reject a
  palette.
- **Nearest** is the CIEDE2000 distance from a palette color to the closest
  sampled point in the artwork. A value of 3 or less is a close match. A value
  above 3 asks you to check the color and explain any deliberate adjustment.
- **Share within 8** is the percentage of sampled artwork points reasonably
  close to that color. A small share can be valid when the color comes from a
  tiny but important detail.
- **Suggested pick order** says which colors enter first when someone requests
  fewer colors. The numbers line up with `p01`, `p02`, and the remaining
  palette positions. It does not rearrange the continuous ramp you created.

The numbers help find possible problems. They cannot judge balance, mood, or
the character of the artwork. Compare the palette with the source and trust
your eyes. Return to step 03 to change the selection or order. Return to step
04 to make a careful color adjustment.
"""),
        banner("YOUR DECISION", "Judge the report and the palette together. Continue when the colors feel true to the artwork and work well in a visualization."),
    ]


def step_06_cells(example):
    if example:
        metadata = '''{
    "name": "Kashan",
    "persian": "کاشان",
    "pronunciation": "kah-SHAHN",
    "position": 1,
    "source": {
        "title": "Silk Kashan Carpet",
        "artist": "",
        "date": "16th century",
        "geography": "Made in Iran, probably Kashan",
        "medium": "Silk (warp, weft and pile), asymmetrically knotted pile",
        "museum": "The Metropolitan Museum of Art, New York",
        "department": "Islamic Art",
        "accession": "58.46",
        "credit": "Gift of Mrs. Douglas M. Moffat, 1958",
        "url": "https://www.metmuseum.org/art/collection/search/451470",
        "image": "https://images.metmuseum.org/CRDImages/is/original/DT5450.jpg",
        "card_image": "sources/kashan/card.jpg",
        "public_domain": True
    }
}'''
    else:
        metadata = '''{
    "name": "YourPalette",
    "persian": "نام فارسی",
    "pronunciation": "how to say it",
    "about": "A short, personal description of the palette",
    "source": {
        "title": "Artwork title",
        "artist": "Artist when known",
        "date": "Date",
        "geography": "Place",
        "medium": "Materials",
        "museum": "Museum or collection",
        "accession": "Accession number",
        "credit": "Credit line",
        "url": "OBJECT PAGE URL",
        "image": "SOURCE IMAGE URL",
        "public_domain": True
    }
}'''
    return [
        section("06", "Prepare the palette files",
                "Enter the source record and create the palette JSON."),
        banner("YOUR INPUT", "Enter the artwork metadata exactly as the source page gives it. Check the rights fields carefully."),
        code(f"PALETTE_METADATA = {metadata}", "user-input"),
        code('''draft_path = WORK_DIR / f"{PALETTE_SLUG}-palette.json"
draft = palette_draft(RECIPE_PATH, PALETTE_METADATA, draft_path)
print("Palette JSON:", draft_path)
print("Final colors:", *draft["colors"])'''),
        markdown("""
The final ZIP contains the source image, recipe, working figures, report, and
palette JSON. Copy the recipe to `recipes/<name>.json` and the palette JSON to
`palettes/<name>.json` in a local Rang checkout. Then run
`python tools/build.py <name>` from the repository.
"""),
    ]


def step_07_cells():
    return [
        section("07", "Replay, verify, and download",
                "Reproduce the accepted extraction and adjustments before saving."),
        code('''result = verify_recipe(RECIPE_PATH, WORK_DIR)
for key, value in result.items():
    print(f"{key}: {value}")
if not result["verified"]:
    raise ValueError("The saved workflow did not reproduce exactly")
print("The recipe reproduced the accepted candidates and final colors.")'''),
        banner("SAVE YOUR WORK", "Download the complete workflow ZIP. This is the only ZIP download in the notebook."),
        code('''workflow_zip = make_final_zip()
if DOWNLOAD_FINAL_ZIP:
    offer_download(workflow_zip)
else:
    print("Workflow ZIP:", workflow_zip)'''),
    ]


def notebook(path, example):
    cells = setup_cells(path, example)
    cells += step_01_cells(example)
    cells += step_02_cells()
    cells += step_03_cells(example)
    cells += step_04_cells(example)
    cells += step_05_cells()
    cells += step_06_cells(example)
    cells += step_07_cells()
    value = {
        "cells": cells,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    output = ROOT / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=1, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    print(f"wrote {output}")


def main():
    notebook(MAIN_NOTEBOOK, example=False)
    notebook(EXAMPLE_NOTEBOOK, example=True)


if __name__ == "__main__":
    main()
