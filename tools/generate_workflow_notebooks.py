"""Regenerate the numbered Colab notebooks in tools/.

Created by Mohsen Tahmasebi Nasab, PhD
https://hydromohsen.com

Copyright (c) 2026 Mohsen Tahmasebi Nasab
Licensed under the MIT License in the repository root.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "tools" / "notebooks"
EXAMPLE_DIR = ROOT / "tools" / "examole"


def _source(text):
    return text.strip("\n").splitlines(keepends=True)


def markdown(text):
    return {"cell_type": "markdown", "metadata": {}, "source": _source(text)}


def code(text, tag=None):
    metadata = {"tags": [tag]} if tag else {}
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

Created by **Mohsen Tahmasebi Nasab, PhD**<br>
[hydromohsen.com](https://hydromohsen.com)

Copyright and license holder: Mohsen Tahmasebi Nasab. Notebook code is
licensed under the repository's MIT License. Rang palette data follows the
CC0 dedication described in the licensing guide. Source images keep their own
rights and reuse terms.

</div>
""")


def common_inputs(example):
    slug = "kashan" if example else "your-palette"
    return [
        banner("YOUR INPUT", "Set the Git branch, choose whether to use Google Drive, and give the palette a short filename."),
        code(f'''
REPO_REF = "main" #@param {{type:"string"}}
USE_GOOGLE_DRIVE = True #@param {{type:"boolean"}}
PALETTE_SLUG = "{slug}" #@param {{type:"string"}}
''', "user-input"),
        markdown("""
Google Drive keeps the recipe available when you move to the next notebook.
For a local Jupyter session, working files are placed under
`cache/notebook_workflow/`. When testing a GitHub branch, replace `main` with
the branch name above.
"""),
        code('''
import shutil
import subprocess
import sys
from pathlib import Path

IN_COLAB = False
try:
    from google.colab import drive
    IN_COLAB = True
except ImportError:
    pass

if IN_COLAB:
    REPO_ROOT = Path("/content/Rang")
    if not (REPO_ROOT / "tools" / "notebook_workflow.py").exists():
        subprocess.run([
            "git", "clone", "--depth", "1", "--branch", REPO_REF,
            "https://github.com/mohsennasab/Rang.git", str(REPO_ROOT)
        ], check=True)
else:
    probe = Path.cwd().resolve()
    REPO_ROOT = next(
        candidate for candidate in (probe, *probe.parents)
        if (candidate / "tools" / "notebook_workflow.py").exists()
    )

try:
    import matplotlib
    import numpy
    import PIL
    import sklearn
except ImportError:
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-q", "-r",
        str(REPO_ROOT / "tools" / "requirements.txt")
    ], check=True)

sys.path.insert(0, str(REPO_ROOT / "tools"))

from notebook_workflow import *

if IN_COLAB and USE_GOOGLE_DRIVE:
    drive.mount("/content/drive")
    WORK_DIR = Path("/content/drive/MyDrive/Rang") / PALETTE_SLUG
else:
    WORK_DIR = REPO_ROOT / "cache" / "notebook_workflow" / PALETTE_SLUG

WORK_DIR.mkdir(parents=True, exist_ok=True)
RECIPE_PATH = WORK_DIR / f"{PALETTE_SLUG}-recipe.json"
use_arial()
print("Repository:", REPO_ROOT)
print("Working folder:", WORK_DIR)
print("Recipe:", RECIPE_PATH)
''')
    ]


def require_recipe():
    return code('''
if not RECIPE_PATH.exists():
    raise FileNotFoundError(
        f"Recipe not found at {RECIPE_PATH}. Run notebook 01 first and use "
        "the same Google Drive and palette slug settings."
    )
recipe = read_json(RECIPE_PATH)
print(f'Loaded {recipe["palette"]} with {len(recipe["regions"])} regions')
''')


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
        source = "https://images.metmuseum.org/CRDImages/is/original/DT5450.jpg"
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
        source = "PASTE AN HTTPS IMAGE URL HERE"
        regions = '''[
    {"id": "main-detail", "label": "Main detail", "box": [100, 100, 600, 600], "k": 8,
     "note": "Say why this part of the artwork matters"},
]'''
    cells = [title(path, "01", "Define regions",
                   "Load the artwork, read its pixel coordinates, and save the regions that matter to you.")]
    cells += common_inputs(example)
    cells += [
        banner("YOUR INPUT", "Enter the palette name and source image. Use an HTTPS image or a local path when working outside Colab."),
        code(f'''
PALETTE_NAME = "{palette_name}" #@param {{type:"string"}}
SOURCE_IMAGE = "{source}" #@param {{type:"string"}}
''', "user-input"),
        code('''
if SOURCE_IMAGE.startswith("PASTE "):
    raise ValueError("Replace SOURCE_IMAGE in the yellow input cell")
source_path = obtain_source(SOURCE_IMAGE, WORK_DIR)
source_image = open_rgb(source_path)
print("Image size:", source_image.size)
show_source(source_path, PALETTE_NAME)
'''),
        markdown("""
Read x from the horizontal axis and y from the vertical axis. A box is written
as `[left, top, right, bottom]`. Start with distinct visual parts, such as a
border, medallion, garment, flower, tile panel, or area of reflected light.
"""),
        banner("YOUR DECISION", "Edit the region list. Give each region a unique ID, a readable label, a pixel box, a value of k, and a short note."),
        code(f"REGIONS = {regions}", "user-decision"),
        code('''
recipe = create_recipe(
    PALETTE_NAME, SOURCE_IMAGE, source_path, REGIONS, RECIPE_PATH
)
overlay_path = WORK_DIR / "regions.png"
region_overlay(RECIPE_PATH, WORK_DIR, overlay_path)
print("Saved recipe:", RECIPE_PATH)
print("Saved region overlay:", overlay_path)
'''),
        markdown("""
Look at the overlay before moving on. If a box includes a frame, caption,
glare, or large neutral background that you do not want, change the box and
run the last two cells again.
"""),
    ]
    notebook(path, cells)


def step_02(path, example):
    cells = [title(path, "02", "Extract colors with k-means",
                   "Run k-means separately in every saved region and review the candidate sheet.")]
    cells += common_inputs(example)
    cells += [
        require_recipe(),
        region_overlay_code(),
        markdown("""
Each region is clustered in CIELAB. The candidate sheet orders clusters by
their share within that region. A large region does not get more authority
than a small region. The rows are evidence for your decision, not a finished
palette.
"""),
        banner("YOUR DECISION", "Choose whether this extraction run should become the accepted candidate snapshot in the recipe."),
        code('''
ACCEPT_THIS_RUN = True #@param {type:"boolean"}
''', "user-decision"),
        code('''
candidates = save_candidates(
    RECIPE_PATH, WORK_DIR, accept=ACCEPT_THIS_RUN
)
print(f"Extracted {len(candidates)} candidates")
for candidate in candidates:
    print(candidate["id"], candidate["hex"],
          f'{candidate["share"]:.1f}%')
print("Candidate sheet:", WORK_DIR / "candidates.png")
'''),
    ]
    notebook(path, cells)


def region_overlay_code():
    return code('''
region_overlay(RECIPE_PATH, WORK_DIR, WORK_DIR / "regions.png")
''')


def step_03(path, example):
    if example:
        selections = '''[
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
        selections = '''[
    {"candidate": "main-detail:c01", "note": "where this color appears"},
    {"candidate": "main-detail:c02", "note": "where this color appears"},
    {"candidate": "main-detail:c03", "note": "where this color appears"},
    {"candidate": "main-detail:c04", "note": "where this color appears"},
    {"candidate": "main-detail:c05", "note": "where this color appears"},
]'''
    cells = [title(path, "03", "Curate the palette",
                   "Choose five to twelve candidates and arrange them in a useful visual order.")]
    cells += common_inputs(example)
    cells += [
        require_recipe(),
        code('''
candidates = recipe.get("accepted_candidates", [])
if not candidates:
    raise ValueError("Run notebook 02 and accept the extraction first")
candidate_sheet(candidates, WORK_DIR / "candidates.png")
'''),
        markdown("""
Choose colors that carry the character of the artwork and can do useful work
in a figure. A frequent color does not have to be selected. A small detail can
be central to the palette. The order below becomes the continuous ramp order.
"""),
        banner("YOUR DECISION", "List the candidate IDs in your chosen ramp order. Write one note per color saying where it comes from."),
        code(f"SELECTIONS = {selections}", "user-decision"),
        code('''
recipe = save_curation(RECIPE_PATH, SELECTIONS)
colors = recipe["expected"]["colors"]
before_after_sheet(colors, colors)
for item in recipe["curation"]["colors"]:
    print(item["id"], item["from"], item["current"], item["note"])
print("Saved choices in:", RECIPE_PATH)
'''),
    ]
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
                   "Make careful LCh changes and save a readable record of every accepted adjustment.")]
    cells += common_inputs(example)
    cells += [
        require_recipe(),
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
print("Saved adjustment record:", RECIPE_PATH)
'''),
    ]
    notebook(path, cells)


def step_05(path, example):
    cells = [title(path, "05", "Check the palette",
                   "Review source distance, color separation, and the suggested categorical pick order.")]
    cells += common_inputs(example)
    cells += [
        require_recipe(),
        code('''
report = check_recipe(
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
    print(color, f'nearest={values["nearest"]:.1f}', marker)
print("Saved report:", WORK_DIR / "check-report.json")
'''),
        banner("YOUR DECISION", "Read the report and look at real sample plots. Keep meaningful colors when they serve the artwork, and explain any large source distance in the pull request."),
        markdown("""
A number can point to a problem, but it cannot decide whether a palette feels
right. Return to notebooks 03 and 04 when two colors collapse together, a
color drifts too far from the source, or the ramp loses the mood of the work.
"""),
    ]
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
        run_build = "True"
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
        run_build = "False"
    cells = [title(path, "06", "Build the palette",
                   "Write the palette JSON, run the repository build, and inspect the generated page.")]
    cells += common_inputs(example)
    cells += [
        require_recipe(),
        banner("YOUR INPUT", "Enter the artwork metadata exactly as the museum or source page gives it. Set the rights fields carefully."),
        code(f"PALETTE_METADATA = {metadata}", "user-input"),
        banner("YOUR DECISION", "Build inside the Colab clone after the draft is written. Leave this off until the metadata and rights are ready."),
        code(f'''
RUN_BUILD = {run_build} #@param {{type:"boolean"}}
''', "user-decision"),
        code('''
draft_path = WORK_DIR / f"{PALETTE_SLUG}-palette.json"
draft = palette_draft(RECIPE_PATH, PALETTE_METADATA, draft_path)
print("Palette draft:", draft_path)
print("Final colors:", *draft["colors"])

if RUN_BUILD:
    repository_palette = REPO_ROOT / "palettes" / f"{PALETTE_SLUG}.json"
    shutil.copyfile(draft_path, repository_palette)
    subprocess.run([
        sys.executable, str(REPO_ROOT / "tools" / "build.py"), PALETTE_SLUG
    ], cwd=REPO_ROOT, check=True)
    print("Generated page:", REPO_ROOT / "docs" / PALETTE_SLUG / "README.md")
'''),
        markdown("""
The build inside Colab is a validation copy. Download the recipe and palette
draft, then add them to your own Git branch with the generated repository
files. Check the artwork preview and every sample plot before opening a pull
request.
"""),
    ]
    notebook(path, cells)


def step_07(path, example):
    cells = [title(path, "07", "Replay and verify",
                   "Rerun the accepted extraction and adjustment history without making new decisions.")]
    cells += common_inputs(example)
    cells += [
        require_recipe(),
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
