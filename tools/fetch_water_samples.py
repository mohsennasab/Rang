"""Build the water surface elevation and stream network grids for sample plots.

Two real datasets, both public, both centered on Ithaca, New York:

  data/wse.png, wse.json          water surface elevation for the 100 year
                                  high flood profile from the USGS flood
                                  inundation mapping study of Cayuga Inlet,
                                  Sixmile, Cascadilla and Fall Creeks
                                  (ScienceBase item 5b757eb6e4b0f5d5787fe461)
  data/streams.json               Fall Creek's upstream flowline network and
                                  basin boundary from the USGS NLDI service,
                                  with NHDPlusV2 attributes from USGS Fabric

The files ship with the repo, so contributors normally never run this. It
needs rasterio on top of the regular tool requirements.

  pip install rasterio
  python tools/fetch_water_samples.py
"""
import json
import urllib.request

import numpy as np
from PIL import Image

from colorlib import REPO_ROOT

ITEM = "5b757eb6e4b0f5d5787fe461"
PROFILE = "WSE12_100yrHigh"
GAGE = "USGS-04234000"  # Fall Creek near Ithaca NY
NLDI = "https://api.water.usgs.gov/nldi/linked-data/nwissite"
FABRIC = ("https://api.water.usgs.gov/fabric/pygeoapi/collections/"
          "nhdflowline_network/items")
SCALE = 20  # stored value = (elevation ft - vmin) x SCALE + 1, 0 marks dry cells


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Rang palette tools",
                                               "Accept": "*/*"})
    with urllib.request.urlopen(req) as r:
        data = r.read()
    return data if binary else json.loads(data)


def fetch_wse():
    import rasterio

    item = get(f"https://www.sciencebase.gov/catalog/item/{ITEM}?format=json")
    tif_url = None
    for facet in item.get("facets", []):
        if facet.get("name") == PROFILE:
            for f in facet.get("files", []):
                if f["name"].endswith(".tif"):
                    tif_url = f.get("url") or f.get("downloadUri")
    if tif_url is None:
        raise SystemExit(f"could not find {PROFILE}.tif on ScienceBase item {ITEM}")

    tif = REPO_ROOT / "cache" / f"{PROFILE}.tif"
    tif.parent.mkdir(exist_ok=True)
    if not tif.exists():
        print(f"downloading {PROFILE}.tif")
        tif.write_bytes(get(tif_url, binary=True))

    with rasterio.open(tif) as src:
        wse = src.read(1).astype(float)
        if src.nodata is not None:
            wse[wse == src.nodata] = np.nan
        units = (src.crs.linear_units or "feet") if src.crs else "feet"
    step = max(1, wse.shape[1] // 1400)
    wse = wse[::step, ::step]
    vmin = float(np.nanmin(wse))
    print(f"grid {wse.shape[1]}x{wse.shape[0]}, elevation {vmin:.0f} "
          f"to {np.nanmax(wse):.0f} ({units})")

    out = REPO_ROOT / "data"
    out.mkdir(exist_ok=True)
    stored = np.where(np.isfinite(wse), np.round((wse - vmin) * SCALE) + 1, 0)
    Image.fromarray(np.clip(stored, 0, 65535).astype(np.uint16)).save(out / "wse.png")
    (out / "wse.json").write_text(json.dumps({
        "vmin_ft": vmin,
        "scale": SCALE,
        "encoding": "value = (elevation ft - vmin_ft) x scale + 1, 0 marks dry cells",
        "profile": "100 year high flood profile",
        "place": "Ithaca, New York",
        "source": "USGS, Water surface elevation (NAVD 88) for flood-inundation "
                  "maps for Cayuga Inlet, Sixmile Creek, Cascadilla Creek, and "
                  "Fall Creek at Ithaca, New York",
        "url": f"https://www.sciencebase.gov/catalog/item/{ITEM}",
    }, indent=2), encoding="utf-8")
    print(f"wrote {out / 'wse.png'} and wse.json")


def rounded(coords):
    return [[round(x, 4), round(y, 4)] for x, y in coords]


def fetch_streams():
    print("fetching NLDI basin and flowlines")
    basin = get(f"{NLDI}/{GAGE}/basin?simplified=true")
    tribs = get(f"{NLDI}/{GAGE}/navigation/UT/flowlines?distance=9999")
    main = get(f"{NLDI}/{GAGE}/navigation/UM/flowlines?distance=9999")

    ring = basin["features"][0]["geometry"]["coordinates"]
    ring = ring[0] if basin["features"][0]["geometry"]["type"] == "Polygon" else ring[0][0]
    xs, ys = zip(*ring)
    bbox = ",".join(str(round(value, 5)) for value in
                    (min(xs), min(ys), max(xs), max(ys)))
    fabric = get(f"{FABRIC}?bbox={bbox}&limit=1000&f=json")
    attributes = {
        int(feature["properties"]["comid"]): feature["properties"]
        for feature in fabric["features"]
    }
    main_ids = {
        int(feature["properties"]["nhdplus_comid"])
        for feature in main["features"]
    }

    flowlines = []
    missing = []
    for feature in tribs["features"]:
        comid = int(feature["properties"]["nhdplus_comid"])
        props = attributes.get(comid)
        if props is None:
            missing.append(comid)
            continue
        geometry = feature["geometry"]
        parts = ([geometry["coordinates"]] if geometry["type"] == "LineString"
                 else geometry["coordinates"])
        for part in parts:
            flowlines.append({
                "coordinates": rounded(part),
                "comid": comid,
                "stream_order": int(props["streamorde"]),
                "drainage_sq_km": round(float(props["totdasqkm"]), 3),
                "name": (props.get("gnis_name") or "").strip(),
                "main_stem": comid in main_ids,
            })
    if missing:
        raise RuntimeError(f"USGS Fabric did not return {len(missing)} flowlines")

    out = REPO_ROOT / "data"
    (out / "streams.json").write_text(json.dumps({
        "basin": rounded(ring),
        "flowlines": flowlines,
        "place": "Fall Creek upstream of Ithaca, New York",
        "gage": GAGE,
        "source": "USGS Network Linked Data Index and USGS Fabric",
        "url": "https://api.water.usgs.gov/nldi/",
        "attributes_url": "https://api.water.usgs.gov/docs/fabric-pygeoapi/",
    }, separators=(",", ":")), encoding="utf-8")
    n = sum(len(line["coordinates"]) for line in flowlines)
    print(f"wrote {out / 'streams.json'} "
          f"({len(flowlines)} flowlines, {n} vertices)")


def main():
    fetch_wse()
    fetch_streams()


if __name__ == "__main__":
    main()
