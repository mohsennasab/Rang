# Golestan (Persian: گلستان, say it goh-leh-STAHN, Persian for rose garden)

![Golestan swatch](swatch.png)

## Source

Hunting-scene tile panel at Golestan Palace, photographed 2018. Tehran, Iran.
Glazed polychrome tilework.
Golestan Palace, UNESCO World Heritage Site.
Photo by Mohsen Tahmasebi Nasab, 2018.

[Site reference](https://whc.unesco.org/en/list/1422/). Copyright Mohsen Tahmasebi Nasab, all rights reserved.

## The setting

![The panel in place at the palace, with a resident cat](../../sources/golestan/palace.jpg)

The panel in place at the palace, with a resident cat.

## Colors

| position | hex | drawn from | nearest sample |
|---|---|---|---|
| 1 | `#432f2c` | dark umber, outlines and the hunter's horse | 0.7 |
| 2 | `#ae6259` | coral red, blossoms and the rider's coat | 0.6 |
| 3 | `#b57f86` | rose pink, flowers among the scrollwork | 0.4 |
| 4 | `#b5b5ac` | ivory, tile ground of the medallion | 0.3 |
| 5 | `#cbb11c` | golden yellow, the field | 0.0 |
| 6 | `#9a9a68` | pale olive, the hunting ground | 0.7 |
| 7 | `#45939c` | turquoise, the medallion ring | 0.6 |
| 8 | `#577ab1` | azure, lit edges of the scrollwork | 0.3 |
| 9 | `#333a80` | cobalt, the arabesque scrolls | 0.0 |

The last column shows the CIEDE2000 distance to the closest sampled color in
the source photo. Lower numbers mean a closer match.

## The palette beside the artwork

![Golestan preview](preview.png)

## Extraction regions

![Golestan extraction regions](regions.png)

These are the saved sampling areas used for CIELAB k-means. The exact pixel
coordinates, normalized coordinates and k values are recorded in the
[Golestan recipe](../../recipes/golestan.json). The regions make the
extraction repeatable. Choosing and refining the final colors still depends
on the artwork and the contributor's eye.

## Sample plots

![Golestan samples](samples.png)

The rainfall map uses one day of NOAA AORC precipitation on a roughly 1 km grid.
Run `python tools/make_samples.py golestan` to remake the plots. Add
`--dem your_dem.tif` to use your own elevation raster.

## Separation and color vision

| vision | min CIEDE2000 | mean |
|---|---|---|
| normal vision | 12.1 | 36.4 |
| protanopia | 8.4 | 30.4 |
| deuteranopia | 9.7 | 31.7 |
| tritanopia | 8.0 | 34.4 |

The lowest score is 8.0. Rang's cutoff is 8, so all pairwise scores are above it. The difference is less than 0.1, so treat Golestan as borderline.

When you ask for fewer colors, the stored pick order spreads them out. Check the finished figure when color distinction matters.

## Use it

Python

```python
import rang

rang.rang("Golestan", 5)              # five well separated colors
rang.cmap("Golestan")                 # smooth matplotlib colormap
rang.cmap("Golestan", 6)              # six fixed steps for classified data

rang.register()                     # then use it anywhere by name
data.plot(cmap="rang:Golestan")
```

R

```r
library(Rang)
library(ggplot2)

rang("Golestan", 5)                   # five well separated colors

# categories
ggplot(df, aes(group, value, fill = group)) +
  geom_col() +
  scale_fill_rang_d("Golestan")

# a numeric variable
ggplot(df, aes(x, y, color = value)) +
  geom_point() +
  scale_color_rang_c("Golestan")
```

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/Golestan.gpl](../../qgis/Golestan.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS users can import
[hecras/Rang-Golestan.xml](../../hecras/Rang-Golestan.xml), see the
[HEC-RAS guide](../../hecras/README.md). GeoLibre users can copy colors from
[geolibre/Rang.txt](../../geolibre/Rang.txt), with steps for raster and vector
layers in the [GeoLibre guide](../../geolibre/README.md).
