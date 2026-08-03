# Khatam (Persian: خاتم, say it khaw-TAM)

![Khatam swatch](swatch.png)

A warm ramp from khatam marquetry, the Persian craft of laying wood, bone and brass into star patterns. It runs from ebony dark to brass bright, and the discrete picks jump between wood, metal and bone so classes stay easy to tell apart.

## Source

Khatam panel with brass stars.
Wood, bone and brass marquetry.
Khatam marquetry tradition.
Photos by Mohsen Tahmasebi Nasab, 2018 and 2026.

[Craft history](https://www.iranicaonline.org/articles/isfahan-xiii-crafts/). Copyright Mohsen Tahmasebi Nasab, all rights reserved.

## The setting

![A handicraft shop in the Isfahan bazaar, 2018, khatam boxes stacked in front of minakari enamel and metalwork](../../sources/khatam/bazaar.jpg)

A handicraft shop in the Isfahan bazaar, 2018, khatam boxes stacked in front of minakari enamel and metalwork.

## The craft

Khatam, also called khatam-kari or khatam-sazi, is Persian marquetry made from small pieces of wood, bone and brass. The pieces form dense mosaics of stars and other geometric shapes on boxes, furniture, frames, doors and musical instruments. The geometry does the drawing. In the source photo, each star, dot and triangle comes from the cross section of bundled material.

Encyclopaedia Iranica traces khatam work in Shiraz and Isfahan to at least the Zand period in the late eighteenth century. The craft later declined and was revived in Isfahan during the twentieth century, with palace commissions in Tehran helping it flourish again. Khatam boxes and small objects are still easy to spot in Iranian handicraft shops, like those in the second photograph.

## Colors

| position | hex | drawn from | nearest sample |
|---|---|---|---|
| 1 | `#1c110b` | ebony dark, the stained triangles around each star | 0.3 |
| 2 | `#542020` | maroon, the dyed divider rails | 0.5 |
| 3 | `#8d310e` | russet, orange rods in shadow | 0.7 |
| 4 | `#bf480d` | burnt orange, the brightest rods | 0.4 |
| 5 | `#b27a3c` | oak brown, framing strips | 0.4 |
| 6 | `#c58c51` | light oak, sanded frame edges | 0.5 |
| 7 | `#d9a545` | straw gold, the hexagon field | 0.3 |
| 8 | `#dbba94` | bone, the pale triangles | 0.3 |
| 9 | `#e5c870` | brass, the six point stars | 0.7 |

The nearest sample column is the CIEDE2000 distance from each palette color to
the closest evaluated point in a reduced copy of the source photo. Small
numbers show that a close visual match occurs in the sampled image.

## The palette beside the artwork

![Khatam preview](preview.png)

## Sample plots

![Khatam samples](samples.png)

The rainfall panel is real data, one day of NOAA AORC precipitation on a roughly 1 km grid.
Regenerate this page with `python tools/make_samples.py khatam`, and
pass `--dem your_dem.tif` to draw the elevation panel from your own raster.

## Separation and color vision

| vision | min CIEDE2000 | mean |
|---|---|---|
| normal vision | 6.2 | 32.5 |
| protanopia | 6.5 | 30.3 |
| deuteranopia | 6.0 | 29.3 |
| tritanopia | 3.5 | 29.5 |

The worst case across the four vision types is 3.5, so this palette
does not pass the project's CVD separation threshold of 8.
This screening rule is not an accessibility guarantee.
Discrete picks use the stored order, which was chosen to keep the first few
colors as far apart as possible under every vision type.

## Use it

Python

```python
import rang
rang.rang("Khatam", 5)
rang.cmap("Khatam")
```

R

```r
library(Rang)
rang("Khatam", 5)
```

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/Khatam.gpl](../../qgis/Khatam.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS surface fills are in
[hecras/Khatam.rasmap.xml](../../hecras/Khatam.rasmap.xml), see the
[HEC-RAS guide](../../hecras/README.md). GeoLibre users can copy colors from
[geolibre/Rang.txt](../../geolibre/Rang.txt), with steps for raster and vector
layers in the [GeoLibre guide](../../geolibre/README.md).
