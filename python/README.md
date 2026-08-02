# rang for Python

Color palettes from Persian art. Part of the [Rang](https://github.com/mohsennasab/Rang)
project, which also ships the palettes for R and ArcGIS Pro.

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
