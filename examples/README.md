# Rang examples

These notebooks install Rang directly from GitHub. The short Python and R
examples use the Palmer Penguins dataset. The hydrologic mapping notebook reads
elevation, river, temperature and precipitation data from public sources, then
maps the reduced flood-depth raster stored with Rang.

These examples show how to use finished palettes. To create and document a new
palette, use the numbered [palette-making notebooks](../tools/README.md).

[![Open Python notebook in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/examples/rang_python_colab.ipynb)

[![Open R notebook in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/examples/rang_r_colab.ipynb)

[![Open hydrologic maps notebook in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/examples/rang_hydrology_maps_colab.ipynb)

## What the notebooks cover

- installing the current Rang package from GitHub
- viewing every available palette
- selecting well separated colors for categories
- building a continuous color map for numeric data
- using the same online dataset in Python and R
- reading the artwork source metadata stored with a palette
- mapping the transboundary Mississippi basin topography at 1000 dpi
- drawing the national river network within the CONUS boundary at 1000 dpi
- showing Hurricane Helene precipitation in a six-panel UTC sequence
- mapping monthly U.S. temperature and stretching precipitation to reveal lower totals
- mapping flood depth over a clean white background

The Python notebook uses pandas and matplotlib. The R notebook uses ggplot2.
The hydrologic notebook also uses Microsoft Planetary Computer, NOAA,
HydroSHEDS and U.S. Census Bureau data. Google Colab installs anything missing
in the first setup cell.

The example dataset is the
[Palmer Penguins dataset](https://allisonhorst.github.io/palmerpenguins/),
originally collected by Dr. Kristen Gorman and the Palmer Station Long Term
Ecological Research program. The notebooks download it at runtime and do not
redistribute it in this repository.

The flood-depth example uses a reduced copy of the Whiskey Chitto
`BLE_DEP01PCT` raster. Its [metadata](../data/whiskey_chitto_depth_1pct.json)
records the source layer, coordinate system, units and resampling. The file is
included for visualization and must not be used for engineering decisions.
