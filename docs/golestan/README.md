# Golestan (Persian: گلستان, say it goh-leh-STAHN, Persian for rose garden)

![Golestan swatch](swatch.png)

## Source

Hunting-scene tile panel at Golestan Palace, photographed 2018. Tehran, Iran.
Glazed polychrome tilework.
Golestan Palace, UNESCO World Heritage Site.
Photo by Mohsen Tahmasebi Nasab, 2018.

[Site reference](https://whc.unesco.org/en/list/1422/). Photographer's own work, contributed to the project.

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

The nearest sample column is the CIEDE2000 distance from each palette color to
the closest evaluated point in a reduced copy of the source photo. Small
numbers show that a close visual match occurs in the sampled image.

## The palette beside the artwork

![Golestan preview](preview.png)

## Sample plots

![Golestan samples](samples.png)

The rainfall panel is real data, one day of NOAA AORC precipitation on a roughly 1 km grid.
Regenerate this page with `python tools/make_samples.py golestan`, and
pass `--dem your_dem.tif` to draw the elevation panel from your own raster.

## Separation and color vision

| vision | min CIEDE2000 | mean |
|---|---|---|
| normal vision | 12.1 | 36.4 |
| protanopia | 8.4 | 30.4 |
| deuteranopia | 9.7 | 31.7 |
| tritanopia | 8.0 | 34.4 |

The worst case across the four vision types is 8.0, so this palette
passes the project's CVD separation threshold of 8.
The margin is less than 0.1, so small changes to a color or the simulation can alter the result.
This screening rule is not an accessibility guarantee.
Discrete picks use the stored order, which was chosen to keep the first few
colors as far apart as possible under every vision type.

## Use it

Python

```python
import rang
rang.rang("Golestan", 5)
rang.cmap("Golestan")
```

R

```r
library(Rang)
rang("Golestan", 5)
```

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/Golestan.gpl](../../qgis/Golestan.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS surface fills are in
[hecras/Golestan.rasmap.xml](../../hecras/Golestan.rasmap.xml), see the
[HEC-RAS guide](../../hecras/README.md).
