# Rang in ArcGIS Pro

Three kinds of files, all built with `tools/build.py`:

| file | contents |
|---|---|
| `Rang.stylx` | every palette as an ArcGIS Pro style, colors plus smooth and discrete color schemes |
| `<Name>.clr` | the discrete colors as an Esri colormap file, for integer rasters |
| `<Name>_continuous.clr` | a 256 step ramp as an Esri colormap file, for integer rasters |

## The style file, start here

`Rang.stylx` is the same kind of file ArcGIS Pro writes when you build a
style yourself, so one import covers everything:

1. Open the **Catalog** pane and find **Styles**.
2. Right click **Styles**, then **Add**, then **Add Style File** (on some
   versions this sits under **Insert**, **Styles**).
3. Pick `Rang.stylx`.

Every palette then shows up in two places:

- Each **color scheme dropdown**, symbology for stretched rasters, unclassed
  and graduated colors, bivariate schemes, charts. The plain name, such as
  "Rang - Termeh", is the smooth ramp. The name marked discrete holds the
  exact palette steps for classified data.
- Each **color picker**, under the Rang category, one swatch per palette
  color, named with its hex code.

This route works with any raster type, floating point included, because the
symbology does the coloring instead of the dataset. For a depth or water
surface elevation grid, open **Symbology**, choose **Stretch** or
**Classify**, and pick the Rang scheme from the dropdown.

## The .clr files, integer rasters only

A `.clr` file writes a colormap into the raster dataset itself through the
**Add Colormap** tool or the **Colormap** raster function. ArcGIS only
allows that for integer rasters, so on a floating point raster the tool
stops with error 000199, "Failed to add Colormap".

So use `.clr` when the raster is integer, classified land cover, flood
zones, a reclassified DEM. `<Name>.clr` fits class values 1, 2, 3 and so
on, `<Name>_continuous.clr` fits values 0 to 255. If you really want a
colormap burned into a float raster, convert it first with the **Int** tool
or a reclassify, though for display the style file above is the better
answer.

A `.clr` file is plain text, one `value red green blue` line per entry, so
you can also open it in a text editor and copy values out.

## Pick single colors

Any color picker in Pro accepts hex codes through **Color Properties**. With
the style imported you rarely need to, the swatches are already there.

## Suggested pairings

Sequential data such as depth, water surface elevation or rainfall reads
best with a smooth scheme, and Termeh was drawn for exactly that. Categorical
maps read best with a discrete scheme, which keeps the palette's pick order
so the first few classes stay far apart.
