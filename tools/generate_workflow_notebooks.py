"""Regenerate the numbered upload-based Colab notebooks in tools/.

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


def title(path, number, name, summary):
    url_path = path.as_posix()
    return markdown(f"""
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/{url_path})

<div style="font-family:Arial,sans-serif">

# {number}. {name}

{summary}

Files move between your computer and Colab through the upload and download
buttons. Each step tells you which file to choose and what to save.

Created by **Mohsen Tahmasebi Nasab, PhD**<br>
[hydromohsen.com](https://hydromohsen.com)

Copyright and license holder: Mohsen Tahmasebi Nasab. Notebook code is
licensed under the repository's MIT License. Rang palette data follows the
CC0 dedication described in the licensing guide. Source images keep their own
rights and reuse terms.

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
import zipfile
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

def receive_file(local_path, label, canonical_stem=None):
    if IN_COLAB:
        print(f"Choose {{label}} from your computer")
        uploaded = files.upload()
        if len(uploaded) != 1:
            raise ValueError("Upload exactly one file")
        filename, data = next(iter(uploaded.items()))
        uploaded_name = Path(filename).name
        if canonical_stem:
            suffix = Path(uploaded_name).suffix.lower()
            if not suffix:
                raise ValueError("The uploaded file needs a filename extension")
            output = WORK_DIR / f"{{canonical_stem}}{{suffix}}"
        else:
            output = WORK_DIR / uploaded_name
        output.write_bytes(data)
        return output, uploaded_name
    if not local_path:
        raise ValueError(f"Enter a local path for {{label}}")
    path = Path(local_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    if canonical_stem:
        if not path.suffix:
            raise ValueError("The source file needs a filename extension")
        output = WORK_DIR / f"{{canonical_stem}}{{path.suffix.lower()}}"
        if path != output.resolve():
            output.write_bytes(path.read_bytes())
        return output, path.name
    return path, path.name

def load_workflow_zip(local_path):
    archive, _ = receive_file(
        local_path, "the workflow ZIP from the previous notebook"
    )
    with zipfile.ZipFile(archive) as handle:
        total = 0
        for item in handle.infolist():
            member = Path(item.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError("The workflow ZIP contains an unsafe path")
            total += item.file_size
        if total > 200 * 1024 * 1024:
            raise ValueError("The workflow ZIP expands beyond 200 MB")
        handle.extractall(WORK_DIR)
    if not RECIPE_PATH.exists():
        raise FileNotFoundError("The uploaded ZIP does not contain the expected recipe")
    return archive

def make_workflow_zip():
    archive = WORK_DIR / f"{{PALETTE_SLUG}}-workflow.zip"
    return make_workflow_archive(RECIPE_PATH, WORK_DIR, archive)

def offer_download(path):
    print("Saved:", path)
    if IN_COLAB:
        files.download(str(path))

print("Working folder:", WORK_DIR)
''', tag="setup", hidden=True)


def start_cells(example, first=False):
    slug = "kashan" if example else "your-palette"
    cells = [
        banner("YOUR INPUT", "Give the palette a short filename. Use the same name in all seven notebooks."),
        code(f'''PALETTE_SLUG = "{slug}" #@param {{type:"string"}}
DOWNLOAD_UPDATED_ZIP = True #@param {{type:"boolean"}}''', "user-input"),
        embedded_runtime(),
    ]
    if not first:
        local_zip = ("cache/notebook-upload/kashan/kashan-workflow.zip"
                     if example else "")
        cells += [
            banner("YOUR INPUT", "Upload the workflow ZIP downloaded from the previous notebook. Local Jupyter users can enter its path."),
            code(f'''LOCAL_WORKFLOW_ZIP = "{local_zip}" #@param {{type:"string"}}
load_workflow_zip(LOCAL_WORKFLOW_ZIP)
recipe = read_json(RECIPE_PATH)
print(f'Loaded {{recipe["palette"]}} with {{len(recipe["regions"])}} regions')''',
                 "user-input"),
        ]
    return cells


def handoff_cells(final=False):
    wording = ("Download the final workflow ZIP for your contribution files."
               if final else
               "Download the updated workflow ZIP. Upload it in the next notebook.")
    return [
        banner("SAVE YOUR WORK", wording),
        code('''
workflow_zip = make_workflow_zip()
if DOWNLOAD_UPDATED_ZIP:
    offer_download(workflow_zip)
else:
    print("Workflow ZIP:", workflow_zip)
'''),
    ]


def notebook(path, cells):
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


def step_01(path, example):
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
    cells = [title(path, "01", "Upload the image and define regions",
                   "Upload one artwork image, read its pixel coordinates, and mark the regions that matter to you.")]
    cells += start_cells(example, first=True)
    cells += [
        banner("YOUR INPUT", "Upload the artwork from your computer. Local Jupyter users can enter the image path. Also enter the palette name and object page."),
        code(f'''
PALETTE_NAME = "{palette_name}" #@param {{type:"string"}}
LOCAL_IMAGE_PATH = "{local_image}" #@param {{type:"string"}}
SOURCE_REFERENCE = "{reference}" #@param {{type:"string"}}

source_path, original_filename = receive_file(
    LOCAL_IMAGE_PATH, "the artwork image", canonical_stem="source"
)
source_image = open_rgb(source_path)
print("Image size:", source_image.size)
''', "user-input"),
        markdown("""
In Colab, drag boxes directly over the image. Each box gets an ID, name, k
value, and note. Use Undo or Delete when a box does not feel right, then click
**Use these regions**. The drawer converts the boxes to original image pixels.
"""),
        banner("YOUR DECISION", "Draw the regions over the artwork. The Kashan example can also use its saved boxes for an exact replay."),
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
    show_source(source_path, PALETTE_NAME)

print(f"{{len(REGIONS)}} regions ready")
for number, region in enumerate(REGIONS, start=1):
    print(f'{{number}}. {{region["label"]}}, k={{region["k"]}}')''', "user-decision"),
        code('''
recipe = create_recipe(
    PALETTE_NAME, source_path.name, source_path, REGIONS, RECIPE_PATH
)
recipe["source"]["reference"] = SOURCE_REFERENCE
recipe["source"]["original_filename"] = original_filename
write_json(RECIPE_PATH, recipe)
overlay_path = WORK_DIR / "regions.png"
region_overlay(RECIPE_PATH, WORK_DIR, overlay_path)
print("Saved recipe:", RECIPE_PATH)
print("Saved region overlay:", overlay_path)
'''),
        markdown("""
Look at the overlay before moving on. If a box includes a frame, caption,
glare, or large background that you do not want, change the box and rerun the
last two cells.
"""),
    ]
    cells += handoff_cells()
    notebook(path, cells)


def step_02(path, example):
    cells = [title(path, "02", "Extract colors with k-means",
                   "Upload the step 01 ZIP, run k-means in every region, and review the candidate sheet.")]
    cells += start_cells(example)
    cells += [
        code('''region_overlay(RECIPE_PATH, WORK_DIR, WORK_DIR / "regions.png")'''),
        markdown("""
Each region is clustered in CIELAB. The candidate sheet orders clusters by
their share within that region. A large region does not get more authority
than a small region. The rows are evidence for your decision, not a finished
palette.
"""),
        banner("YOUR DECISION", "Choose whether this run should become the accepted candidate snapshot."),
        code('''ACCEPT_THIS_RUN = True #@param {type:"boolean"}''', "user-decision"),
        code('''
candidates = save_candidates(RECIPE_PATH, WORK_DIR, accept=ACCEPT_THIS_RUN)
print(f"Extracted {len(candidates)} candidates")
for candidate in candidates:
    print(candidate["id"], candidate["hex"],
          f'{candidate["share"]:.1f}%')
print("Candidate sheet:", WORK_DIR / "candidates.png")
'''),
    ]
    cells += handoff_cells()
    notebook(path, cells)


def step_03(path, example):
    if example:
        selection_cell = '''SELECTIONS = [
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
        selection_cell = '''CANDIDATES_BY_REGION = {}
for candidate in candidates:
    CANDIDATES_BY_REGION.setdefault(candidate["region"], []).append(candidate)

STARTING_IDS = []
largest_region = max(len(items) for items in CANDIDATES_BY_REGION.values())
for rank in range(largest_region):
    for items in CANDIDATES_BY_REGION.values():
        if rank < len(items):
            STARTING_IDS.append(items[rank]["id"])

# Replace IDs or change their order after looking at the candidate sheet.
SELECTED_IDS = STARTING_IDS[:5]

candidate_lookup = {item["id"]: item for item in candidates}
SELECTIONS = [
    {
        "candidate": candidate_id,
        "note": f'write where this color appears in {candidate_lookup[candidate_id]["region_label"]}',
    }
    for candidate_id in SELECTED_IDS
]

print("Starting selection")
for selection in SELECTIONS:
    item = candidate_lookup[selection["candidate"]]
    print(item["id"], item["hex"], item["region_label"])'''
    cells = [title(path, "03", "Curate the palette",
                   "Upload the step 02 ZIP, choose five to twelve candidates, and arrange the ramp.")]
    cells += start_cells(example)
    cells += [
        code('''
candidates = recipe.get("accepted_candidates", [])
if not candidates:
    raise ValueError("Run notebook 02 and accept the extraction first")
candidate_figure = candidate_sheet(candidates, WORK_DIR / "candidates.png")
'''),
        markdown("""
Choose colors that carry the character of the artwork and can do useful work
in a figure. A frequent color does not have to be selected. A small detail can
be central to the palette. The order below becomes the continuous ramp order.
"""),
        banner("YOUR DECISION", "List candidate IDs in your chosen ramp order. Write one note per color saying where it comes from."),
        code(selection_cell, "user-decision"),
        code('''
recipe = save_curation(RECIPE_PATH, SELECTIONS)
colors = recipe["expected"]["colors"]
before_after_sheet(colors, colors)
for item in recipe["curation"]["colors"]:
    print(item["id"], item["from"], item["current"], item["note"])
'''),
    ]
    cells += handoff_cells()
    notebook(path, cells)


def step_04(path, example):
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
    {"target": "p01", "delta": {"L": 2, "C": 0, "H": 0},
     "reason": "say what looks better and where you see it in the artwork"},
]'''
    cells = [title(path, "04", "Adjust colors",
                   "Upload the step 03 ZIP, make careful LCh changes, and record every reason.")]
    cells += start_cells(example)
    cells += [
        code('''
if "curation" not in recipe:
    raise ValueError("Run notebook 03 and save the candidate choices first")
current = recipe["expected"]["colors"]
before_after_sheet(current, current)
'''),
        markdown("""
L changes lightness, C changes chroma, and H rotates hue in degrees. Small
changes are easier to explain and review. Trust the artwork and the finished
visualization. The cluster center is a starting point, not a command.
"""),
        banner("YOUR DECISION", "Edit the adjustment list. Keep only changes that improve the palette and give each one a short reason."),
        code(f'''REPLACE_SAVED_ADJUSTMENTS = True #@param {{type:"boolean"}}

ADJUSTMENTS = {adjustments}''', "user-decision"),
        code('''
adjusted = apply_adjustments(
    RECIPE_PATH, ADJUSTMENTS, WORK_DIR / "adjustments.png",
    reset=REPLACE_SAVED_ADJUSTMENTS
)
for item in adjusted["curation"]["colors"]:
    print(item["id"], item["source_hex"], "to", item["current"])
'''),
    ]
    cells += handoff_cells()
    notebook(path, cells)


def step_05(path, example):
    cells = [title(path, "05", "Check the palette",
                   "Upload the step 04 ZIP and review source distance, separation, and pick order.")]
    cells += start_cells(example)
    cells += [
        code('''
report = check_recipe(RECIPE_PATH, WORK_DIR, WORK_DIR / "check-report.json")
print(report["palette"], *report["colors"])
print("Suggested pick order:", report["suggested_pick_order"])
print("Color vision flag:", report["colorblind"])
print()
for view, values in report["viewing"].items():
    print(f'{view:14s} min={values["minimum"]:.1f} mean={values["mean"]:.1f}')
print()
for color, values in report["source_presence"].items():
    marker = "check" if values["nearest"] > 3 else ""
    print(color, f'nearest={values["nearest"]:.1f}', marker)
'''),
        banner("YOUR DECISION", "Read the report and look at real sample plots later. Keep meaningful colors when they serve the artwork, and explain any large source distance."),
        markdown("""
A number can point to a problem, but it cannot decide whether a palette feels
right. Return to notebooks 03 and 04 when two colors collapse together, a
color drifts too far from the source, or the ramp loses the mood of the work.
"""),
    ]
    cells += handoff_cells()
    notebook(path, cells)


def step_06(path, example):
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
    cells = [title(path, "06", "Prepare the palette files",
                   "Upload the step 05 ZIP, enter the source record, and create the palette JSON.")]
    cells += start_cells(example)
    cells += [
        banner("YOUR INPUT", "Enter the artwork metadata exactly as the source page gives it. Check the rights fields carefully."),
        code(f"PALETTE_METADATA = {metadata}", "user-input"),
        code('''
draft_path = WORK_DIR / f"{PALETTE_SLUG}-palette.json"
draft = palette_draft(RECIPE_PATH, PALETTE_METADATA, draft_path)
print("Palette JSON:", draft_path)
print("Final colors:", *draft["colors"])
'''),
        markdown("""
The ZIP now contains the source image, recipe, reports, and palette JSON. Copy
the recipe to `recipes/<name>.json` and the palette JSON to
`palettes/<name>.json` in your local Rang checkout. Then run
`python tools/build.py <name>` from the repository.
"""),
    ]
    cells += handoff_cells()
    notebook(path, cells)


def step_07(path, example):
    cells = [title(path, "07", "Replay and verify",
                   "Upload the step 06 ZIP and reproduce the accepted extraction and adjustments.")]
    cells += start_cells(example)
    cells += [
        code('''
result = verify_recipe(RECIPE_PATH, WORK_DIR)
for key, value in result.items():
    print(f"{key}: {value}")
if not result["verified"]:
    raise ValueError("The saved workflow did not reproduce exactly")
print("The recipe reproduced the accepted candidates and final colors.")
'''),
        markdown("""
Verification is mechanical. It confirms that the saved image, regions,
k-means settings, choices, and adjustments still lead to the accepted colors.
It does not claim that another artist would make the same choices.
"""),
    ]
    cells += handoff_cells(final=True)
    notebook(path, cells)


def build_set(directory, example):
    names = [
        ("01_define_regions.ipynb", step_01),
        ("02_extract_colors.ipynb", step_02),
        ("03_curate_palette.ipynb", step_03),
        ("04_adjust_colors.ipynb", step_04),
        ("05_check_palette.ipynb", step_05),
        ("06_build_palette.ipynb", step_06),
        ("07_replay_and_verify.ipynb", step_07),
    ]
    for filename, writer in names:
        path = pathlib.Path(directory) / filename
        writer(path, example)
        print(f"wrote {ROOT / path}")


def main():
    build_set(pathlib.Path("tools/notebooks"), example=False)
    build_set(pathlib.Path("tools/examole"), example=True)


if __name__ == "__main__":
    main()
