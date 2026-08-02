"""Render the sample plot page for a palette.

Draws the same six panels for every palette so readers can compare them on a
level field: violin plot, grouped bars, labeled scatter, stacked area, a real
daily rainfall field from NOAA AORC on the continuous ramp, and a CONUS
elevation map. Writes docs/<name>/samples.png.

The rainfall and elevation panels use the small real grids committed in
data/, built by fetch_aorc_precip.py and fetch_conus_dem.py. Pass --dem to
swap your own single band GeoTIFF into the elevation panel (needs rasterio).
Missing grids fall back to synthetic fields so the script always runs.

  python tools/make_samples.py kashan
  python tools/make_samples.py kashan --dem C:/data/my_dem.tif
"""
import argparse
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from PIL import Image

from colorlib import REPO_ROOT, discrete_subset, load_palette

SEED = 42


def palette_cmap(pal):
    return LinearSegmentedColormap.from_list(pal["name"], pal["colors"])


def pick(pal, n):
    if "order" in pal:
        return discrete_subset(pal["colors"], pal["order"], n)
    return pal["colors"][:n]


# ------------------------------------------------------------------ the panels

def panel_violin(ax, pal, rng):
    colors = pick(pal, 5)
    data = [rng.normal(loc, scale, 400) for loc, scale in
            [(0, 1.0), (1.2, 0.8), (0.4, 1.4), (2.2, 0.7), (1.6, 1.1)]]
    parts = ax.violinplot(data, showmedians=True)
    for body, c in zip(parts["bodies"], colors):
        body.set_facecolor(c)
        body.set_edgecolor("#333333")
        body.set_alpha(0.9)
    for key in ("cmedians", "cmins", "cmaxes", "cbars"):
        parts[key].set_color("#333333")
        parts[key].set_linewidth(1)
    ax.set_xticks(range(1, 6), [f"Site {i}" for i in "ABCDE"])
    ax.set_title("Violin plot")


def panel_bars(ax, pal, rng):
    colors = pick(pal, 3)
    groups = ["Winter", "Spring", "Summer", "Fall"]
    x = np.arange(len(groups))
    for i, (label, c) in enumerate(zip(["Basin 1", "Basin 2", "Basin 3"], colors)):
        ax.bar(x + (i - 1) * 0.26, rng.uniform(20, 90, len(groups)),
               width=0.24, color=c, label=label)
    ax.set_xticks(x, groups)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Grouped bars")


def panel_scatter(ax, pal, rng):
    colors = pick(pal, 6)
    centers = rng.uniform(-4, 4, (6, 2))
    for c, center in zip(colors, centers):
        pts = center + rng.normal(0, 0.7, (60, 2))
        ax.scatter(pts[:, 0], pts[:, 1], s=14, color=c, edgecolors="none")
    ax.set_title("Scatter, six classes")


def panel_area(ax, pal, rng):
    colors = pick(pal, 5)
    x = np.arange(120)
    layers = np.abs(np.cumsum(rng.normal(0, 1, (5, 120)), axis=1)) + 4
    ax.stackplot(x, layers, colors=colors, edgecolor="white", linewidth=0.4)
    ax.set_xlim(0, 119)
    ax.set_title("Stacked area")


def load_aorc_precip():
    png = REPO_ROOT / "data" / "aorc_precip.png"
    meta = REPO_ROOT / "data" / "aorc_precip.json"
    if not (png.exists() and meta.exists()):
        return None, None
    info = json.loads(meta.read_text(encoding="utf-8"))
    raw = np.asarray(Image.open(png), float)
    precip = np.where(raw > 0, (raw - 1) / info["scale"], np.nan)
    return precip, info


def panel_precip(ax, fig, pal, rng):
    """Daily rainfall on the continuous ramp, real AORC data when available."""
    cmap = palette_cmap(pal)
    precip, info = load_aorc_precip()
    if precip is None:
        x, y = np.meshgrid(np.linspace(-3, 3, 240), np.linspace(-3, 3, 240))
        z = np.exp(-((x - 1) ** 2 + (y - 1) ** 2)) * 60 + \
            np.exp(-((x + 1.5) ** 2 + (y + 0.8) ** 2) / 2) * 25
        im = ax.imshow(z, cmap=cmap, extent=(-3, 3, -3, 3), origin="lower")
        fig.colorbar(im, ax=ax, shrink=0.85, label="mm")
        ax.set_title("Precipitation, synthetic")
        return
    step = max(1, precip.shape[1] // 900)
    z = precip[::step, ::step]
    hi = np.nanpercentile(z, 99.5)
    cmap = cmap.copy()
    cmap.set_bad("#ebebeb")
    im = ax.imshow(np.ma.masked_invalid(z), cmap=cmap, vmin=0, vmax=hi)
    fig.colorbar(im, ax=ax, shrink=0.85, label="mm per day")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f'Precipitation, AORC roughly 1 km, {info["date"]}')


# ----------------------------------------------------------------- elevation

def hillshade(z, azimuth=315, altitude=45):
    gy, gx = np.gradient(z)
    slope = np.pi / 2 - np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    az = np.radians(360 - azimuth + 90)
    alt = np.radians(altitude)
    shade = (np.sin(alt) * np.sin(slope)
             + np.cos(alt) * np.cos(slope) * np.cos(az - aspect))
    return np.clip(shade, 0, 1)


def load_conus_dem():
    png = REPO_ROOT / "data" / "conus_dem.png"
    meta = REPO_ROOT / "data" / "conus_dem.json"
    if not (png.exists() and meta.exists()):
        return None, None
    info = json.loads(meta.read_text(encoding="utf-8"))
    dem = np.asarray(Image.open(png), float) - info["offset_m"]
    return dem, "Elevation, CONUS"


def load_geotiff(path):
    import rasterio
    with rasterio.open(path) as src:
        dem = src.read(1).astype(float)
        if src.nodata is not None:
            dem[dem == src.nodata] = np.nan
    return dem, f"Elevation, {path}"


def synthetic_dem(size=400, seed=SEED):
    rng = np.random.default_rng(seed)
    spec = np.fft.fft2(rng.normal(size=(size, size)))
    kx = np.fft.fftfreq(size)[:, None]
    ky = np.fft.fftfreq(size)[None, :]
    k = np.hypot(kx, ky)
    k[0, 0] = 1
    dem = np.real(np.fft.ifft2(spec / k ** 1.8))
    return dem, "Elevation, synthetic terrain"


def panel_dem(ax, pal, dem_path=None):
    dem, title = (None, None)
    if dem_path:
        dem, title = load_geotiff(dem_path)
    if dem is None:
        dem, title = load_conus_dem()
    if dem is None:
        dem, title = synthetic_dem()

    # keep the hillshade math on a modest grid
    step = max(1, dem.shape[1] // 900)
    dem = dem[::step, ::step]
    land = dem > 0 if np.nanmin(dem) <= 0 else np.isfinite(dem)
    z = np.where(land, dem, np.nan)

    lo, hi = np.nanpercentile(z, [1, 99])
    norm = np.clip((z - lo) / (hi - lo), 0, 1)
    cmap = palette_cmap(pal)
    rgba = cmap(np.nan_to_num(norm))
    shade = hillshade(np.nan_to_num(dem, nan=0.0))[..., None]
    rgb = rgba[..., :3] * (0.55 + 0.45 * shade)
    rgb[~land] = 0.92  # water and nodata in light gray
    ax.imshow(rgb, aspect="auto")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title)


# ------------------------------------------------- water palettes, two panels
# Palettes with "samples": "water" in their json are made for water surface
# elevation and depth rasters, so their page shows exactly that: a real USGS
# flood profile and a real stream network instead of the six generic panels.

def panel_wse(ax, fig, pal):
    png = REPO_ROOT / "data" / "wse.png"
    meta = REPO_ROOT / "data" / "wse.json"
    if not (png.exists() and meta.exists()):
        raise SystemExit("data/wse.png is missing, run tools/fetch_water_samples.py")
    info = json.loads(meta.read_text(encoding="utf-8"))
    raw = np.asarray(Image.open(png), float)
    wse = np.where(raw > 0, (raw - 1) / info["scale"] + info["vmin_ft"], np.nan)

    # crop to the wetted extent, with a little margin
    rows = np.where(np.isfinite(wse).any(axis=1))[0]
    cols = np.where(np.isfinite(wse).any(axis=0))[0]
    pad = 20
    wse = wse[max(rows[0] - pad, 0):rows[-1] + pad,
              max(cols[0] - pad, 0):cols[-1] + pad]

    # percentile stretch, most of a flood profile sits near the low end
    lo, hi = np.nanpercentile(wse, [1, 99])
    cmap = palette_cmap(pal).copy()
    cmap.set_bad((0, 0, 0, 0))
    ax.set_facecolor("white")
    im = ax.imshow(np.ma.masked_invalid(wse), cmap=cmap, vmin=lo, vmax=hi)
    wet = np.isfinite(wse)
    ax.contour(wet.astype(float), levels=[0.5], colors="#aebbc0",
               linewidths=0.45, alpha=0.7)
    fig.colorbar(im, ax=ax, shrink=0.82, pad=0.025,
                 label="ft NAVD 88", extend="max")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Water surface elevation\n"
                 f'{info["profile"].capitalize()}, {info["place"]}', pad=12)
    for spine in ax.spines.values():
        spine.set_visible(False)


def stream_linewidth(order):
    """Return a readable line width for an NHDPlusV2 stream order."""
    return 0.5 + 0.11 * max(order - 1, 0) ** 1.8


def panel_streams(ax, pal):
    meta = REPO_ROOT / "data" / "streams.json"
    if not meta.exists():
        raise SystemExit("data/streams.json is missing, run tools/fetch_water_samples.py")
    info = json.loads(meta.read_text(encoding="utf-8"))
    flowlines = info["flowlines"]
    basin = np.asarray(info["basin"])
    ax.set_facecolor("white")
    ax.fill(basin[:, 0], basin[:, 1], facecolor="none",
            edgecolor="#9daeb4", linewidth=1.1, zorder=1)

    orders = sorted({line["stream_order"] for line in flowlines})
    lo, hi = min(orders), max(orders)
    cmap = palette_cmap(pal)

    def order_color(order):
        fraction = 1 if hi == lo else (order - lo) / (hi - lo)
        return cmap(0.28 + 0.72 * fraction)

    for line in sorted(flowlines, key=lambda item: item["stream_order"]):
        xy = np.asarray(line["coordinates"])
        order = line["stream_order"]
        ax.plot(xy[:, 0], xy[:, 1], color=order_color(order),
                linewidth=stream_linewidth(order), solid_capstyle="round",
                zorder=2 + order)

    handles = [
        Line2D([0], [0], color=order_color(order),
               linewidth=stream_linewidth(order), label=f"Order {order}")
        for order in orders
    ]
    handles.append(Line2D([0], [0], color="#9daeb4", linewidth=1.1,
                          label="Watershed boundary"))
    ax.legend(handles=handles, title="NHDPlusV2 stream order", loc="upper left",
              frameon=False, fontsize=8, title_fontsize=8, ncol=2)
    mid_lat = float(np.mean(basin[:, 1]))
    ax.set_aspect(1 / np.cos(np.radians(mid_lat)))
    ax.margins(0.035)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Stream network by stream order\n"
                 f'{info["place"]}', pad=12)
    for spine in ax.spines.values():
        spine.set_visible(False)


def water_page(pal):
    fig, axes = plt.subplots(1, 2, figsize=(15, 8), dpi=140)
    fig.patch.set_facecolor("white")
    panel_wse(axes[0], fig, pal)
    panel_streams(axes[1], pal)
    fig.suptitle(f'{pal["name"]}, water mapping examples',
                 fontsize=18, fontfamily="serif")
    fig.tight_layout(rect=(0.025, 0.035, 0.975, 0.94), w_pad=3.2)
    return fig


# ------------------------------------------------------------------- assemble

def standard_page(pal, rng, dem_path):
    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5), dpi=140)
    fig.patch.set_facecolor("white")

    panel_violin(axes[0, 0], pal, rng)
    panel_bars(axes[0, 1], pal, rng)
    panel_scatter(axes[0, 2], pal, rng)
    panel_area(axes[1, 0], pal, rng)
    panel_precip(axes[1, 1], fig, pal, rng)
    panel_dem(axes[1, 2], pal, dem_path)

    for ax in axes.flat:
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle(f'{pal["name"]}, sample plots', fontsize=16, fontfamily="serif")
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    return fig


def main(name, dem_path=None):
    pal = load_palette(name)
    rng = np.random.default_rng(SEED)

    if pal.get("samples") == "water":
        fig = water_page(pal)
    else:
        fig = standard_page(pal, rng, dem_path)

    out_dir = REPO_ROOT / "docs" / pal["name"].lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "samples.png", metadata={"Software": "Rang"})
    plt.close(fig)
    print(f"wrote {out_dir / 'samples.png'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("palette", help="name of a file in palettes/")
    ap.add_argument("--dem", help="optional single band GeoTIFF for the "
                                  "elevation panel (needs rasterio)")
    args = ap.parse_args()
    main(args.palette, args.dem)
