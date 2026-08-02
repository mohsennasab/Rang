"""Build the precipitation grid used by the sample plots.

Pulls one day of NOAA AORC precipitation, on a roughly 1 km grid, from the
AWS Open Data bucket, sums the hourly fields, and stores the result as a
16 bit grayscale PNG in data/. The default day is 27 August 2017, Hurricane
Harvey stalled over the Texas coast, which gives the sample pages a dramatic
and instantly readable rainfall field.

The grid ships with the repo, so contributors normally never run this. It
needs xarray, zarr and s3fs on top of the regular tool requirements:

  pip install xarray zarr s3fs
  python tools/fetch_aorc_precip.py

Data: NOAA Analysis of Record for Calibration (AORC) v1.1,
https://registry.opendata.aws/noaa-nws-aorc/
"""
import json

import numpy as np
from PIL import Image

from colorlib import REPO_ROOT

DATE = "2017-08-27"
BBOX = (-100.5, 25.5, -88.5, 33.5)  # lon min, lat min, lon max, lat max
SCALE = 10  # stored value = precipitation in mm times SCALE


def main():
    import s3fs
    import xarray as xr

    year = DATE[:4]
    fs = s3fs.S3FileSystem(anon=True)
    store = s3fs.S3Map(f"noaa-nws-aorc-v1-1-1km/{year}.zarr", s3=fs)
    print(f"opening s3://noaa-nws-aorc-v1-1-1km/{year}.zarr")
    ds = xr.open_zarr(store, consolidated=True)

    da = ds["APCP_surface"].sel(time=DATE)
    lat = slice(BBOX[1], BBOX[3])
    if float(ds.latitude[0]) > float(ds.latitude[-1]):
        lat = slice(BBOX[3], BBOX[1])
    da = da.sel(latitude=lat, longitude=slice(BBOX[0], BBOX[2]))
    print(f"summing {da.sizes['time']} hourly fields over "
          f"{da.sizes['latitude']}x{da.sizes['longitude']} cells")
    total = da.sum("time", skipna=False).compute()

    arr = np.asarray(total.values, float)
    # orient north up for plain image display
    if float(total.latitude[0]) < float(total.latitude[-1]):
        arr = arr[::-1]
    print(f"daily total: max {np.nanmax(arr):.0f} mm, "
          f"mean {np.nanmean(arr):.1f} mm")

    out = REPO_ROOT / "data"
    out.mkdir(exist_ok=True)
    stored = np.where(np.isfinite(arr), np.round(arr * SCALE) + 1, 0)
    Image.fromarray(np.clip(stored, 0, 65535).astype(np.uint16)).save(
        out / "aorc_precip.png")
    (out / "aorc_precip.json").write_text(json.dumps({
        "date": DATE,
        "scale": SCALE,
        "encoding": "value = mm x scale + 1, 0 marks missing cells",
        "bbox": {"lon_min": BBOX[0], "lat_min": BBOX[1],
                 "lon_max": BBOX[2], "lat_max": BBOX[3]},
        "event": "Hurricane Harvey daily rainfall over Texas and Louisiana",
        "source": "NOAA Analysis of Record for Calibration (AORC) v1.1, "
                  "roughly 1 km, hourly, via AWS Open Data",
        "url": "https://registry.opendata.aws/noaa-nws-aorc/",
    }, indent=2), encoding="utf-8")
    print(f"wrote {out / 'aorc_precip.png'} and aorc_precip.json")


if __name__ == "__main__":
    main()
