# Rang

Rang is a collection of thoughtfully crafted color palettes inspired by the
rich visual traditions of Persian art. Drawing from carpets, miniature
paintings, tilework, manuscripts, ceramics and architecture, each palette
translates historic colors into clear, expressive and accessible schemes for
Python, R and ArcGIS Pro.

The name Rang means "color" in Persian. The goal is to preserve the character
of these works while adapting them for data visualization, cartography and
creative coding.

Every palette here traces back to a specific museum object with an open access
photograph. Each one documents where its colors came from, how far each color
sits from actual pixels of the artwork, and how well the set holds up under
simulated color vision deficiency. Sample pages show the palette on real plot
types before you commit to it.

## Contents

- [Palettes](#palettes)
- [Install](#install)
- [Use the palettes](#use-the-palettes)
  - [Python](#python)
  - [R](#r)
  - [ArcGIS Pro](#arcgis-pro)
- [How palettes are made](#how-palettes-are-made)
- [Contributing](#contributing)
- [Repository layout](#repository-layout)
- [Credits and license](#credits-and-license)

## Palettes

Each palette links to its own page with the source artwork, sample plots,
per color provenance and color vision numbers.

<!-- gallery:start -->

### Kashan

![Kashan](docs/kashan/swatch.png)

Silk Kashan Carpet, 16th century. Iran, probably Kashan.
The Metropolitan Museum of Art, New York, accession 58.46. [Object page](https://www.metmuseum.org/art/collection/search/451470)

`#7f3020 #ab4a47 #c07049 #c59b46 #ccac7e #e2cfb1 #8a9463 #345f72 #1a3b45`

[Sample plots and full details](docs/kashan/README.md)

<!-- gallery:end -->

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

### ArcGIS Pro

No install. Grab the `.clr` files from [arcgis/](arcgis/) and follow the
[ArcGIS guide](arcgis/README.md).

## Use the palettes

Palettes are stored as a color ramp plus a pick order. Asking for a few colors
returns a well separated subset chosen for legibility, asking for more than
the palette holds interpolates along the ramp.

### Python

```python
import rang

rang.list_palettes()                     # available names
rang.rang("Kashan")                      # the full ramp
rang.rang("Kashan", 4)                   # four well separated colors
rang.rang("Kashan", 100, "continuous")   # smooth ramp for gridded data

# matplotlib
import matplotlib.pyplot as plt
plt.imshow(data, cmap=rang.cmap("Kashan"))

# where the colors came from
rang.source("Kashan")
```

### R

```r
library(Rang)

names(rang_palettes)                     # available names
rang("Kashan")                           # the full ramp, prints as a swatch
rang("Kashan", 4)                        # four well separated colors
rang("Kashan", 100, type = "continuous") # smooth ramp

# ggplot2
ggplot(iris, aes(Species, Petal.Length, fill = Species)) +
  geom_violin() +
  scale_fill_manual(values = rang("Kashan", 3))

ggplot(faithfuld, aes(waiting, eruptions, fill = density)) +
  geom_raster() +
  scale_fill_gradientn(colors = rang("Kashan", 100, type = "continuous"))
```

### ArcGIS Pro

Each palette ships a discrete and a continuous `.clr` colormap file in
[arcgis/](arcgis/). Apply them to rasters with the Add Colormap tool, or build
a reusable color scheme from the hex codes. Step by step instructions are in
the [ArcGIS guide](arcgis/README.md).

## How palettes are made

The short version, with the full walkthrough in
[CONTRIBUTING.md](CONTRIBUTING.md):

1. Colors are sampled from an open access museum photo by k-means clustering
   in CIELAB, run region by region rather than over the whole image so small
   motifs are not averaged away by large fields of background.
2. The candidate set is trimmed to a ramp of five to twelve colors and checked
   against the photo. Each color should sit within a small CIEDE2000 distance
   of real pixels, and each palette page publishes those distances.
3. Separation is measured under normal vision and simulated protanopia,
   deuteranopia and tritanopia. A pick order is computed so that the first few
   discrete colors stay as far apart as possible under every vision type.
4. One build command regenerates the Python, R and ArcGIS files, the sample
   plots and the documentation, so every palette in the collection is packaged
   the same way.

The scripts behind each step live in [tools/](tools/README.md) and are the
same ones contributors use.

## Contributing

New palettes are welcome. The bar is that the source is Persian art with an
open access photograph, the colors verifiably come from that photograph, and
the palette page is built with the standard tooling so it matches the rest of
the collection. [CONTRIBUTING.md](CONTRIBUTING.md) walks through the whole
process, from picking an artwork to opening a pull request, including the
sample code for extracting colors from a photo and adjusting any color that
does not sit right.

## Repository layout

```
palettes/    one json per palette, the single source of truth
python/      pip installable package, reads generated _palettes.py
r/           R package, reads generated palettes_data.R
arcgis/      .clr colormap files and the ArcGIS Pro guide
tools/       contributor scripts, extraction to build
docs/        one page per palette with previews and sample plots
data/        the small CONUS elevation grid used by the sample plots
```

## Credits and license

Code is MIT licensed. The palettes themselves are free to use anywhere, with
or without credit, though a link back is always appreciated.

Artwork photographs belong to their museums and are used under their open
access programs. The first palette draws on the
[Silk Kashan Carpet](https://www.metmuseum.org/art/collection/search/451470)
at The Metropolitan Museum of Art, New York.

The elevation grid behind the map panels comes from the
[AWS Open Data terrain tiles](https://registry.opendata.aws/terrain-tiles/),
which composite SRTM, GMTED2010, ETOPO1 and other public datasets.

The package interface follows the conventions set by
[MetBrewer](https://github.com/BlakeRMills/MetBrewer) and
[wesanderson](https://github.com/karthik/wesanderson), which made this style
of palette package familiar to a lot of people.
