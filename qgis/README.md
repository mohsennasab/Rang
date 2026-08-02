# Rang in QGIS

Two file types, both written by `tools/build.py`:

| file | contents |
|---|---|
| `Rang.xml` | every palette as a color ramp, smooth and discrete, in one QGIS style file |
| `<Name>.gpl` | one palette as swatches for the color picker |

## Import the ramps

1. Open **Settings**, then **Style Manager**.
2. Click **Import/Export**, then **Import Item(s)**.
3. Pick `Rang.xml`, select all, import.

Each palette shows up twice under the Rang tag. The plain name is the smooth
ramp for continuous data. The name marked discrete holds the palette's exact
colors as steps.

After importing, the ramps appear in every color ramp dropdown, including
singleband pseudocolor for rasters, graduated symbology for vectors, and the
mesh and point cloud renderers.

## Import the swatches

1. Open **Settings**, then **Options**, then the **Colors** tab.
2. Under the palette list click the plus dropdown, then **Import Palette**.
3. Pick a `.gpl` file.

The colors then sit in every QGIS color picker under the palette's name,
handy for styling single symbols and labels to match a map that uses the
ramp.

## Example, a DEM

Load a DEM, set the symbology to **Singleband pseudocolor**, and choose a
Rang ramp from the color ramp dropdown. For classified data such as land
cover, use the discrete variant so classes get the palette's exact colors in
their pick order.
