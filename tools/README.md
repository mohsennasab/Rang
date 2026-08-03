# Tools

Everything a contributor needs to go from a museum photo to a finished
palette. Install the dependencies first:

```
pip install -r tools/requirements.txt
```

| script | what it does |
|---|---|
| `extract_colors.py` | k-means clustering of a photo in CIELAB, whole image or region by region |
| `adjust_colors.py` | nudge a color in lightness, chroma or hue when the sampled value is not quite right |
| `check_palette.py` | separation scores under four vision types, suggested pick order, distance to the source photo |
| `make_preview.py` | the swatch strip and the artwork preview for one palette |
| `make_logo.py` | the reproducible transparent pixel logo used in the main README |
| `make_samples.py` | the standard sample plots, plus a two-map water layout for water palettes |
| `make_hecras_ramp.py` | individual and combined HEC-RAS color-ramp import files |
| `make_stylx.py` | the ArcGIS Pro style file with every palette's colors and schemes |
| `build.py` | runs everything above and regenerates the Python, R, ArcGIS, QGIS, GeoLibre and HEC-RAS files plus the README gallery |
| `fetch_conus_dem.py` | rebuilds the small CONUS elevation grid in `data/`, rarely needed |
| `fetch_aorc_precip.py` | rebuilds the AORC rainfall grid in `data/`, rarely needed, wants xarray, zarr and s3fs |
| `fetch_water_samples.py` | rebuilds the USGS water surface elevation and stream network files in `data/`, including NHDPlusV2 stream order, rarely needed, wants rasterio |
| `colorlib.py` | the shared color math, imported by the rest |

A typical session while developing a palette:

```
python tools/extract_colors.py --image <photo url> -k 8 --region 900,1400,1700,2200,medallion
python tools/check_palette.py --colors "#7f3020,#ab4a47,#c07049,#1a3b45" --image <photo url>
python tools/adjust_colors.py --colors "#8a9463" --edit "1:L+4,C-2"
```

Then write `palettes/<name>.json` and finish with:

```
python tools/build.py <name>
```

The build fills in the pick order if the json does not have one, regenerates
all package files, renders the three images and writes the palette page. See
[CONTRIBUTING.md](../CONTRIBUTING.md) for the full walkthrough.
