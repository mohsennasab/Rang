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
SUBMISSION_NOTEBOOK = pathlib.Path("tools/notebooks/rang_submission_builder.ipynb")


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


def title(path):
    url_path = path.as_posix()
    return markdown(f"""
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/{url_path})

<div style="font-family:Arial,sans-serif">

# Rang palette workflow, notebook 1

This notebook takes one artwork image through region drawing, color extraction,
curation, adjustment, checking, file preparation, and replay.

Upload the artwork once. All seven stages run in this notebook, and the final
workflow ZIP downloads after verification. Upload that ZIP to notebook 2 to
prepare a complete proposal package.

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


def submission_title(path):
    url_path = path.as_posix()
    return markdown(f"""
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/{url_path})

<div style="font-family:Arial,sans-serif">

# Rang submission builder

This is notebook 2. Upload the verified workflow ZIP from notebook 1. This
notebook checks the saved work, creates repository-ready files, prepares
palette-specific files for software testing, and downloads one submission ZIP.

Created by **Mohsen Tahmasebi Nasab, PhD**<br>
[hydromohsen.com](https://hydromohsen.com)

Copyright and license holder: Mohsen Tahmasebi Nasab. Notebook code is
licensed under the repository's MIT License. Rang palette data follows the
CC0 dedication described in the licensing guide. Source images keep their own
rights and reuse terms.

</div>
""")


def embedded_submission_runtime():
    module_names = (
        "colorlib",
        "adjust_colors",
        "notebook_workflow",
        "make_preview",
        "make_samples",
        "make_stylx",
        "make_hecras_ramp",
        "submission_workflow",
    )
    sources = {
        name: (ROOT / "tools" / f"{name}.py").read_text(encoding="utf-8")
        for name in module_names
    }
    encoded = json.dumps(sources, ensure_ascii=False).encode("utf-8")
    packed = base64.b85encode(zlib.compress(encoded, level=9)).decode("ascii")
    names = json.dumps(module_names)
    return code(f'''#@title Set up this notebook
import base64
import json
import shutil
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
for module_name in {names}:
    module = types.ModuleType(module_name)
    module.__file__ = f"{{module_name}}.py"
    sys.modules[module_name] = module
    exec(compile(MODULE_SOURCES[module_name], module.__file__, "exec"),
         module.__dict__)

from notebook_workflow import read_json, use_arial
from submission_workflow import *

if IN_COLAB:
    SUBMISSION_BASE = Path("/content/rang-submission")
else:
    SUBMISSION_BASE = Path.cwd() / "cache" / "submission-notebook"
SUBMISSION_BASE.mkdir(parents=True, exist_ok=True)
use_arial()

def receive_workflow_zip(local_path):
    input_dir = SUBMISSION_BASE / "upload"
    input_dir.mkdir(parents=True, exist_ok=True)
    if IN_COLAB:
        print("Choose the final workflow ZIP downloaded from notebook 1")
        uploaded = files.upload()
        if len(uploaded) != 1:
            raise ValueError("Upload exactly one workflow ZIP")
        filename, data = next(iter(uploaded.items()))
        if Path(filename).suffix.lower() != ".zip":
            raise ValueError("The uploaded file must end in .zip")
        output = input_dir / Path(filename).name
        output.write_bytes(data)
        return output
    if not local_path:
        raise ValueError("Enter the local path to the workflow ZIP")
    path = Path(local_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".zip":
        raise ValueError("The workflow file must end in .zip")
    output = input_dir / path.name
    if path != output.resolve():
        shutil.copy2(path, output)
    return output

def offer_submission_download(path):
    print("Saved:", path)
    if IN_COLAB:
        files.download(str(path))

print("Submission folder:", SUBMISSION_BASE)
''', tag="setup", hidden=True)


def submission_notebook(path):
    cells = [
        submission_title(path),
        markdown("""
### Contents

01. Upload the verified workflow ZIP
02. Complete and validate the metadata
03. Describe the proposal and confirm the source rights
04. Build the submission package
05. Review the generated files and images
06. Download the submission ZIP
"""),
        embedded_submission_runtime(),
        section("01", "Upload the verified workflow ZIP",
                "Use the single ZIP downloaded at the end of notebook 1."),
        markdown("""
The ZIP must contain one recipe, one palette draft, the uploaded artwork,
`check-report.json`, and the saved workflow figures. Do not rename files inside
the ZIP. Renaming the ZIP itself is fine.
"""),
        banner("YOUR INPUT", "Upload the completed workflow ZIP from notebook 1."),
        code('''LOCAL_WORKFLOW_ZIP = "" #@param {type:"string"}

workflow_archive = receive_workflow_zip(LOCAL_WORKFLOW_ZIP)
bundle = load_workflow_archive(
    workflow_archive, SUBMISSION_BASE / "verified-workflow"
)
print("Palette name in recipe:", bundle["recipe"].get("palette", "missing"))
print("Palette name in draft:", bundle["palette"].get("name", "missing"))
print("Recipe:", bundle["recipe_path"].name)
print("Palette draft:", bundle["palette_path"].name)
print("Source image:", bundle["source_path"].name)''', "user-input"),
        section("02", "Complete and validate the metadata",
                "Review what was saved and fill any gaps before building the proposal."),
        markdown("""
Notebook 2 recovers the palette name and object-page link from the recipe when
it can. It also prepares a repository path for the uploaded source image.

The report below separates two kinds of messages. A **STOP** message means the
saved color workflow cannot be built. A **WARNING** identifies incomplete
descriptive metadata. Warnings do not stop you from creating the proposal ZIP.
You can finish those fields now or leave them for later review.
"""),
        code('''bundle = apply_metadata_updates(bundle, {})
palette = bundle["palette"]
source = palette.get("source", {})

print("Saved palette metadata")
for field in ("name", "persian", "pronunciation", "about"):
    print(f"{field}: {palette.get(field, 'missing')}")
print()
print("Saved source metadata")
for field in (
    "title", "artist", "date", "geography", "medium", "museum",
    "accession", "credit", "url", "image", "rights", "public_domain",
):
    print(f"{field}: {source.get(field, 'missing')}")

blocking_problems = validate_submission_input(bundle)
metadata_warnings = submission_metadata_warnings(bundle)
if blocking_problems:
    print("\\nSTOP")
    for problem in blocking_problems:
        print("-", problem)
else:
    print("\\nThe saved color workflow can be built")
if metadata_warnings:
    print("\\nWARNINGS")
    for warning in metadata_warnings:
        print("-", warning)
    print("You may continue and complete these fields later")
else:
    print("\\nThe metadata has no warnings")'''),
        markdown("""
The next cell is optional. It starts as an empty dictionary, so running it as
shown keeps every recovered value and continues. Add only the fields you want
to enter or correct. Do not copy saved values into this cell.

For example, this changes three palette fields and two source fields:

```python
METADATA_UPDATES = {
    "persian": "گیلاس",
    "pronunciation": "gee-LAAS",
    "about": "A short description in your own words",
    "source": {
        "title": "The artwork title",
        "date": "The date shown by the source",
    },
}
```

Use exact wording from the artwork or collection page. Do not type filler such
as `f`, `test`, or `unknown` into a field. Leave the field out instead. Missing
metadata will be listed in the proposal for later review.

- `name` is one capitalized word, such as `Saffron`. It must match the
  name used in notebook 1. This is the only required metadata field, and the
  builder normally recovers it for you.
- `persian` is the Persian name. `pronunciation` explains how to say it in
  English. `about` is a short description in your own words.
- `title`, `date`, `geography`, and `medium` describe the artwork.
- `url` is the HTTPS page where a reviewer can confirm the artwork and rights.
- `image` is either a direct HTTPS image address or its future repository path.
  The builder normally proposes a path such as `sources/saffron/source.jpg`.
- Set `public_domain` to `True` only when the source page explicitly says the
  image is public domain or open access. A museum source should also include
  `museum` and `accession`.
- Set `public_domain` to `False` for your own photo or a licensed image. Then
  enter the exact `credit` and `rights` wording.
- Set `preserve_aspect` to `True` when the complete artwork should retain its
  original proportions. Leave it as `None` to keep the saved value.

If a recovered value is correct, do not mention it in `METADATA_UPDATES`.
"""),
        banner("OPTIONAL INPUT", "Leave this dictionary empty to keep the saved values, or add only the fields you want to change."),
        code('''METADATA_UPDATES = {
}''', "user-input"),
        code('''bundle = apply_metadata_updates(bundle, METADATA_UPDATES)
blocking_problems = validate_submission_input(bundle)
if blocking_problems:
    raise ValueError(
        "The saved color workflow cannot be built:\\n- "
        + "\\n- ".join(blocking_problems)
    )

metadata_warnings = submission_metadata_warnings(bundle)
if metadata_warnings:
    print("Metadata warnings")
    for warning in metadata_warnings:
        print("-", warning)
    print("These warnings will be included in the proposal for later review")

verification = verify_recipe(bundle["recipe_path"], bundle["work_dir"])
for key, value in verification.items():
    print(f"{key}: {value}")
if not verification["verified"]:
    raise ValueError("The saved recipe did not reproduce. Return to notebook 1")

palette = bundle["palette"]
source = palette["source"]
print()
print("Name:", palette["name"])
print("Persian:", palette.get("persian", "not provided"))
print("Pronunciation:", palette.get("pronunciation", "not provided"))
print("Colors:", *palette["colors"])
print("Artwork:", source.get("title", "not provided"))
print("Object page:", source.get("url", "not provided"))
print("Public domain:", source.get("public_domain", "not confirmed"))
if source.get("public_domain") is False:
    print("Rights:", source.get("rights", "not provided"))'''),
        markdown("""
The three saved figures below show the regions, k-means candidates, and color
adjustments. A missing adjustment image is normal when no colors were changed.
"""),
        code('''review_paths = [
    bundle["work_dir"] / name
    for name in ("regions.png", "candidates.png", "adjustments.png")
    if (bundle["work_dir"] / name).is_file()
]
figure, axes = plt.subplots(
    1, len(review_paths), figsize=(7 * len(review_paths), 7), squeeze=False
)
for axis, image_path in zip(axes[0], review_paths):
    axis.imshow(Image.open(image_path))
    axis.set_title(image_path.stem.replace("-", " ").title())
    axis.axis("off")
figure.tight_layout()'''),
        section("03", "Describe and confirm the proposal",
                "Write the short context a maintainer needs before reviewing it."),
        markdown("""
`WHY_THIS_WORK` should explain why the artwork and its colors belong in Rang.
Keep it to one or two direct sentences. Use `MAINTAINER_NOTES` for an unusual
color adjustment, source limitation, or anything else that deserves attention.
It can stay empty when there is nothing additional to explain.

Open the object page again before checking the rights box. Confirm the creator,
credit, reuse status, and exact license against the source record. Also inspect
the four viewing rows and source distances from notebook 1. The checks support
your judgment, but the palette should still feel true to the artwork and work
well as a visualization.

If metadata warnings remain, checking the source box means you reviewed the
object page and understand that those warnings must be resolved before the
palette is merged. The warnings do not prevent you from building the proposal.
"""),
        banner("YOUR INPUT", "Describe why the work belongs in Rang and add any review notes."),
        code('''WHY_THIS_WORK = "" #@param {type:"string"}
MAINTAINER_NOTES = "" #@param {type:"string"}

validate_proposal_details(WHY_THIS_WORK, MAINTAINER_NOTES)''', "user-input"),
        banner("YOUR DECISION", "Confirm the source record and the visual review after checking them yourself."),
        code('''CONFIRM_SOURCE_RIGHTS = False #@param {type:"boolean"}
CONFIRM_VISUAL_REVIEW = False #@param {type:"boolean"}

if not CONFIRM_SOURCE_RIGHTS:
    raise ValueError(
        "Open the object page, verify the credit and reuse terms, then check CONFIRM_SOURCE_RIGHTS"
    )
if not CONFIRM_VISUAL_REVIEW:
    raise ValueError(
        "Review the artwork, palette, and four viewing rows, then check CONFIRM_VISUAL_REVIEW"
    )''', "user-decision"),
        section("04", "Build the submission package",
                "Create repository files, test files, documentation, and review material."),
        markdown("""
The `repository` folder contains the palette, recipe, source card, documentation
page, and images in their expected Rang paths. The `software` folder contains
one-palette files for testing in ArcGIS Pro, QGIS, HEC-RAS, and GeoLibre, plus
Python and R examples. The `review` folder keeps the extraction evidence.

The software files are deliberately palette-specific. They must not replace
Rang's combined collection files. After copying the repository-ready files, a
maintainer runs `python tools/build.py <name>` to rebuild the shared outputs.
"""),
        code('''proposal = build_submission(
    bundle,
    SUBMISSION_BASE,
    WHY_THIS_WORK,
    MAINTAINER_NOTES,
)
print("Submission folder:", proposal["root"])
print("Submission ZIP:", proposal["archive"])
print("ArcGIS, QGIS, HEC-RAS, and GeoLibre test files are ready")'''),
        section("05", "Review the generated files and images",
                "Inspect the proposal before downloading it."),
        markdown("""
`README.md` explains where each file belongs. `PULL_REQUEST.md` is a prepared
pull request description with the workflow results. Its remaining unchecked
items are repository commands that must run after the proposal files are copied
into a branch.

The gallery card and sample plots appear below. Check that the artwork is not
distorted, the palette order reads well, labels fit, and all panels are clear.
"""),
        code('''for path in sorted(proposal["root"].rglob("*")):
    if path.is_file():
        print(path.relative_to(proposal["root"]))

slug = palette_slug(proposal["palette"]["name"])
docs_dir = proposal["root"] / "repository" / "docs" / slug
figure, axes = plt.subplots(2, 1, figsize=(14, 12))
for axis, filename in zip(axes, ("card.png", "samples.png")):
    axis.imshow(Image.open(docs_dir / filename))
    axis.set_title(filename.replace(".png", "").title())
    axis.axis("off")
figure.tight_layout()'''),
        banner("SAVE YOUR WORK", "Download the submission ZIP after the files and images look right."),
        section("06", "Download the submission ZIP",
                "Save the complete proposal package to your computer."),
        code('''CONFIRM_PROPOSAL_REVIEW = False #@param {type:"boolean"}
DOWNLOAD_SUBMISSION_ZIP = True #@param {type:"boolean"}

if not CONFIRM_PROPOSAL_REVIEW:
    raise ValueError(
        "Inspect the generated file list, gallery card, and samples, then check CONFIRM_PROPOSAL_REVIEW"
    )
if DOWNLOAD_SUBMISSION_ZIP:
    offer_submission_download(proposal["archive"])
else:
    print("Submission ZIP:", proposal["archive"])''', "user-decision"),
    ]
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


def setup_cells(path):
    return [
        title(path),
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
        code('''PALETTE_SLUG = "your-palette" #@param {type:"string"}
DOWNLOAD_FINAL_ZIP = True #@param {type:"boolean"}''', "user-input"),
        embedded_runtime(),
    ]


def step_01_cells():
    regions = '''[
    {"id": "main-detail", "label": "Main detail", "box": [100, 100, 600, 600], "k": 8,
     "note": "Say why this part of the artwork matters"},
]'''
    return [
        section("01", "Upload the image and define regions",
                "Upload one artwork image and draw the regions that matter to you."),
        banner("YOUR INPUT", "Upload the artwork. Also enter its name and object page."),
        code('''PALETTE_NAME = "Your palette name" #@param {type:"string"}
LOCAL_IMAGE_PATH = "" #@param {type:"string"}
SOURCE_REFERENCE = "PASTE THE OBJECT PAGE URL HERE" #@param {type:"string"}

source_path, original_filename = receive_source(LOCAL_IMAGE_PATH)
source_image = open_rgb(source_path)
print("Image size:", source_image.size)''', "user-input"),
        markdown("""
Drag boxes directly over the image in Colab. Each box gets an ID, name, k
value, and note. Use Undo or Delete when a box does not feel right, then click
**Use these regions**. The drawer converts each box to original image pixels.
"""),
        banner("YOUR DECISION", "Draw the sampling regions, then check that each box covers the part of the artwork you meant to sample."),
        code(f'''DRAW_REGIONS_INTERACTIVELY = True #@param {{type:"boolean"}}
START_WITH_TEMPLATE_BOXES = False #@param {{type:"boolean"}}

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


def step_03_cells():
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


def step_04_cells():
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


def step_06_cells():
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
        "public_domain": None
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
palette JSON. Notebook 2 reads this ZIP, reports incomplete source fields as
warnings, and places the accepted files in their expected repository paths.
It also creates documentation images and palette-specific software files for
review.
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
        markdown("""
Continue with [notebook 2, the Rang submission builder](https://github.com/mohsennasab/Rang/blob/main/tools/notebooks/rang_submission_builder.ipynb).
Upload the workflow ZIP there without changing any files inside it.
"""),
    ]


def notebook(path):
    cells = setup_cells(path)
    cells += step_01_cells()
    cells += step_02_cells()
    cells += step_03_cells()
    cells += step_04_cells()
    cells += step_05_cells()
    cells += step_06_cells()
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
    notebook(MAIN_NOTEBOOK)
    submission_notebook(SUBMISSION_NOTEBOOK)


if __name__ == "__main__":
    main()
