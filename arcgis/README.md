# Rang in ArcGIS Pro

One file, written by `tools/build.py`:

| file | contents |
|---|---|
| `Rang.stylx` | every palette as an ArcGIS Pro style, colors plus smooth and discrete color schemes |

ArcGIS Pro stores styles as `.stylx` database files. Import this file once to
add the collection to a project:

1. Open the **Catalog** pane and find **Styles**.
2. Right click **Styles**, then **Add**, then **Add Style** (on some versions
   this sits under **Insert**, **Styles**).
3. Pick `Rang.stylx`.

<img src="add-style.jpg" width="250" alt="Adding a style through the Catalog pane">

Every palette then shows up in two places:

- **Color scheme menus** for stretched rasters, unclassed and graduated
  colors, unique values and charts. The plain name, such as
  "Rang - Termeh", is the smooth ramp. The name marked discrete holds the
  exact palette steps for classified data.
- **Color pickers**, under the Rang category, with one swatch per palette
  color, named with its hex code.

Because a color scheme lives in the symbology rather than the dataset, this
works with any raster type, floating point included. For a depth or water
surface elevation grid, open **Symbology**, choose **Stretch** or
**Classify**, and pick the Rang scheme from the dropdown.

## Suggested pairings

Use a smooth scheme for depth, water surface elevation, rainfall and other
continuous data. Termeh was made with those maps in mind. Use a discrete
scheme for categories or classes that need fixed colors.
