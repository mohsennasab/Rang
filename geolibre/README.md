# Rang for GeoLibre

GeoLibre can use Rang colors in raster ramps, vector class styles, legends and
colorbars. The quickest route is to copy a prepared list from
[Rang.txt](Rang.txt). [Rang.json](Rang.json) provides the same values in a
machine-readable form for Python and project tooling.

The files contain three kinds of color list:

- `raster anchors` preserve the full palette ramp for continuous rasters
- `graduated n` gives exactly `n` ordered colors for numeric vector classes
- `categorical n` gives `n` well separated colors for distinct classes

Both files are generated from `palettes/*.json` by `tools/build.py`. Do not
edit them by hand.

## Raster layers in the GeoLibre app

1. Add a single-band GeoTIFF or Cloud Optimized GeoTIFF.
2. Open the layer's Style panel and find Raster symbology.
3. Choose `Custom` in the color ramp menu.
4. Copy the palette's `raster anchors` line from [Rang.txt](Rang.txt) and paste
   the hex colors into Custom colors.
5. Click outside the field to apply the ramp.
6. Turn on Reverse ramp when high values should use the first color.
7. Turn on Classify when discrete raster classes are preferable to a smooth
   ramp, then select the class count and method.

GeoLibre accepts colors separated by commas, spaces or new lines. At least two
valid hex colors are required. The app interpolates between the supplied
anchors for a continuous raster.

To add a matching scale, open Controls, add a Colorbar, choose its custom
color mode and paste the same anchors. Set the minimum, maximum, label and
units to match the raster.

## Vector layers in the GeoLibre app

GeoLibre generates vector stops from one of its built-in ramp names. Its
current vector ramp menu does not accept an arbitrary pasted ramp. Rang colors
can still be assigned to the generated stops:

1. Open the vector layer's Style panel.
2. Choose Graduated for a numeric attribute or Categorized for distinct
   values.
3. Select the attribute, class count and classification method.
4. Copy the matching `graduated n` or `categorical n` line from
   [Rang.txt](Rang.txt).
5. Replace the generated stop colors in order, using the color control beside
   each stop.
6. Apply the style and add a Legend from the Controls menu if needed.

Use the graduated list for quantities such as depth, elevation or rainfall.
Use the categorical list for land cover, administrative type or other nominal
groups. Categorical lists stop at the number of distinct colors held by the
palette.

GeoLibre's Style Manager can save the finished layer style for reuse. Its ramp
preset format currently records a built-in ramp name rather than an arbitrary
color list, so [Rang.json](Rang.json) is a color bundle and not a native Style
Manager import file.

## GeoLibre in Jupyter and Colab

Install both packages in a notebook:

```python
%pip install -q geolibre rang
```

Rang colors can be passed directly to GeoLibre legends and colorbars:

```python
from geolibre import Map
import rang

m = Map()

depth_colors = rang.rang("Termeh", 100, "continuous")
m.add_colorbar(
    colors=depth_colors,
    vmin=0,
    vmax=8,
    label="Water depth",
    units="m",
)

land_use = ["Water", "Forest", "Cropland", "Urban"]
land_colors = rang.rang("Golestan", len(land_use))
m.add_legend(
    title="Land use",
    labels=land_use,
    colors=land_colors,
)

m
```

For a vector layer, pass explicit stops through `add_geojson`. Replace
`geojson_data`, `land_use` and the labels with fields and values from the
dataset:

```python
stops = [
    {"value": label, "label": label, "color": color}
    for label, color in zip(land_use, land_colors)
]

m.add_geojson(
    geojson_data,
    name="Land use",
    vectorStyleMode="categorized",
    vectorStyleProperty="land_use",
    vectorStyleClassCount=len(stops),
    vectorStyleStops=stops,
)
```

The current `add_cog()` Python method accepts a named GeoLibre colormap. To use
a Rang ramp on that raster, add the COG in Python, open its Style panel in the
rendered map and follow the raster steps above. `add_colorbar(colors=...)`
already accepts Rang colors directly.

## Load the generated bundle without installing Rang

Notebook code can read the public JSON file directly:

```python
import json
from urllib.request import urlopen

url = "https://raw.githubusercontent.com/mohsennasab/Rang/main/geolibre/Rang.json"
with urlopen(url) as response:
    palettes = json.load(response)["palettes"]

termeh_anchors = palettes["Termeh"]["raster_anchors"]
golestan_five = palettes["Golestan"]["categorical"]["5"]
```

## GeoLibre references

- [Styling layers](https://geolibre.app/user-guide/styling/)
- [Map controls](https://geolibre.app/user-guide/map-controls/)
- [GeoLibre for Python and Jupyter](https://geolibre.app/python/)
- [Python console](https://geolibre.app/user-guide/python-console/)
- [Project format](https://geolibre.app/project-format/)
