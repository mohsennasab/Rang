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
- A photograph you have the rights to share. Two paths work. Museum open
  access images, The Met, the Cleveland Museum of Art, the Smithsonian and
  the David Collection all release suitable ones. Or your own photograph of
  tilework, a building or an object, committed under `sources/<name>/` with
  your credit line, the way the Golestan palette does it. Either way keep a
  reference URL, an object page or something like the UNESCO listing for a
  site.
- Strong, varied color. A good source usually offers a warm side and a cool
  side so the ramp can carry both discrete classes and continuous data.

Name the palette after the place, the art form or the work itself. One word,
capitalized, no spaces. Kashan, Isfahan, Tabriz, Shiraz, Mina, Zarrin. Add a
pronunciation so readers can say it, stress goes on the last syllable in
Persian.

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
`palettes/kashan.json` as a template for a museum source, or
`palettes/golestan.json` for your own photograph. Fill in every source field.
Write one short note per color saying where in the artwork it comes from, and
add the pronunciation. A second photo showing the work in its setting can go
in `source.context_image` with a caption, it appears on the palette page.
Leave out `order` and `colorblind` if you want the build to compute them.

## Step 6, build

```
python tools/build.py <name>
```

This regenerates the Python, R, ArcGIS and QGIS files for the whole
collection, renders your swatch, gallery card, preview and sample plots,
writes `docs/<name>/README.md` and adds your palette to the gallery in the
main README. Look at the sample page it produced. If a plot reads badly, go
back to step 4.

The rainfall and elevation panels use the real grids in `data/`, one day of
NOAA AORC precipitation and a CONUS DEM. Pass your own raster with
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
| `persian` | yes | the name in Persian script, like کاشان |
| `pronunciation` | yes | how to say it, like "kah-SHAHN", add the meaning if you like |
| `position` | no | gallery order, the build assigns the next slot when absent |
| `colors` | yes | 5 to 12 hex codes in ramp order |
| `notes` | yes | one short phrase per color, where in the artwork it lives |
| `order` | no | pick order for discrete use, computed by the build if absent |
| `colorblind` | no | set by the build from the worst case separation if absent |
| `source.title` | yes | object or work title |
| `source.artist` | no | empty string when unknown |
| `source.date` | yes | as the museum or reference gives it |
| `source.geography` | yes | for example "Iran, probably Kashan" |
| `source.medium` | yes | for example "Glazed polychrome tilework" |
| `source.museum` | museum sources | full museum name |
| `source.site` | own photos | the place, for example "Golestan Palace, UNESCO World Heritage Site" |
| `source.department` | no | museum department |
| `source.accession` | museum sources | accession number |
| `source.credit` | own photos | your credit line, "Photo by Your Name, year" |
| `source.url` | yes | object page or reference page for the site |
| `source.image` | yes | image URL, or repo path under `sources/` for your own photo |
| `source.card_image` | no | square crop used beside the palette in the gallery, falls back to `source.image` |
| `source.context_image` | no | second photo showing the work in its setting |
| `source.context_caption` | no | one line under the context photo |
| `source.public_domain` | yes | true for open access images, false for your own photo |
| `source.rights` | own photos | for example "photographer's own work, contributed to the project" |
