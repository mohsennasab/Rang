# Palette-making tools

Two notebooks take a contributor from an artwork photo to a checked,
reproducible palette proposal. They run in Google Colab or a local Jupyter
session. The notebooks handle color math and record keeping, while the
contributor decides what belongs in the palette. Notebook 2 packages the
verified work for review.

Created by **Mohsen Tahmasebi Nasab, PhD**. Visit
[hydromohsen.com](https://hydromohsen.com).

Copyright and license holder: Mohsen Tahmasebi Nasab. The notebook code and
shared tool code are licensed under the repository's MIT License. Palette data
follows the CC0 dedication in the [licensing guide](../LICENSES/README.md).
Source images keep their own rights and reuse terms.

## Start here

[![Open notebook 1 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/notebooks/rang_palette_workflow.ipynb)

[![Open notebook 2 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/notebooks/rang_submission_builder.ipynb)

Run the seven stages in notebook 1 from top to bottom. Upload the artwork once
and download the workflow ZIP after the final replay. Open notebook 2, upload
that ZIP, review any metadata warnings, and download the submission ZIP. Leave
the optional update dictionary empty when the recovered values are correct.
No repository checkout or cloud storage connection is needed.

Cells with a yellow **YOUR INPUT** box need factual information such as an
object page or museum record. Cells with a blue **YOUR DECISION** box ask for
artistic judgment.

## The two notebooks

| notebook | file | result |
|---|---|---|
| 1, make the palette | [`rang_palette_workflow.ipynb`](notebooks/rang_palette_workflow.ipynb) | a verified workflow ZIP with the source, recipe, decisions, report, and palette draft |
| 2, prepare the proposal | [`rang_submission_builder.ipynb`](notebooks/rang_submission_builder.ipynb) | a submission ZIP with repository files, images, software tests, review material, and a pull request draft |

Notebook 2 recovers values already known from the recipe, shows any missing
metadata as warnings, and gives you one optional input cell for additions or
corrections. Leave that dictionary empty to keep every recovered value. Missing
descriptive metadata does not stop the proposal from being built. It then
replays the recipe and asks for a short explanation of why the work belongs in
Rang. It also creates palette-specific ArcGIS Pro, QGIS, HEC-RAS, and GeoLibre
files for testing. These do not replace the combined collection files. The
maintainer rebuilds those after adding the proposed palette to a branch.

## The seven stages in notebook 1

| step | stage | what you do |
|---|---|---|
| 01 | Define regions | upload the artwork, draw boxes over it, choose k for each region, and inspect the overlay |
| 02 | Extract colors | run region-by-region k-means in CIELAB and accept a candidate snapshot |
| 03 | Curate the palette | read the available region and candidate IDs, select five to twelve candidates, write notes, and arrange the ramp |
| 04 | Adjust colors | change lightness, chroma, or hue and record why |
| 05 | Check the palette | review source distance, color separation, and the suggested pick order |
| 06 | Prepare the palette files | enter source metadata and write the palette JSON for the repository |
| 07 | Replay, verify, and download | reproduce the accepted colors and download the complete workflow ZIP |

The workflow notebook places a format example beside every input that needs
one. Start with your own artwork and make each decision while viewing the image.

## How to choose regions

Step 01 opens an interactive region drawer in Colab. Drag a box over each
part of the image you want to sample. Name the region, choose its k value, and
add a short note below the image. Undo removes the last box. Delete removes a
specific box. Clear all lets you start again.

When you click **Use these regions**, the drawer converts every box to exact
coordinates in the original image. The saved form is
`[left, top, right, bottom]`. Local Jupyter users can edit those coordinates
in `REGION_TEMPLATE` when the Colab drawer is not available.

Good regions have a visual purpose. A carpet might have separate regions for
the border, field, medallion, and guard bands. A miniature might use the sky,
architecture, clothing, landscape, and illuminated heading. A mosque interior
might separate stained glass, tilework, walls, and reflected light.

Keep these points in mind:

- Start with three to seven regions.
- Use a separate region for a small detail that carries an important color.
- Let regions overlap when two visual ideas share part of the artwork.
- Avoid frames, captions, glare, and museum backgrounds unless you want them
  in the palette.
- Do not use one full-image box unless the photograph is already tightly
  framed.
- Look at the saved overlay before moving on.

The region overlay is included in the final workflow ZIP. In local Jupyter it
also stays in the ignored `cache/` directory. The recipe stores the source
checksum, image dimensions, pixel boxes, normalized boxes, labels, notes, and
k values.

## What k-means does

Step 02 runs k-means inside each region in CIELAB. CIELAB makes the
distance calculation closer to how people notice color differences than a
simple RGB calculation.

The value of k is the number of clusters requested for one region. Eight is a
useful starting point for a detailed region. Try a smaller value for a simple
area and a larger value when several pigments or materials share the same
box. The accepted value is saved in the recipe.

Candidate rows are ordered by their pixel share inside each region. This is
not a ranking of artistic importance. A rare flower, line, or reflection can
matter more than a large background.

## Where your judgment belongs

Step 03 is the main artistic step. Choose five to twelve candidates and
arrange them into a ramp that feels connected to the artwork and works in a
figure. You may leave out a dominant color, keep a color from a tiny detail,
or choose two related colors when their relationship matters.

The first code cell in step 03 lists every region ID and its available
candidate numbers. Copy five to twelve complete candidate IDs into the empty
selection template in the next cell. The notebook does not choose them for
you.

Step 04 lets you adjust a selected color in LCh:

- `L` changes lightness.
- `C` changes chroma, which is similar to colorfulness.
- `H` rotates hue in degrees.

Keep changes deliberate. Each accepted adjustment stores the color before the
change, the color after the change, the numeric change, and your reason. The
saved before-and-after figure makes those choices easy to review later.

## What the recipe saves

The recipe is a small JSON file. It records:

- the creator and license holder
- the source reference, original filename, checksum, and oriented dimensions
- every region and k value
- deterministic k-means settings
- Python, NumPy, Pillow, and scikit-learn versions
- the accepted candidate colors and their CIELAB centers
- selected candidate IDs and notes
- ordered color adjustments with before and after values
- the final expected colors

Temporary images and reports stay in the working folder until step 07 creates
the workflow ZIP. Notebook 2 reads this ZIP and places the accepted recipe,
palette JSON, source card, page, and images into their expected repository
paths. It also prepares review copies for supported software.

## Command-line alternatives

The existing scripts remain useful for quick checks and maintenance.

| script | what it does |
|---|---|
| `extract_colors.py` | k-means clustering for a photo, either whole image or repeated rectangular regions |
| `adjust_colors.py` | LCh adjustment for a list of hex colors |
| `check_palette.py` | source distance, separation scores, and suggested pick order |
| `build.py` | all generated packages, integration files, images, and pages |
| `make_preview.py` | swatch, gallery card, and artwork preview |
| `make_samples.py` | standard visualization samples and the water-map layout |
| `make_hecras_ramp.py` | individual and combined HEC-RAS import files |
| `make_stylx.py` | ArcGIS Pro style file |
| `generate_workflow_notebooks.py` | regenerates the two reusable notebooks |
| `notebook_workflow.py` | shared recipe, extraction, curation, adjustment, and replay functions |
| `submission_workflow.py` | validation, proposal images, software test files, and submission packaging |

Install the command-line dependencies with:

```text
pip install -r tools/requirements.txt
```

## Files passed from notebook 1 to notebook 2

The downloaded `<palette>-workflow.zip` contains:

```text
<palette>-recipe.json
source.jpg
regions.png
candidates.json
candidates.png
adjustments.png
check-report.json
<palette>-palette.json
```

The source extension matches the uploaded file. In local Jupyter, the same
files go under `cache/notebook-upload/<palette>/`. The cache remains ignored
by Git.

## Files in the submission ZIP

Notebook 2 creates four clear areas:

```text
repository/     palette, recipe, source card, documentation page, and images
software/       palette-specific ArcGIS Pro, QGIS, HEC-RAS, and GeoLibre tests
review/         regions, candidates, adjustments, report, and source image
PULL_REQUEST.md prepared contribution description
```

The package README explains which files can be copied directly and which are
only for testing. The repository build remains the final source for all
collection-wide outputs.

## Before opening a pull request

- Verify the source rights and credit against the object page.
- Check the region overlay and candidate sheet.
- Read every saved adjustment and reason.
- Run step 05 and inspect the complete report.
- Run step 06 and inspect the palette JSON it prepares.
- Run step 07 and confirm `verified: True` before downloading.
- Upload the workflow ZIP to notebook 2.
- Verify the source rights against the object page again.
- Inspect the proposal gallery card and sample plots.
- Download the submission ZIP and read its `README.md`.
- Copy the `repository` files into a branch and run the commands given in the
  package README.
