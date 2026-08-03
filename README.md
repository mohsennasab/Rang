# Rang | رنگ <img align="right" src="logo/rang.png" width="200">

Rang is a collection of color palettes drawn from the visual traditions of
Persian art. Drawing from carpets, miniature
paintings, tilework, manuscripts, ceramics and architecture, each palette
turns the character of an artwork into a practical color scheme.

The name Rang (Persian: رنگ) means "color" in Persian. The goal is to
preserve the character of these works while adapting them for data
visualization, cartography and creative coding.

Every palette traces to a documented source photograph. Each record explains
where its colors came from and reports the nearest match in a sampled, reduced
copy of the photograph. The pages also report pairwise separation under four
viewing simulations. Sample plots include NOAA AORC rainfall and CONUS
elevation data.

Use Rang with Python, R, ArcGIS Pro, QGIS, GeoLibre and HEC-RAS. The same
palette can move easily from code to maps and hydraulic models.

Created by **Mohsen Tahmasebi Nasab, PhD**. Read
[the story behind Rang](https://hydromohsen.com/blog/the-story-behind-rang/).

## Contents

[Palettes](#palettes) | [Install](#install) | [Use](#use-the-palettes) | [How they are made](#how-palettes-are-made) | [Contribute](#contributing) | [Credits and license](#credits-and-license)

## Palettes

Each entry shows the artwork beside its palette and links to a page with
sample plots, per color provenance and color vision numbers.

<!-- gallery:start -->

### Kashan

![Kashan, the artwork and its palette](docs/kashan/card.png)

Silk Kashan Carpet, 16th century. The Metropolitan Museum of Art, New York. [Reference](https://www.metmuseum.org/art/collection/search/451470) Persian: کاشان. Say it kah-SHAHN.

`#7f3020 #ab4a47 #c07049 #c59b46 #ccac7e #e2cfb1 #8a9463 #345f72 #1a3b45`

[Sample plots and full details](docs/kashan/README.md)

***

### Golestan

![Golestan, the artwork and its palette](docs/golestan/card.png)

Hunting-scene tile panel at Golestan Palace, photographed 2018. Golestan Palace, UNESCO World Heritage Site. Photo by Mohsen Tahmasebi Nasab, 2018. [Reference](https://whc.unesco.org/en/list/1422/) Passes the project CVD separation check. Persian: گلستان. Say it goh-leh-STAHN, Persian for rose garden.

`#432f2c #ae6259 #b57f86 #b5b5ac #cbb11c #9a9a68 #45939c #577ab1 #333a80`

[Sample plots and full details](docs/golestan/README.md)

***

### Termeh

![Termeh, the artwork and its palette](docs/termeh/card.png)

Termeh cloth with boteh motifs, photographed 2026. Yazd textile tradition. Photo by Mohsen Tahmasebi Nasab, 2026. [Reference](https://asia-archive.si.edu/object/S2017.14/) Persian: ترمه. Say it tehr-MEH.

A sequential ramp made for water surface elevation and depth rasters, following the termeh's blue ground from foam light to deep indigo. The colors are named for the water they are meant to carry: Foam Mist, Glacial Blue, Powder Aqua, River Teal, Slate Blue, Deep Channel and Night Current.

`#e5f0ee #c8dfe3 #a9ccd7 #7fb5c1 #5d95a8 #3e738e #274e68`

[Sample plots and full details](docs/termeh/README.md)

***

### Khatam

![Khatam, the artwork and its palette](docs/khatam/card.png)

Khatam panel with brass stars, 2026. Khatam marquetry tradition. Photos by Mohsen Tahmasebi Nasab, 2018 and 2026. [Reference](https://www.iranicaonline.org/articles/isfahan-xiii-crafts/) Persian: خاتم. Say it khaw-TAM.

A warm ramp from khatam marquetry, the Persian craft of laying wood, bone and brass into star patterns. It runs from ebony dark to brass bright, and the discrete picks jump between wood, metal and bone so classes stay easy to tell apart.

`#1c110b #542020 #8d310e #bf480d #b27a3c #c58c51 #d9a545 #dbba94 #e5c870`

[Sample plots and full details](docs/khatam/README.md)

***

### Nasir

![Nasir, the artwork and its palette](docs/nasir/card.png)

Stained-glass window at Nasir al-Mulk Mosque, 2018. Nasir al-Mulk Mosque. Photograph by Tpmehdi, 2018. [Reference](https://commons.wikimedia.org/wiki/File:DSC_0277-%D9%85%D8%B3%D8%AC%D8%AF_%D9%86%D8%B5%DB%8C%D8%B1%D8%A7%D9%84%D9%85%D9%84%DA%A9.jpg) Persian: نصیر. Say it nah-SEER, from Nasir al-Mulk Mosque in Shiraz.

A vivid spectrum drawn from the stained glass of Nasir al-Mulk Mosque in Shiraz. Violet and cobalt open into cyan and green, then warm through gold to vermilion. It is especially lively for categories, lines and maps that call for strong contrast.

`#261410 #3b1261 #4027e1 #518ffd #74ecf9 #50a877 #6dd96f #ebc05c #f04a23`

[Sample plots and full details](docs/nasir/README.md)

<!-- gallery:end -->

## Saying the names

The names are Persian, and they are easy once you see them spelled out. The
stress lands on the last syllable.

| name | Persian | say it | meaning |
|---|---|---|---|
| Rang | رنگ | rahng, close to the English word rung | color |
| Kashan | کاشان | kah-SHAHN | a city famous for its carpets and silks |
| Golestan | گلستان | goh-leh-STAHN | rose garden, the Qajar palace in Tehran |
| Termeh | ترمه | tehr-MEH | a patterned textile associated with Yazd |
| Khatam | خاتم | khaw-TAM | marquetry of star patterns in wood, bone and brass |
| Nasir | نصیر | nah-SEER | from Nasir al-Mulk Mosque in Shiraz |

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

### ArcGIS Pro, QGIS, GeoLibre and HEC-RAS

No Rang install is needed. Grab the files from [arcgis/](arcgis/),
[qgis/](qgis/), [geolibre/](geolibre/) or [hecras/](hecras/) and follow the
matching guide, [ArcGIS](arcgis/README.md), [QGIS](qgis/README.md),
[GeoLibre](geolibre/README.md) or [HEC-RAS](hecras/README.md).

## Use the palettes

Want to try Rang without setting anything up locally? Start with the
[Colab-ready Python and R examples](examples/).

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

Import [arcgis/Rang.stylx](arcgis/Rang.stylx) once through the Catalog pane
and every palette lands in the color scheme dropdowns, smooth and discrete,
plus the individual colors in every color picker. Color schemes live in the
symbology rather than the dataset, so this works for any raster type,
floating point included. Steps are in the [ArcGIS guide](arcgis/README.md).

### QGIS

Import [qgis/Rang.xml](qgis/Rang.xml) once through the Style Manager and every
palette appears in the color ramp dropdowns, smooth and discrete. The `.gpl`
files add the exact colors to the QGIS color picker. Steps are in the
[QGIS guide](qgis/README.md).

### GeoLibre

Copy a prepared color list from [geolibre/Rang.txt](geolibre/Rang.txt) into a
raster Custom color ramp. For vectors, use the matching graduated or
categorical list to replace the generated class colors. A machine-readable
bundle for notebooks and project tooling is available as
[geolibre/Rang.json](geolibre/Rang.json). The [GeoLibre guide](geolibre/README.md)
covers raster layers, vector layers, legends, colorbars and Jupyter use.

### HEC-RAS

Import [hecras/Rang-All.xml](hecras/Rang-All.xml) through the RAS Mapper
Surface Fill window to add the full collection, or download one palette from
the [hecras folder](hecras/). The [HEC-RAS guide](hecras/README.md) walks
through the interface step by step.

## How palettes are made

The short version, with the full walkthrough in
[CONTRIBUTING.md](CONTRIBUTING.md):

1. Colors are sampled from a photo of the artwork by k-means clustering in
   CIELAB, run region by region rather than over the whole image so small
   motifs are not averaged away by large fields of background. Sources are
   museum open access photos or the contributor's own photographs.
2. The candidate set is trimmed to a ramp of five to twelve colors and checked
   against a sampled, reduced copy of the photo. Each palette page publishes
   the nearest CIEDE2000 distance found in that sample.
3. Separation is measured under normal vision and simulated protanopia,
   deuteranopia and tritanopia. A pick order is computed so that the first few
   discrete colors stay as far apart as possible under every vision type.
4. One build command regenerates the Python, R, ArcGIS, QGIS, GeoLibre and
   HEC-RAS files, the sample plots and the documentation, so every palette in
   the collection is packaged the same way.

The sample pages use real data on purpose: one day of NOAA AORC 1 km rainfall
from Hurricane Harvey, a CONUS elevation grid from AWS Open Data, and, for the
water palettes, a USGS flood profile and stream network from Ithaca, New York.
The fetch scripts live in [tools/](tools/README.md).

## Contributing

New palettes are welcome. The bar is that the source is Persian art with a
photograph you have the rights to share, the colors verifiably come from that
photograph, and the palette page is produced by the standard tooling so it
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
arcgis/      Rang.stylx style file and the ArcGIS Pro guide
qgis/        style file, .gpl swatches and the QGIS guide
geolibre/    copy-ready and machine-readable color lists plus a usage guide
hecras/      HEC-RAS custom color-ramp imports and the interface guide
tools/       contributor scripts, extraction to build
docs/        one page per palette with previews and sample plots
data/        small real rainfall and elevation grids for the sample plots
examples/    Colab-ready Python and R notebooks using public online data
```

## Credits and license

Rang source code is licensed under the [MIT License](LICENSE). To the extent
that copyright or database rights apply, the palette names, color values,
descriptions, and ordering are dedicated to the public domain under
[CC0 1.0 Universal](LICENSES/CC0-1.0.txt). The palettes may therefore be used
for any purpose without permission or credit, though a link back is always
appreciated. The complete file-by-file scope is in
[the licensing guide](LICENSES/README.md).

Artwork photographs are not covered by the MIT License or CC0 unless stated
otherwise. The Golestan, Termeh and Khatam photographs remain copyright
Mohsen Tahmasebi Nasab, with all rights reserved. The Kashan palette draws
on the
[Silk Kashan Carpet](https://www.metmuseum.org/art/collection/search/451470)
at The Metropolitan Museum of Art, whose qualifying Open Access images are
available under CC0. The Golestan palette comes from a photograph of the
tilework at
[Golestan Palace](https://whc.unesco.org/en/list/1422/) in Tehran, taken by
Mohsen Tahmasebi Nasab in 2018. The Termeh palette comes from his photograph
of a termeh cloth, 2026. The Smithsonian's
[termeh record](https://asia-archive.si.edu/object/S2017.14/) documents the
Yazd tradition and the boteh motif. The Khatam palette comes from his
photographs of khatam marquetry, 2026, and of a handicraft shop in the
Isfahan bazaar, 2018. The Encyclopaedia Iranica article on
[crafts in Isfahan](https://www.iranicaonline.org/articles/isfahan-xiii-crafts/)
documents the craft's history in Shiraz, Isfahan and Tehran.
The Nasir palette draws on a
[stained-glass photograph](https://commons.wikimedia.org/wiki/File:DSC_0277-%D9%85%D8%B3%D8%AC%D8%AF_%D9%86%D8%B5%DB%8C%D8%B1%D8%A7%D9%84%D9%85%D9%84%DA%A9.jpg)
by Tpmehdi, 2018, and an
[interior photograph](https://commons.wikimedia.org/wiki/File:Nasir_al-_mulk_mosque%2C_Shiraz.jpg)
by MohammadReza Domiri Ganji, 2013. Both are licensed under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

The sample plots use public data: rainfall from the
[NOAA Analysis of Record for Calibration](https://registry.opendata.aws/noaa-nws-aorc/),
elevation from the AWS Open Data
[terrain tiles](https://registry.opendata.aws/terrain-tiles/) built on SRTM,
GMTED2010 and ETOPO1, water surface elevation from the
[USGS flood inundation study of the Ithaca creeks](https://www.sciencebase.gov/catalog/item/5b757eb6e4b0f5d5787fe461),
and stream networks from the
[USGS Network Linked Data Index](https://api.water.usgs.gov/nldi/), with
NHDPlusV2 stream order from [USGS Fabric](https://api.water.usgs.gov/docs/fabric-pygeoapi/).
Detailed source status, requested credits, and data notices are recorded in
[the third-party notices](THIRD_PARTY_NOTICES.md).

The package interface tries to follow the conventions set by
[MetBrewer](https://github.com/BlakeRMills/MetBrewer) and
[wesanderson](https://github.com/karthik/wesanderson).
