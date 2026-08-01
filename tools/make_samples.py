"""Render the sample plot page for a palette.

Draws the same six panels for every palette so readers can compare them on a
level field: violin plot, grouped bars, labeled scatter, stacked area, a
gridded field with the continuous ramp, and a CONUS elevation map. Writes
docs/<name>/samples.png.

The elevation panel uses the small real DEM in data/conus_dem.png that ships
with the repo. Pass --dem to swap in your own single band GeoTIFF instead
(needs rasterio). If neither is available the panel falls back to synthetic
terrain so the script always runs.

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


def panel_field(ax, fig, pal, rng):
    cmap = palette_cmap(pal)
    x, y = np.meshgrid(np.linspace(-3, 3, 240), np.linspace(-3, 3, 240))
    z = (np.exp(-((x - 1) ** 2 + (y - 1) ** 2)) * 2
         - np.exp(-((x + 1.5) ** 2 + (y + 0.8) ** 2) / 2)
         + 0.3 * np.sin(2 * x) * np.cos(2 * y))
    im = ax.imshow(z, cmap=cmap, extent=(-3, 3, -3, 3), origin="lower")
    fig.colorbar(im, ax=ax, shrink=0.85)
    ax.set_title("Gridded field, continuous ramp")


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


# ------------------------------------------------------------------- assemble

def main(name, dem_path=None):
    pal = load_palette(name)
    rng = np.random.default_rng(SEED)

    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5), dpi=140)
    fig.patch.set_facecolor("white")

    panel_violin(axes[0, 0], pal, rng)
    panel_bars(axes[0, 1], pal, rng)
    panel_scatter(axes[0, 2], pal, rng)
    panel_area(axes[1, 0], pal, rng)
    panel_field(axes[1, 1], fig, pal, rng)
    panel_dem(axes[1, 2], pal, dem_path)

    for ax in axes.flat:
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle(f'{pal["name"]}, sample plots', fontsize=16, fontfamily="serif")
    fig.tight_layout(rect=(0, 0, 1, 0.96))

    out_dir = REPO_ROOT / "docs" / pal["name"].lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "samples.png", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_dir / 'samples.png'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("palette", help="name of a file in palettes/")
    ap.add_argument("--dem", help="optional single band GeoTIFF for the "
                                  "elevation panel (needs rasterio)")
    args = ap.parse_args()
    main(args.palette, args.dem)
