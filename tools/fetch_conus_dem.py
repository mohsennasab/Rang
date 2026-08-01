"""Build the small CONUS elevation grid used by the sample plots.

Downloads a handful of public terrain tiles (terrarium encoding) from the AWS
Open Data elevation tiles bucket at zoom 5, mosaics them, crops to the lower
48, and stores the result as a 16 bit grayscale PNG in data/. The file is a
few hundred kilobytes and is committed to the repo, so contributors normally
never need to run this. It exists so anyone can rebuild the grid from source.

Elevation sources behind the tiles include SRTM, GMTED2010 and ETOPO1,
composited by the former Mapzen project and hosted on AWS Open Data.

  python tools/fetch_conus_dem.py
"""
import io
import json
import math
import urllib.request

import numpy as np
from PIL import Image

from colorlib import REPO_ROOT

ZOOM = 5
TILE = 256
BBOX = (-125.0, 24.0, -66.5, 50.0)  # lon min, lat min, lon max, lat max
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
OFFSET = 1000  # stored value = elevation in meters + OFFSET, keeps uint16 positive


def to_pixels(lon, lat, z):
    """Web mercator global pixel coordinates at zoom z."""
    scale = TILE * 2 ** z
    x = (lon + 180) / 360 * scale
    lat_r = math.radians(lat)
    y = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * scale
    return x, y


def fetch_tile(z, x, y):
    req = urllib.request.Request(URL.format(z=z, x=x, y=y),
                                 headers={"User-Agent": "Rang palette tools"})
    with urllib.request.urlopen(req) as r:
        rgb = np.asarray(Image.open(io.BytesIO(r.read())).convert("RGB"), float)
    return rgb[..., 0] * 256 + rgb[..., 1] + rgb[..., 2] / 256 - 32768


def main():
    x0, y1 = to_pixels(BBOX[0], BBOX[1], ZOOM)
    x1, y0 = to_pixels(BBOX[2], BBOX[3], ZOOM)
    tx0, tx1 = int(x0 // TILE), int(x1 // TILE)
    ty0, ty1 = int(y0 // TILE), int(y1 // TILE)

    mosaic = np.zeros(((ty1 - ty0 + 1) * TILE, (tx1 - tx0 + 1) * TILE))
    n = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
    print(f"fetching {n} tiles at zoom {ZOOM}")
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            tile = fetch_tile(ZOOM, tx, ty)
            mosaic[(ty - ty0) * TILE:(ty - ty0 + 1) * TILE,
                   (tx - tx0) * TILE:(tx - tx0 + 1) * TILE] = tile

    # crop the mosaic to the exact bounding box
    px0, px1 = int(x0 - tx0 * TILE), int(x1 - tx0 * TILE)
    py0, py1 = int(y0 - ty0 * TILE), int(y1 - ty0 * TILE)
    dem = mosaic[py0:py1, px0:px1]
    print(f"grid {dem.shape[1]}x{dem.shape[0]}, "
          f"elevation {dem.min():.0f} to {dem.max():.0f} m")

    out = REPO_ROOT / "data"
    out.mkdir(exist_ok=True)
    stored = np.clip(np.round(dem + OFFSET), 0, 65535).astype(np.uint16)
    Image.fromarray(stored).save(out / "conus_dem.png")
    (out / "conus_dem.json").write_text(json.dumps({
        "offset_m": OFFSET,
        "bbox": {"lon_min": BBOX[0], "lat_min": BBOX[1],
                 "lon_max": BBOX[2], "lat_max": BBOX[3]},
        "projection": "web mercator, cropped at zoom 5",
        "source": "AWS Open Data terrain tiles (terrarium), elevation from "
                  "SRTM, GMTED2010, ETOPO1 and other public datasets",
        "url": "https://registry.opendata.aws/terrain-tiles/",
    }, indent=2), encoding="utf-8")
    print(f"wrote {out / 'conus_dem.png'} and conus_dem.json")


if __name__ == "__main__":
    main()
