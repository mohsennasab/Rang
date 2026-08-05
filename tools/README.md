# Palette-making tools

The numbered notebooks take a contributor from an artwork photo to a checked,
reproducible palette. They run in Google Colab or a local Jupyter session.
Nothing is chosen automatically. The notebooks handle the repeated color math
and record keeping, while the contributor decides what belongs in the palette.

Created by **Mohsen Tahmasebi Nasab, PhD**. Visit
[hydromohsen.com](https://hydromohsen.com).

Copyright and license holder: Mohsen Tahmasebi Nasab. The notebook code and
shared tool code are licensed under the repository's MIT License. Palette data
follows the CC0 dedication in the [licensing guide](../LICENSES/README.md).
Source images keep their own rights and reuse terms.

## Start here

The easiest way to learn the workflow is the completed Kashan example in
[`tools/examole`](examole/README.md).

[![Open Kashan step 01 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/examole/01_define_regions.ipynb)

Run the notebooks in order. Notebook 01 asks you to upload the artwork from
your computer. At the end of each step, download the workflow ZIP. Upload that
ZIP at the beginning of the next notebook. No repository checkout or cloud
storage connection is needed after the notebook opens.

Cells with a yellow **YOUR INPUT** box need factual information such as an
object page or museum record. Cells with a blue **YOUR DECISION** box ask for
artistic judgment.

## The seven notebooks

| step | notebook | what you do |
|---|---|---|
| 01 | [Define regions](notebooks/01_define_regions.ipynb) | upload the artwork, enter pixel boxes, choose k for each region, and inspect the overlay |
| 02 | [Extract colors](notebooks/02_extract_colors.ipynb) | run region-by-region k-means in CIELAB and accept a candidate snapshot |
| 03 | [Curate the palette](notebooks/03_curate_palette.ipynb) | select five to twelve candidates, write notes, and arrange the ramp |
| 04 | [Adjust colors](notebooks/04_adjust_colors.ipynb) | change lightness, chroma, or hue and record why |
| 05 | [Check the palette](notebooks/05_check_palette.ipynb) | review source distance, color separation, and the suggested pick order |
| 06 | [Prepare the palette files](notebooks/06_build_palette.ipynb) | enter source metadata and write the palette JSON for the repository |
| 07 | [Replay and verify](notebooks/07_replay_and_verify.ipynb) | reproduce the accepted candidates and final colors from the saved recipe |

Every notebook has an **Open in Colab** button at the top. The reusable set
contains blank or sample inputs. The Kashan set contains complete decisions so
you can see a real workflow before starting your own.

## How to choose regions

Notebook 01 displays the full-resolution source with pixel coordinates. A
region is written as `[left, top, right, bottom]`.

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

The region overlay stays in the workflow ZIP or the local `cache/` directory.
The recipe stores the source checksum, image dimensions, pixel boxes,
normalized boxes, labels, notes, and k values.

## What k-means does

Notebook 02 runs k-means inside each region in CIELAB. CIELAB makes the
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

Notebook 03 is the main artistic step. Choose five to twelve candidates and
arrange them into a ramp that feels connected to the artwork and works in a
figure. You may leave out a dominant color, keep a color from a tiny detail,
or choose two related colors when their relationship matters.

Notebook 04 lets you adjust a selected color in LCh:

- `L` changes lightness.
- `C` changes chroma, which is similar to colorfulness.
- `H` rotates hue in degrees.

Keep changes deliberate. Each accepted adjustment stores the color before the
change, the color after the change, the numeric change, and your reason. The
Kashan example shows how sampled clusters were brought back toward colors seen
in the carpet.

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

Temporary images and reports stay in the workflow ZIP. When contributing a
palette, copy the final recipe into `recipes/<palette>.json` and the palette
draft into `palettes/<palette>.json`. Then run the repository build locally.

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
| `generate_workflow_notebooks.py` | regenerates the reusable and Kashan notebook sets |
| `notebook_workflow.py` | shared recipe, extraction, curation, adjustment, and replay functions |

Install the command-line dependencies with:

```text
pip install -r tools/requirements.txt
```

## Files created while you work

The downloaded `<palette>-workflow.zip` carries these files between steps:

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

## Before opening a pull request

- Verify the source rights and credit against the object page.
- Check the region overlay and candidate sheet.
- Read every saved adjustment and reason.
- Run notebook 05 and inspect the complete report.
- Run notebook 06 and inspect the palette JSON it prepares.
- Copy the recipe and palette JSON into a local checkout and run
  `python tools/build.py <name>`.
- Open the generated palette page.
- Inspect the artwork preview and every sample plot.
- Run notebook 07 and confirm `verified: True`.
- Add the recipe, palette JSON, and all normal generated files to the branch.
