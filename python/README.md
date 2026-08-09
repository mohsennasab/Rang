# rang for Python

Color palettes from Persian art. Part of the [Rang](https://github.com/mohsennasab/Rang)
project, which also packages the palettes for R, ArcGIS Pro, QGIS, GeoLibre
and HEC-RAS.

```
pip install rang
```

The package has no required dependencies. The matplotlib helpers need
matplotlib, which you can pull in at the same time:

```
pip install "rang[plots]"
```

## Colors

```python
import rang

rang.list_palettes()                      # available names
rang.rang("Kashan")                       # all nine colors, ramp order
rang.rang("Kashan", 4)                    # four well separated colors
rang.rang("Kashan", 30, "continuous")     # interpolated ramp
rang.source("Kashan")                     # the artwork behind the palette
```

Discrete requests use the stored separation order. Continuous requests
interpolate through the source ramp in sRGB.

## matplotlib

```python
rang.cmap("Termeh")           # smooth colormap
rang.cmap("Termeh", 6)        # six fixed steps, for classified data
rang.cmap("Termeh", direction=-1)   # reversed

rang.set_palette("Golestan")  # default colors for lines and bars
```

`register()` adds every palette to the matplotlib registry under a `rang:`
name. Do this once and any library that accepts a colormap name will take a
Rang palette, including xarray, geopandas, rioxarray and seaborn.

```python
rang.register()

plt.imshow(data, cmap="rang:Iwan")
plt.imshow(data, cmap="rang:Iwan_r")      # every palette also registers reversed
```

Calling `register()` again is safe and quiet.

## Picking a palette

Termeh, Iwan, Khatam and Rostan run steadily from light to dark or dark to
light, which is what depth, elevation and rainfall maps need. Kashan,
Golestan and Mina move from a warm side through a light center to a cool
side. Nasir, Shahnameh and Gilas jump around in brightness, so they suit
categories rather than measured quantities.

Each palette page in the repository shows sample plots and the color vision
checks.

## License

The package software is available under the MIT License. To the extent that
copyright or database rights apply, the Rang palette definitions are
dedicated to the public domain under CC0 1.0 Universal. Photographs and
third-party data are covered by the notices in the main repository.
