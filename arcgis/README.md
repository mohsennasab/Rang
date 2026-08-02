# Rang in ArcGIS Pro

One file, built with `tools/build.py`:

| file | contents |
|---|---|
| `Rang.stylx` | every palette as an ArcGIS Pro style, colors plus smooth and discrete color schemes |

A `.stylx` is the same kind of file ArcGIS Pro writes when you build a style
yourself, so one import covers the whole collection:

1. Open the **Catalog** pane and find **Styles**.
2. Right click **Styles**, then **Add**, then **Add Style File** (on some
   versions this sits under **Insert**, **Styles**).
3. Pick `Rang.stylx`.

Every palette then shows up in two places:

- Each **color scheme dropdown**, symbology for stretched rasters, unclassed
  and graduated colors, unique values, charts. The plain name, such as
  "Rang - Termeh", is the smooth ramp. The name marked discrete holds the
  exact palette steps for classified data.
- Each **color picker**, under the Rang category, one swatch per palette
  color, named with its hex code.

Because a color scheme lives in the symbology rather than the dataset, this
works with any raster type, floating point included. For a depth or water
surface elevation grid, open **Symbology**, choose **Stretch** or
**Classify**, and pick the Rang scheme from the dropdown.

## A note on colormap files

Earlier versions of this folder also shipped `.clr` colormap files for the
**Add Colormap** tool. That tool writes colors into the raster dataset
itself and only accepts integer rasters, which made it a trap for the
floating point depth and elevation grids these palettes are mostly used on.
The style file replaced them. If you ever need a dataset embedded colormap
for an integer raster, the hex codes on each palette page rebuild a `.clr`
in a minute, one `value red green blue` line per class.

## Suggested pairings

Sequential data such as depth, water surface elevation or rainfall reads
best with a smooth scheme, and Termeh was drawn for exactly that. Categorical
maps read best with a discrete scheme, which keeps the palette's pick order
so the first few classes stay far apart.
