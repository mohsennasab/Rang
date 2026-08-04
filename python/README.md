# rang for Python

Color palettes from Persian art. Part of the [Rang](https://github.com/mohsennasab/Rang)
project, which also packages the palettes for R, ArcGIS Pro, QGIS, GeoLibre
and HEC-RAS.

```
pip install "git+https://github.com/mohsennasab/Rang.git#subdirectory=python"
```

```python
import rang

rang.list_palettes()                      # available names
rang.rang("Kashan")                       # all nine colors, ramp order
rang.rang("Kashan", 4)                    # four well separated colors
rang.rang("Kashan", 30, "continuous")     # interpolated ramp
rang.cmap("Kashan")                       # matplotlib colormap
rang.source("Kashan")                     # the artwork behind the palette
```

The package has no required dependencies. `cmap()` needs matplotlib, which you
can add with `pip install matplotlib`.
Discrete requests use the stored separation order. Continuous requests
interpolate through the source ramp in sRGB.

The package software is available under the MIT License. To the extent that
copyright or database rights apply, the Rang palette definitions are
dedicated to the public domain under CC0 1.0 Universal. Photographs and
third-party data are covered by the notices in the main repository.
