# Kashan (Persian: کاشان, say it kah-SHAHN)

![Kashan swatch](swatch.png)

## Source

Silk Kashan Carpet, 16th century. Iran, probably Kashan.
Silk (warp, weft and pile), asymmetrically knotted pile.
The Metropolitan Museum of Art, New York, Islamic Art, accession 58.46.
Gift of Mrs. Douglas M. Moffat, 1958.

[Object page](https://www.metmuseum.org/art/collection/search/451470) and [full resolution photo](https://images.metmuseum.org/CRDImages/is/original/DT5450.jpg), released by the museum under open access.

## Colors

| position | hex | drawn from | nearest pixel |
|---|---|---|---|
| 1 | `#7f3020` | deep madder, corner cartouche outlines | 1.1 |
| 2 | `#ab4a47` | rose red of the field | 0.3 |
| 3 | `#c07049` | terracotta | 0.9 |
| 4 | `#c59b46` | saffron gold, medallion palmettes | 0.0 |
| 5 | `#ccac7e` | tan of the border ground | 0.3 |
| 6 | `#e2cfb1` | ivory, medallion star and cartouches | 0.8 |
| 7 | `#8a9463` | sage green, guard border | 3.0 |
| 8 | `#345f72` | mid blue, medallion lobes | 0.5 |
| 9 | `#1a3b45` | indigo, medallion ground | 0.2 |

The nearest pixel column is the CIEDE2000 distance from each palette color to
the closest pixel in the source photo. Small numbers mean the color is really
in the artwork.

## The palette beside the artwork

![Kashan preview](preview.png)

## Sample plots

![Kashan samples](samples.png)

The rainfall panel is real data, one day of NOAA AORC 1 km precipitation.
Regenerate this page with `python tools/make_samples.py kashan`, and
pass `--dem your_dem.tif` to draw the elevation panel from your own raster.

## Separation and color vision

| vision | min CIEDE2000 | mean |
|---|---|---|
| normal vision | 9.1 | 34.2 |
| protanopia | 7.9 | 28.2 |
| deuteranopia | 5.9 | 28.8 |
| tritanopia | 6.2 | 34.2 |

The worst case across the four vision types is 5.9, so this palette
does not pass the collection's colorblind friendliness threshold of 8.
Discrete picks use the stored order, which was chosen to keep the first few
colors as far apart as possible under every vision type.

## Use it

Python

```python
import rang
rang.rang("Kashan", 5)
rang.cmap("Kashan")
```

R

```r
library(Rang)
rang("Kashan", 5)
```

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/Kashan.gpl](../../qgis/Kashan.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS surface fills are in
[hecras/Kashan.rasmap.xml](../../hecras/Kashan.rasmap.xml), see the
[HEC-RAS guide](../../hecras/README.md).
