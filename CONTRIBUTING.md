# Contributing a palette

Thanks for wanting to add to Rang. This guide takes you from a museum photo to
a merged pull request. The tooling does the packaging for you, your judgment
goes into picking the artwork and curating the colors.

The recommended path uses two Jupyter notebooks in Google Colab. Notebook 1
carries one recipe from regions to a finished palette. Notebook 2 validates
that work and prepares a complete proposal package. The command-line scripts
remain available for contributors who prefer a terminal.

## Contents

- [What makes a good source](#what-makes-a-good-source)
- [Setup](#setup)
- [Step 1, extract candidate colors](#step-1-extract-candidate-colors)
- [Step 2, curate the ramp](#step-2-curate-the-ramp)
- [Step 3, adjust colors that miss](#step-3-adjust-colors-that-miss)
- [Step 4, check the palette](#step-4-check-the-palette)
- [Step 5, write the palette file](#step-5-write-the-palette-file)
- [Step 6, build](#step-6-build)
- [Step 7, open the pull request](#step-7-open-the-pull-request)
- [Palette file reference](#palette-file-reference)

## What makes a good source

- Persian art in a broad sense. Carpets, miniatures, tilework, manuscripts,
  ceramics, metalwork, architecture. Works from the wider Persianate world
  fit when the visual tradition is Persian.
- A photograph you have the rights to share. Two paths work. Use a museum
  image whose object page states a suitable reuse license, or your own photo of
  tilework, a building or an object. New contributed photographs must use CC
  BY 4.0 or CC0, with the exact license and credit line recorded in the palette
  file. Either way keep a reference URL, an object page or something like the
  UNESCO listing for a site.
- Strong, varied color. A good source usually offers a warm side and a cool
  side so the ramp can carry both discrete classes and continuous data.

Name the palette after the place, the art form or the work itself. One word,
capitalized, no spaces. Kashan, Isfahan, Tabriz, Shiraz, Mina, Zarrin. Add a
pronunciation so readers can say it, stress goes on the last syllable in
Persian.

## Setup

### Google Colab

Start with notebook 1:

[![Open the Rang workflow in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/notebooks/rang_palette_workflow.ipynb)

Upload the artwork once and work through the seven stages from top to bottom.
After the replay check succeeds, the notebook downloads one workflow ZIP. It
contains the source copy, region overlay, candidate sheet, adjustment preview,
report, recipe, and palette draft.

Then open notebook 2 and upload the workflow ZIP:

[![Open the Rang submission builder in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/notebooks/rang_submission_builder.ipynb)

Notebook 2 recovers known values from the recipe and shows any missing source
metadata as warnings. Its update dictionary is optional and starts empty, so
running it unchanged keeps every recovered value. Missing descriptive metadata
does not stop the proposal package. The notebook then checks the saved recipe,
asks you to review the source rights and visuals, and downloads one submission
ZIP. That package contains
repository-ready files, documentation images, palette-specific software test
files, review evidence, and a pull request draft.

Yellow **YOUR INPUT** cells need factual information such as an object page.
Blue **YOUR DECISION** cells are where you choose regions, colors, and
adjustments. No cloud storage connection or repository checkout is needed
inside Colab.

The [Kashan example](tools/example/README.md) contains a complete set of
decisions and is the best place to learn the workflow.

### Local setup

```
git clone https://github.com/mohsennasab/Rang.git
cd Rang
pip install -r tools/requirements.txt
```

## Step 1, extract candidate colors

Open [the workflow notebook](tools/notebooks/rang_palette_workflow.ipynb) and
go to step 01. It displays the source you upload in an interactive drawer.
Drag three to seven boxes over
regions with a clear visual purpose, such as a border, medallion, field,
garment, flower, tile panel, or area of reflected light. Name each region,
choose k, and add a short note below the image. You can undo the last box,
delete one region, or clear the drawing and begin again. Inspect the saved
overlay before moving to step 02.

Step 02 runs k-means over each region in CIELAB. Large fields can
dominate a whole-image run and pull cluster centers toward muddy averages.
Separate regions help small details keep their voice.

The notebook saves the regions, source checksum, k values, extraction
settings, and accepted candidates in the recipe. The command-line equivalent
is:

```
python tools/extract_colors.py --image "PHOTO_URL" -k 8 --region 900,1400,1700,2200,medallion --region 700,700,1900,1300,field --swatches cache/clusters.png
```

You get a table of hex codes with CIELAB values and pixel share per region,
and an optional swatch sheet to look at.

This process is not meant to produce one inevitable answer. The regions you
notice, the details you care about and the colors that feel true to the work
will differ from one person to another. That is part of making the palette.
Treat the extracted clusters as a starting point, not a verdict.

## Step 2, curate the ramp

In step 03, run the short inventory cell to see each exact region ID and its
available candidate numbers. Fill the selection template in the next cell with
five to twelve complete candidate IDs. Write one source note for each color
and place the rows in the order you want for a continuous ramp.

Pick five to twelve colors and arrange them as a ramp, dark to light to dark,
warm to cool, whatever walk through the artwork reads smoothly when
interpolated. Look at the artwork while you do this. The clusters are
candidates, the palette is a judgment call about what the work actually looks
like.

Trust your eyes here. You are welcome to move away from an extracted center,
replace it with a color you find more beautiful or leave out a dominant color
that does not help the palette. What matters is that the finished colors still
belong to the artwork, feel good together and work clearly in real
visualizations. The checks in the next steps are guides for that judgment, not
a recipe that overrides it.

## Step 3, adjust colors that miss

Use step 04 when a selected cluster needs a careful change. L changes
lightness, C changes chroma, and H changes hue. Each accepted edit records its
before color, after color, numeric change, and your reason.

When a color is close but not right, nudge it in lightness, chroma or hue
instead of hand editing hex codes:

```
python tools/adjust_colors.py --colors "#8a9463,#345f72" --edit "1:L+4,C-2" --png cache/before_after.png
```

Rerun the check after adjusting. The two scripts are meant to be cycled until
the numbers and your eyes agree.

## Step 4, check the palette

Run step 05 to create the full report from the saved recipe. The command-line
equivalent is:

```
python tools/check_palette.py --colors "#7f3020,#ab4a47,#c07049,#1a3b45" --image "PHOTO_URL"
```

The report covers three things:

- Separation under normal vision and simulated protanopia, deuteranopia and
  tritanopia, as pairwise CIEDE2000. Rang uses 8 as its cutoff for the lowest
  pairwise score. Treat the number as one check, then look at the finished
  figure yourself.
- A suggested pick order, the order in which colors enter the discrete
  palette. Keep it unless you have a reason not to.
- Distance from each color to the nearest sampled point in a reduced copy of
  the photo. Aim for 3 or less. If a color sits farther out, pull it back
  or say in the pull request why it needs to drift, for example lifting a
  color slightly so neighbors stay separable.

## Step 5, write the palette file

In step 06, enter the artwork metadata exactly as the source record gives it.
Pay close attention to the reuse status, rights statement, credit, object page,
and source image URL. The notebook writes a palette draft from the final recipe
colors and notes.

Notebook 2 places the draft at `repository/palettes/<name>.json` inside the
submission ZIP. Fill in every source field in notebook 1 before creating that
package. Write one short note per color saying where in the artwork it comes
from, and add the pronunciation. A second photo showing the work in its setting
can later go in `source.context_image` with a caption, it appears on the palette
page. Leave out `position` if you want the repository build to assign it.

Notebook 2 places the final recipe at `repository/recipes/<name>.json`. It
records the source checksum, regions, k-means settings, accepted candidates,
selected candidate IDs, and the complete adjustment history. Working images
and reports stay under `review` in the submission package or in `cache/`.

## Step 6, build

Step 06 prepares the palette JSON after the metadata is complete. Step 07
replays the recipe and downloads the final workflow ZIP. Upload that ZIP to
notebook 2. Review the metadata and source rights, describe why the artwork and
palette belong in Rang, then build and inspect the proposal.

The `repository` folder in the submission ZIP follows the Rang directory
layout. Copy its contents into a local checkout and then run:

```
python tools/build.py <name>
```

This regenerates the Python, R, ArcGIS, QGIS, GeoLibre and HEC-RAS files for
the whole collection, including the combined HEC-RAS import. It also renders
your swatch, gallery card, preview and sample plots, writes
`docs/<name>/README.md` and adds your palette to the gallery in the main
README. Look at the sample page it produced. If a plot reads badly, go back
to step 4.

The rainfall and elevation panels use the real grids in `data/`, one day of
NOAA AORC precipitation and a CONUS DEM. Pass your own raster with
`python tools/make_samples.py <name> --dem your_dem.tif` if you want to see
the palette on different terrain.

Notebook 2 also creates one-palette ArcGIS Pro, QGIS, HEC-RAS, and GeoLibre
files under `software`. They let a reviewer try the proposal before merging.
Do not copy them over the combined Rang files. The command above recreates the
combined collection correctly.

## Step 7, open the pull request

Before opening the pull request, run step 07 in notebook 1. It reruns the saved
extraction and adjustment history without asking for a new artistic decision.
Download the workflow ZIP only after it reports `verified: True`. Run notebook
2 and inspect its file list, gallery card, and samples before downloading the
submission ZIP.

Notebook 2 writes `PULL_REQUEST.md` as a starting description. Check it against
the finished branch and include:

- the object page link and one sentence on why this work
- anything the check flagged, such as a color beyond distance 3 and why
- the sample page image
- confirmation that step 07 reproduced the accepted candidates and final
  colors

A maintainer will look at the source, the numbers and the samples. Expect
small requests about ramp order or a color that reads poorly in a plot.

## Palette file reference

| key | required | meaning |
|---|---|---|
| `name` | yes | one word, capitalized, matches the filename |
| `persian` | yes | the name in Persian script, like کاشان |
| `pronunciation` | yes | how to say it, like "kah-SHAHN", add the meaning if you like |
| `position` | no | gallery order, the build assigns the next slot when absent |
| `colors` | yes | 5 to 12 hex codes in ramp order |
| `notes` | yes | one short phrase per color, where in the artwork it lives |
| `order` | no | pick order for discrete use, computed by the build if absent |
| `colorblind` | no | project CVD separation flag, set by the build when absent |
| `about` | no | one short paragraph on what the palette was made for, shown in the gallery and on its page |
| `samples` | no | leave out for the standard six panels, or "water" for the water surface elevation and stream network page |
| `craft` | no | a paragraph or two on how the art form is made and its history, claims you can back up, shown on the palette page |
| `story` | no | a short account of the scene or source text, shown on the palette page |
| `source.title` | yes | object or work title |
| `source.note` | no | a brief clarification about the source record |
| `source.citation` | no | first source line on the palette page, used when the standard title, date and geography line does not fit |
| `source.artist` | no | empty string when unknown |
| `source.date` | yes | as the museum or reference gives it |
| `source.dimensions` | no | physical dimensions when they matter to the work |
| `source.geography` | yes | for example "Iran, probably Kashan" |
| `source.medium` | yes | for example "Glazed polychrome tilework" |
| `source.museum` | museum sources | full museum name |
| `source.site` | own photos | the place, for example "Golestan Palace, UNESCO World Heritage Site" |
| `source.department` | no | museum department |
| `source.accession` | museum sources | accession number |
| `source.credit` | own photos | your credit line, "Photo by Your Name, year" |
| `source.url` | yes | object page or reference page for the site |
| `source.reference_label` | no | link text for the reference on the palette page |
| `source.artist_url` | no | official biography or artist page |
| `source.image` | yes | image URL, or repo path under `sources/` for your own photo |
| `source.download_url` | no | full-resolution museum link when `source.image` is a local open-access copy |
| `source.card_image` | no | square crop used beside the palette in the gallery, falls back to `source.image` |
| `source.preserve_aspect` | no | true when the complete image must appear without cropping |
| `source.context_image` | no | second photo showing the work in its setting |
| `source.context_caption` | no | one line under the context photo |
| `source.context_url` | no | source page for the context photo |
| `source.context_credit` | no | photographer and date for the context photo |
| `source.context_rights` | no | license or rights statement for the context photo |
| `source.public_domain` | yes | true for open access images, false for your own photo |
| `source.rights` | own photos | exact license and credit, for example "CC BY 4.0, Photo by Your Name, year" |
