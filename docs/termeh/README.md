# Termeh (Persian: ترمه, say it tehr-MEH)

![Termeh swatch](swatch.png)

A sequential ramp made for water surface elevation and depth rasters, following the termeh's blue ground from foam light to deep indigo. The colors are named for the water they are meant to carry: Foam Mist, Glacial Blue, Powder Aqua, River Teal, Slate Blue, Deep Channel and Night Current.

## Source

Termeh cloth with boteh motifs, photographed 2026. Iran.
Textile.
Yazd textile tradition.
Photo by Mohsen Tahmasebi Nasab, 2026.

[Tradition reference](https://asia-archive.si.edu/object/S2017.14/). Copyright Mohsen Tahmasebi Nasab, all rights reserved.

## The setting

![Termeh at rest, a draped cloth, runners and a covered chest](../../sources/termeh/setting.jpg)

Termeh at rest, a draped cloth, runners and a covered chest.

## Colors

| position | hex | drawn from | nearest sample |
|---|---|---|---|
| 1 | `#e5f0ee` | Foam Mist, white thread highlights | 0.9 |
| 2 | `#c8dfe3` | Glacial Blue, pale silk detailing | 0.7 |
| 3 | `#a9ccd7` | Powder Aqua, light ground between motifs | 0.5 |
| 4 | `#7fb5c1` | River Teal, the twill ground itself | 0.8 |
| 5 | `#5d95a8` | Slate Blue, shaded folds of the ground | 1.1 |
| 6 | `#3e738e` | Deep Channel, blue fill of the boteh | 0.3 |
| 7 | `#274e68` | Night Current, the darkest indigo threads | 0.5 |

The nearest sample column is the CIEDE2000 distance from each palette color to
the closest evaluated point in a reduced copy of the source photo. Small
numbers show that a close visual match occurs in the sampled image.

## The palette beside the artwork

![Termeh preview](preview.png)

## Sample plots

![Termeh samples](samples.png)

Both panels use USGS data. The first shows the 100 year high flood
profile for the creeks at Ithaca, New York. The second uses NLDI
flowlines for Fall Creek, with widths based on NHDPlusV2 stream order
from USGS Fabric. The watershed interior is left unfilled.
Regenerate this page with `python tools/make_samples.py termeh`.

## Separation and color vision

| vision | min CIEDE2000 | mean |
|---|---|---|
| normal vision | 6.2 | 24.6 |
| protanopia | 5.2 | 23.3 |
| deuteranopia | 6.0 | 24.7 |
| tritanopia | 6.8 | 24.6 |

The worst case across the four vision types is 5.2, so this palette
does not pass the project's CVD separation threshold of 8.
This screening rule is not an accessibility guarantee.
Discrete picks use the stored order, which was chosen to keep the first few
colors as far apart as possible under every vision type.

## Use it

Python

```python
import rang
rang.rang("Termeh", 5)
rang.cmap("Termeh")
```

R

```r
library(Rang)
rang("Termeh", 5)
```

ArcGIS Pro users get every palette by importing
[arcgis/Rang.stylx](../../arcgis/Rang.stylx) once, with steps in the
[ArcGIS guide](../../arcgis/README.md). QGIS users can import
[qgis/Rang.xml](../../qgis/Rang.xml) for the ramps or
[qgis/Termeh.gpl](../../qgis/Termeh.gpl) for swatches, see the
[QGIS guide](../../qgis/README.md). HEC-RAS surface fills are in
[hecras/Termeh.rasmap.xml](../../hecras/Termeh.rasmap.xml), see the
[HEC-RAS guide](../../hecras/README.md).
