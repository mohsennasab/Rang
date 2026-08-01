# Rang in ArcGIS Pro

Each palette ships two Esri colormap files, built with `tools/build.py`:

| file | contents |
|---|---|
| `<Name>.clr` | the discrete colors, one line per class value |
| `<Name>_continuous.clr` | a 256 step ramp interpolated along the palette |

A `.clr` file is plain text, one `value red green blue` line per entry, so you
can also open it in a text editor and copy values out.

## Apply a colormap to a raster

Works for integer rasters such as classified land cover, flood zones or a
reclassified DEM.

1. In the Geoprocessing pane search for the **Add Colormap** tool.
2. Set your raster as input and pick the `.clr` file. Use `<Name>.clr` when
   your raster holds class values 1, 2, 3 and so on, or
   `<Name>_continuous.clr` when it holds values 0 to 255.
3. Symbolize the raster with the **Colormap** renderer.

The **Colormap** raster function does the same thing without writing to the
dataset.

## Build a color scheme for any layer

For graduated colors, unclassed colors or a stretch renderer you want a saved
color scheme:

1. Open the **Catalog** pane, right click **Styles**, then **New**, then
   **New Mobile Style**, and give it a name such as `Rang`.
2. Right click the new style, **Manage**, then **New**, then **Color Scheme**.
3. In the scheme editor add one stop per palette color. Each hex code goes in
   through the color picker, **Color Properties**, **HEX** field. Use the ramp
   order listed on the palette page in `docs/`.
4. For a discrete scheme set the stops to discrete, for a smooth ramp leave
   them continuous.

The scheme then shows up in every color scheme dropdown, including raster
stretch symbology and graduated colors for vector layers.

## Pick single colors

Any color picker in Pro accepts hex codes through **Color Properties**. The
hex codes for every palette are in the main README and on each palette page.

## Suggested pairings

Sequential data such as elevation or rainfall reads best with the continuous
ramp. Categorical maps read best with the discrete colors in their pick
order, which keeps the first few classes as far apart as possible. Palette
pages in `docs/` show both against real plot types.
