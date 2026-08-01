# Rang

Rang is a collection of thoughtfully crafted color palettes inspired by the
rich visual traditions of Persian art. Drawing from carpets, miniature
paintings, tilework, manuscripts, ceramics and architecture, each palette
translates historic colors into clear, expressive and accessible schemes for
Python, R, ArcGIS Pro and QGIS.

The name Rang means "color" in Persian. The goal is to preserve the character
of these works while adapting them for data visualization, cartography and
creative coding.

Every palette here traces back to a specific artwork with a documented
photograph. Each one records where its colors came from, how far each color
sits from actual pixels of the photo, and how well the set holds up under
simulated color vision deficiency. Sample pages show the palette on real data,
including NOAA AORC rainfall and CONUS elevation, before you commit to it.

## Contents

- [Palettes](#palettes)
- [Saying the names](#saying-the-names)
- [Install](#install)
- [Use the palettes](#use-the-palettes)
  - [Python](#python)
  - [R](#r)
  - [ArcGIS Pro](#arcgis-pro)
  - [QGIS](#qgis)
- [How palettes are made](#how-palettes-are-made)
- [Contributing](#contributing)
- [Repository layout](#repository-layout)
- [Credits and license](#credits-and-license)

## Palettes

Each entry shows the artwork beside its palette and links to a page with
sample plots, per color provenance and color vision numbers.

<!-- gallery:start -->

### Golestan

![Golestan, the artwork and its palette](docs/golestan/card.png)

Tile panel with a hunting scene, Qajar period. Golestan Palace, UNESCO World Heritage Site. Photo by Mohsen Tahmasebi Nasab, 2018. [Reference](https://whc.unesco.org/en/list/1422/) Colorblind friendly. Say it goh-leh-STAHN, Persian for rose garden.

`#432f2c #ae6259 #b57f86 #b5b5ac #cbb11c #9a9a68 #45939c #577ab1 #333a80`

[Sample plots and full details](docs/golestan/README.md)

***

### Kashan

![Kashan, the artwork and its palette](docs/kashan/card.png)

Silk Kashan Carpet, 16th century. The Metropolitan Museum of Art, New York. [Reference](https://www.metmuseum.org/art/collection/search/451470) Say it kah-SHAHN.

`#7f3020 #ab4a47 #c07049 #c59b46 #ccac7e #e2cfb1 #8a9463 #345f72 #1a3b45`

[Sample plots and full details](docs/kashan/README.md)

<!-- gallery:end -->

## Saying the names

The names are Persian, and they are easy once you see them spelled out. The
stress lands on the last syllable.

| name | say it | meaning |
|---|---|---|
| Rang | rahng, close to the English word rung | color |
| Kashan | kah-SHAHN | a city famous for its carpets and silks |
| Golestan | goh-leh-STAHN | rose garden, the Qajar palace in Tehran |

Every palette page repeats its own pronunciation, and new palettes add
themselves to this pattern through their json file.

## Install

### Python

```
pip install "git+https://github.com/mohsennasab/Rang.git#subdirectory=python"
```

No required dependencies. `rang.cmap()` needs matplotlib.

### R

```r
install.packages("remotes")
remotes::install_github("mohsennasab/Rang", subdir = "r")
```

### ArcGIS Pro and QGIS

No install. Grab the files from [arcgis/](arcgis/) or [qgis/](qgis/) and
follow the [ArcGIS guide](arcgis/README.md) or the [QGIS guide](qgis/README.md).

## Use the palettes

Palettes are stored as a color ramp plus a pick order. Asking for a few colors
returns a well separated subset chosen for legibility, asking for more than
the palette holds interpolates along the ramp.

### Python

```python
import rang

rang.list_palettes()                     # available names
rang.rang("Golestan")                    # the full ramp
rang.rang("Golestan", 4)                 # four well separated colors
rang.rang("Kashan", 100, "continuous")   # smooth ramp for gridded data

# matplotlib
import matplotlib.pyplot as plt
plt.imshow(data, cmap=rang.cmap("Kashan"))

# where the colors came from
rang.source("Golestan")
```

### R

```r
library(Rang)

names(rang_palettes)                     # available names
rang("Golestan")                         # the full ramp, prints as a swatch
rang("Golestan", 4)                      # four well separated colors
rang("Kashan", 100, type = "continuous") # smooth ramp

# ggplot2
ggplot(iris, aes(Species, Petal.Length, fill = Species)) +
  geom_violin() +
  scale_fill_manual(values = rang("Golestan", 3))

ggplot(faithfuld, aes(waiting, eruptions, fill = density)) +
  geom_raster() +
  scale_fill_gradientn(colors = rang("Kashan", 100, type = "continuous"))
```

### ArcGIS Pro

Each palette ships a discrete and a continuous `.clr` colormap file in
[arcgis/](arcgis/). Apply them to rasters with the Add Colormap tool, or build
a reusable color scheme from the hex codes. Steps are in the
[ArcGIS guide](arcgis/README.md).

### QGIS

Import [qgis/Rang.xml](qgis/Rang.xml) once through the Style Manager and every
palette appears in the color ramp dropdowns, smooth and discrete. The `.gpl`
files add the exact colors to the QGIS color picker. Steps are in the
[QGIS guide](qgis/README.md).

## How palettes are made

The short version, with the full walkthrough in
[CONTRIBUTING.md](CONTRIBUTING.md):

1. Colors are sampled from a photo of the artwork by k-means clustering in
   CIELAB, run region by region rather than over the whole image so small
   motifs are not averaged away by large fields of background. Sources are
   museum open access photos or the contributor's own photographs.
2. The candidate set is trimmed to a ramp of five to twelve colors and checked
   against the photo. Each color should sit within a small CIEDE2000 distance
   of real pixels, and each palette page publishes those distances.
3. Separation is measured under normal vision and simulated protanopia,
   deuteranopia and tritanopia. A pick order is computed so that the first few
   discrete colors stay as far apart as possible under every vision type.
4. One build command regenerates the Python, R, ArcGIS and QGIS files, the
   sample plots and the documentation, so every palette in the collection is
   packaged the same way.

The sample pages use real data on purpose: one day of NOAA AORC 1 km rainfall
from Hurricane Harvey and a CONUS elevation grid, both fetched from AWS Open
Data by scripts in [tools/](tools/README.md).

## Contributing

New palettes are welcome. The bar is that the source is Persian art with a
photograph you have the rights to share, the colors verifiably come from that
photograph, and the palette page is built with the standard tooling so it
matches the rest of the collection. [CONTRIBUTING.md](CONTRIBUTING.md) walks
through the whole process, from picking an artwork to opening a pull request,
including the sample code for extracting colors from a photo and adjusting any
color that does not sit right.

## Repository layout

```
palettes/    one json per palette, the single source of truth
sources/     contributor photographs referenced by the palette files
python/      pip installable package, reads generated _palettes.py
r/           R package, reads generated palettes_data.R
arcgis/      .clr colormap files and the ArcGIS Pro guide
qgis/        style file, .gpl swatches and the QGIS guide
tools/       contributor scripts, extraction to build
docs/        one page per palette with previews and sample plots
data/        small real rainfall and elevation grids for the sample plots
```

## Credits and license

Code is MIT licensed. The palettes themselves are free to use anywhere, with
or without credit, though a link back is always appreciated.

Artwork photographs stay with their owners. The Kashan palette draws on the
[Silk Kashan Carpet](https://www.metmuseum.org/art/collection/search/451470)
at The Metropolitan Museum of Art, used under its open access program. The
Golestan palette comes from a photograph of the tilework at
[Golestan Palace](https://whc.unesco.org/en/list/1422/) in Tehran, taken by
Mohsen Tahmasebi Nasab in 2018.

The sample plots use public data from the AWS Open Data program: rainfall
from the
[NOAA Analysis of Record for Calibration](https://registry.opendata.aws/noaa-nws-aorc/)
and elevation from the
[terrain tiles](https://registry.opendata.aws/terrain-tiles/) built on SRTM,
GMTED2010 and ETOPO1.

The package interface follows the conventions set by
[MetBrewer](https://github.com/BlakeRMills/MetBrewer) and
[wesanderson](https://github.com/karthik/wesanderson), which made this style
of palette package familiar to a lot of people.
