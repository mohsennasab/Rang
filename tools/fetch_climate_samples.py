"""Build the climate data used by the departure sample page.

Pulls NOAA nClimDiv precipitation and temperature series and the U.S. Census
county and state boundaries, then stores four small products in data/:

  county_precip.png      2011 county precipitation classes on a CONUS Albers
                         grid, 8 bit grayscale, value = class + 1, 0 = outside
  climate_samples.json   the class table, state outlines, CONUS monthly
                         temperature departures, the yearly share of counties
                         in each class, and regional precipitation correlations

2011 pairs the Texas drought with the record wet Ohio Valley, so one map
reaches both ends of a diverging scale. Normal is the 1991 to 2020 mean.

The data ships with the repo, so contributors normally never run this. It
needs geopandas and rasterio on top of the regular tool requirements:

  pip install geopandas rasterio
  python tools/fetch_climate_samples.py

Connecticut uses its statewide value because the 2023 planning regions do not
match the county records. Other units with no record take the nearest county.

Data: NOAA nClimDiv, https://www.ncei.noaa.gov/pub/data/cirs/climdiv/
      U.S. Census cartographic boundaries,
      https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html
"""
import json
import pathlib
import re
import tempfile
import urllib.request

import geopandas as gpd
import numpy as np
import pandas as pd
from PIL import Image
from rasterio import features, transform

from colorlib import REPO_ROOT

CLIMDIV = "https://www.ncei.noaa.gov/monitoring-content/data/us/climdiv/monthly/current/"
CENSUS = "https://www2.census.gov/geo/tiger/GENZ2023/shp/"

YEAR = 2011
BASELINE = (1991, 2020)
LAST_YEAR = 2025
SHARE_START = 1996
WIDTH = 2000
EDGES = [0, 60, 75, 85, 95, 105, 120, 150, 999]
LABELS = ["under 60", "60 to 75", "75 to 85", "85 to 95", "95 to 105",
          "105 to 120", "120 to 150", "over 150"]

# nClimDiv numbers the lower 48 alphabetically. These are their FIPS codes.
STATE_FIPS = ("01 04 05 06 08 09 10 12 13 16 17 18 19 20 21 22 23 24 25 26 27 "
              "28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 44 45 46 47 48 49 "
              "50 51 53 54 55 56").split()
NOT_CONUS = ["02", "15", "60", "66", "69", "72", "78"]
CONUS_CODE = 110
CONNECTICUT = 6
REGIONS = {101: "Northeast", 102: "Upper Midwest", 103: "Ohio Valley",
           104: "Southeast", 105: "N. Rockies, Plains", 106: "South",
           107: "Southwest", 108: "Northwest", 109: "West"}


def download(url, path):
    request = urllib.request.Request(url, headers={"User-Agent": "Rang/1.0"})
    with urllib.request.urlopen(request, timeout=300) as response:
        path.write_bytes(response.read())
    return path


def climdiv_names():
    request = urllib.request.Request(CLIMDIV, headers={"User-Agent": "Rang/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        listing = response.read().decode("utf-8", "replace")
    names = sorted(set(re.findall(r"climdiv-[a-z]+-v[0-9.]+-[0-9]+", listing)))
    return {kind: [n for n in names if n.startswith(f"climdiv-{kind}-")][-1]
            for kind in ("pcpncy", "pcpnst", "tmpcst")}


def read_table(path):
    """Station ids and 12 monthly columns, with -9.99 and -99.9 as missing."""
    table = pd.read_csv(path, sep=r"\s+", header=None, dtype={0: str})
    months = table.iloc[:, 1:13].to_numpy(float)
    months[months < -9] = np.nan
    return table[0], months


def state_series(path, code, element):
    ids, months = read_table(path)
    keep = (ids.str[:3].astype(int).eq(code) & ids.str[4:6].eq(element)).values
    return pd.DataFrame(months[keep], index=ids[keep].str[6:10].astype(int).values)


def county_percent(path):
    """Annual precipitation as percent of normal, counties by years."""
    ids, months = read_table(path)
    table = pd.DataFrame({
        "state": ids.str[:2],
        "county": ids.str[2:5],
        "year": ids.str[7:11].astype(int),
        "total": np.where(np.isnan(months).any(axis=1), np.nan, months.sum(axis=1)),
    })
    lookup = {f"{i + 1:02d}": code for i, code in enumerate(STATE_FIPS)}
    table = table[table.state.isin(lookup) & (table.year <= LAST_YEAR)].copy()
    table["fips"] = table.state.map(lookup) + table.county
    wide = table.pivot(index="fips", columns="year", values="total")
    normal = wide[list(range(BASELINE[0], BASELINE[1] + 1))].mean(axis=1)
    return wide.div(normal, axis=0) * 100


def conus_layer(path):
    layer = gpd.read_file(f"zip://{path}")
    return layer[~layer.STATEFP.isin(NOT_CONUS)].to_crs(5070)


def county_classes(counties, percent, statewide):
    frame = counties[["GEOID", "STATEFP", "geometry"]].copy()
    frame["percent"] = frame.GEOID.map(percent[YEAR])
    connecticut = statewide.loc[YEAR] / statewide.loc[BASELINE[0]:BASELINE[1]].mean() * 100
    frame.loc[frame.STATEFP == "09", "percent"] = connecticut
    missing = frame.percent.isna()
    nearest = gpd.sjoin_nearest(frame[missing][["GEOID", "geometry"]],
                                frame[~missing][["percent", "geometry"]])
    means = nearest.groupby("GEOID").percent.mean()
    frame.loc[missing, "percent"] = frame.loc[missing, "GEOID"].map(means)
    frame["class"] = pd.cut(frame.percent, EDGES, labels=False)
    return frame


def rasterize(frame):
    left, bottom, right, top = frame.total_bounds
    pad = 20000
    left, bottom, right, top = left - pad, bottom - pad, right + pad, top + pad
    height = round(WIDTH * (top - bottom) / (right - left))
    grid = transform.from_bounds(left, bottom, right, top, WIDTH, height)
    shapes = ((geometry, int(value) + 1)
              for geometry, value in zip(frame.geometry, frame["class"]))
    classes = features.rasterize(shapes, out_shape=(height, WIDTH), transform=grid,
                                 fill=0, dtype="uint8")
    return classes, grid


def outlines(states, grid):
    """State boundaries as simplified polylines in raster pixels."""
    inverse = ~grid
    lines = []
    for geometry in states.boundary.simplify(2500):
        parts = geometry.geoms if hasattr(geometry, "geoms") else [geometry]
        for part in parts:
            if part.length < 20000:
                continue
            lines.append([[round(c, 1) for c in inverse * xy] for xy in part.coords])
    return lines


def main():
    names = climdiv_names()
    with tempfile.TemporaryDirectory() as temporary:
        folder = pathlib.Path(temporary)
        precip_county = download(CLIMDIV + names["pcpncy"], folder / "pcpncy.txt")
        precip_state = download(CLIMDIV + names["pcpnst"], folder / "pcpnst.txt")
        temperature = download(CLIMDIV + names["tmpcst"], folder / "tmpcst.txt")
        counties = conus_layer(download(CENSUS + "cb_2023_us_county_5m.zip",
                                        folder / "counties.zip"))
        states = conus_layer(download(CENSUS + "cb_2023_us_state_5m.zip",
                                      folder / "states.zip"))

        percent = county_percent(precip_county)
        statewide = state_series(precip_state, CONNECTICUT, "01").sum(axis=1)
        classes, grid = rasterize(county_classes(counties, percent, statewide))

        months = state_series(temperature, CONUS_CODE, "02").loc[:LAST_YEAR]
        departure = months - months.loc[BASELINE[0]:BASELINE[1]].mean()

        years = list(range(SHARE_START, LAST_YEAR + 1))
        share = [((percent[years] > low) & (percent[years] <= high)).sum()
                 / percent[years].notna().sum() * 100
                 for low, high in zip(EDGES[:-1], EDGES[1:])]

        anomalies = {}
        for code, name in REGIONS.items():
            series = state_series(precip_state, code, "01").loc[:LAST_YEAR]
            anomalies[name] = (series - series.mean()).stack()
        correlation = pd.DataFrame(anomalies).corr()

        info = {
            "year": YEAR,
            "baseline": list(BASELINE),
            "classes": {"edges": EDGES, "labels": LABELS},
            "states": outlines(states, grid),
            "temperature": {"first_year": int(departure.index[0]),
                            "last_year": int(departure.index[-1]),
                            "departure_f": np.round(departure.values, 2).tolist()},
            "class_share": {"years": years,
                            "percent": [np.round(row.values, 2).tolist() for row in share]},
            "correlation": {"regions": list(correlation.columns),
                            "r": np.round(correlation.values, 3).tolist()},
            "source": "NOAA nClimDiv and U.S. Census cartographic boundaries",
            "files": names,
            "url": "https://www.ncei.noaa.gov/pub/data/cirs/climdiv/",
        }

    data = REPO_ROOT / "data"
    Image.fromarray(classes).save(data / "county_precip.png", optimize=True)
    (data / "climate_samples.json").write_text(
        json.dumps(info, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {data / 'county_precip.png'} and {data / 'climate_samples.json'}")


if __name__ == "__main__":
    main()
