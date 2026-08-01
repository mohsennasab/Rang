# Contributing a palette

Thanks for wanting to add to Rang. This guide takes you from a museum photo to
a merged pull request. The tooling does the packaging for you, your judgment
goes into picking the artwork and curating the colors.

## Contents

- [What makes a good source](#what-makes-a-good-source)
- [Setup](#setup)
- [Step 1, extract candidate colors](#step-1-extract-candidate-colors)
- [Step 2, curate the ramp](#step-2-curate-the-ramp)
- [Step 3, check the palette](#step-3-check-the-palette)
- [Step 4, adjust colors that miss](#step-4-adjust-colors-that-miss)
- [Step 5, write the palette file](#step-5-write-the-palette-file)
- [Step 6, build](#step-6-build)
- [Step 7, open the pull request](#step-7-open-the-pull-request)
- [Palette file reference](#palette-file-reference)

## What makes a good source

- Persian art in a broad sense. Carpets, miniatures, tilework, manuscripts,
  ceramics, metalwork, architecture. Works from the wider Persianate world
  fit when the visual tradition is Persian.
- A museum object with an open access, public domain photograph. The Met,
  the Cleveland Museum of Art, the Smithsonian and the David Collection all
  release suitable images. Keep the object page URL and the direct image URL,
  both go in the palette file.
- Strong, varied color. A good source usually offers a warm side and a cool
  side so the ramp can carry both discrete classes and continuous data.

Name the palette after the place, the art form or the work itself. One word,
capitalized, no spaces. Kashan, Isfahan, Tabriz, Shiraz, Mina, Zarrin.

## Setup

```
git clone https://github.com/mohsennasab/Rang.git
cd Rang
pip install -r tools/requirements.txt
```

## Step 1, extract candidate colors

Run k-means over the photo in CIELAB. Cluster region by region, not the whole
image at once. Large fields dominate a whole-image run and the centers drift
toward muddy averages. Read pixel coordinates for regions off any image viewer
that shows cursor position.

```
python tools/extract_colors.py --image <photo url> -k 8 ^
    --region 900,1400,1700,2200,medallion ^
    --region 700,700,1900,1300,field ^
    --swatches cache/clusters.png
```

You get a table of hex codes with CIELAB values and pixel share per region,
and an optional swatch sheet to look at.

## Step 2, curate the ramp

Pick five to twelve colors and arrange them as a ramp, dark to light to dark,
warm to cool, whatever walk through the artwork reads smoothly when
interpolated. Look at the artwork while you do this. The clusters are
candidates, the palette is a judgment call about what the work actually looks
like.

## Step 3, check the palette

```
python tools/check_palette.py --colors "#7f3020,#ab4a47,#c07049,#1a3b45" ^
    --image <photo url>
```

The report covers three things:

- Separation under normal vision and simulated protanopia, deuteranopia and
  tritanopia, as pairwise CIEDE2000. The collection marks a palette
  colorblind friendly when the worst case stays at or above 8.
- A suggested pick order, the order in which colors enter the discrete
  palette. Keep it unless you have a reason not to.
- Distance from each color to the nearest pixel of the photo. Aim for 3 or
  less. If a color sits farther out, either pull it back toward the artwork
  or say in the pull request why it needs to drift, for example lifting a
  color slightly so neighbors stay separable.

## Step 4, adjust colors that miss

When a color is close but not right, nudge it in lightness, chroma or hue
instead of hand editing hex codes:

```
python tools/adjust_colors.py --colors "#8a9463,#345f72" ^
    --edit "1:L+4,C-2" --png cache/before_after.png
```

Rerun the check after adjusting. The two scripts are meant to be cycled until
the numbers and your eyes agree.

## Step 5, write the palette file

Create `palettes/<name>.json`, all lowercase filename. Copy
`palettes/kashan.json` as a template. Fill in every source field, including
accession number and both URLs. Write one short note per color saying where in
the artwork it comes from. Leave out `order` and `colorblind` if you want the
build to compute them.

## Step 6, build

```
python tools/build.py <name>
```

This regenerates the Python, R and ArcGIS files for the whole collection,
renders your swatch, preview and sample plots, writes `docs/<name>/README.md`
and adds your palette to the gallery in the main README. Look at the sample
page it produced. If a plot reads badly, go back to step 4.

The elevation panel uses the CONUS grid in `data/`. Pass your own raster with
`python tools/make_samples.py <name> --dem your_dem.tif` if you want to see
the palette on different terrain.

## Step 7, open the pull request

Include in the description:

- the object page link and one sentence on why this work
- anything the check flagged, such as a color beyond distance 3 and why
- the sample page image

A maintainer will look at the source, the numbers and the samples. Expect
small requests about ramp order or a color that reads poorly in a plot.

## Palette file reference

| key | required | meaning |
|---|---|---|
| `name` | yes | one word, capitalized, matches the filename |
| `colors` | yes | 5 to 12 hex codes in ramp order |
| `notes` | yes | one short phrase per color, where in the artwork it lives |
| `order` | no | pick order for discrete use, computed by the build if absent |
| `colorblind` | no | set by the build from the worst case separation if absent |
| `source.title` | yes | object title as the museum gives it |
| `source.artist` | no | empty string when unknown |
| `source.date` | yes | as the museum gives it |
| `source.geography` | yes | for example "Iran, probably Kashan" |
| `source.medium` | yes | as the museum gives it |
| `source.museum` | yes | full museum name |
| `source.department` | no | museum department |
| `source.accession` | yes | accession number |
| `source.credit` | no | museum credit line |
| `source.url` | yes | object page |
| `source.image` | yes | direct link to the open access photo |
| `source.public_domain` | yes | must be true to be accepted |
