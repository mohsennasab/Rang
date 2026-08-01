"""Shared color math for the Rang tools.

Covers sRGB to CIELAB and LCh conversions, color vision deficiency simulation
after Machado et al. (2009), the CIEDE2000 color difference, and the palette
level helpers built on top of them. Pure numpy, so the whole toolchain runs
without a color science dependency.
"""
import itertools
import json
import pathlib
import urllib.request

import numpy as np

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PALETTE_DIR = REPO_ROOT / "palettes"
CACHE_DIR = REPO_ROOT / "cache"

# Smallest pairwise CIEDE2000 a palette must keep under every simulated vision
# type before we mark it colorblind friendly. Calibrated against palettes whose
# friendliness is widely agreed on rather than picked from thin air.
COLORBLIND_THRESHOLD = 8.0

# ---------------------------------------------------------------- sRGB and Lab

M_XYZ = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
WHITE = np.array([0.95047, 1.0, 1.08883])


def hex_to_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def rgb_to_hex(rgb):
    r, g, b = np.round(np.clip(rgb, 0, 255)).astype(int)
    return f"#{r:02x}{g:02x}{b:02x}"


def srgb_to_linear(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, float), 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def rgb_to_lab(rgb):
    xyz = srgb_to_linear(rgb) @ M_XYZ.T / WHITE
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_rgb(lab):
    lab = np.asarray(lab, float)
    fy = (lab[..., 0] + 16) / 116
    fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787) * WHITE
    return linear_to_srgb(xyz @ np.linalg.inv(M_XYZ).T)


def lab_to_lch(lab):
    L, a, b = np.asarray(lab, float)
    return np.array([L, np.hypot(a, b), np.degrees(np.arctan2(b, a)) % 360])


def lch_to_lab(lch):
    L, C, h = np.asarray(lch, float)
    return np.array([L, C * np.cos(np.radians(h)), C * np.sin(np.radians(h))])


# ------------------------------------------- vision simulation (Machado 2009)
# Severity 1.0 matrices applied in linear light RGB.

CVD_MATRIX = {
    "protan": np.array([[0.152286, 1.052583, -0.204868],
                        [0.114503, 0.786281, 0.099216],
                        [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968],
                        [0.280085, 0.672501, 0.047413],
                        [-0.011820, 0.042940, 0.968881]]),
    "tritan": np.array([[1.255528, -0.076749, -0.178779],
                        [-0.078411, 0.930809, 0.147602],
                        [0.004733, 0.691367, 0.303900]]),
}

VISION_TYPES = (None, "protan", "deutan", "tritan")
VISION_LABELS = {None: "normal vision", "protan": "protanopia",
                 "deutan": "deuteranopia", "tritan": "tritanopia"}


def simulate(rgb, kind):
    """Simulate dichromatic vision. kind=None returns rgb unchanged."""
    if kind is None:
        return np.asarray(rgb, float)
    return linear_to_srgb(srgb_to_linear(rgb) @ CVD_MATRIX[kind].T)


# ------------------------------------------------------------------- CIEDE2000

def ciede2000(lab1, lab2):
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp) / 2)
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2
    T = (1 - 0.17 * np.cos(np.radians(hbp - 30)) + 0.24 * np.cos(np.radians(2 * hbp))
         + 0.32 * np.cos(np.radians(3 * hbp + 6)) - 0.20 * np.cos(np.radians(4 * hbp - 63)))
    dth = 30 * np.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7))
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / np.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -np.sin(np.radians(2 * dth)) * Rc
    return float(np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                         + Rt * (dCp / Sc) * (dHp / Sh)))


# ---------------------------------------------------------- palette level math

def pairwise_min_mean(hexes, kind=None):
    """Minimum and mean CIEDE2000 between all color pairs under one vision type."""
    lab = rgb_to_lab(simulate(np.array([hex_to_rgb(h) for h in hexes]), kind))
    ds = [ciede2000(lab[i], lab[j]) for i, j in itertools.combinations(range(len(lab)), 2)]
    return min(ds), float(np.mean(ds))


def worst_case(hexes):
    """Smallest pairwise distance across all four vision types."""
    return min(pairwise_min_mean(hexes, k)[0] for k in VISION_TYPES)


def worst_pair(hexes):
    """The single closest pair of colors and the vision type where it happens."""
    best = None
    for kind in VISION_TYPES:
        lab = rgb_to_lab(simulate(np.array([hex_to_rgb(h) for h in hexes]), kind))
        for i, j in itertools.combinations(range(len(hexes)), 2):
            d = ciede2000(lab[i], lab[j])
            if best is None or d < best[0]:
                best = (d, hexes[i], hexes[j], VISION_LABELS[kind])
    return best


def greedy_order(hexes):
    """Build the discrete pick order stored with each palette.

    order[i] is the n at which color i first enters the discrete palette, so
    requesting n colors returns those with order <= n, kept in ramp sequence.
    Each step adds the color that maximizes the minimum CIEDE2000 distance to
    the colors already picked, judged across all four vision types at once.
    """
    n = len(hexes)
    rgb = np.array([hex_to_rgb(h) for h in hexes])
    labs = {k: rgb_to_lab(simulate(rgb, k)) for k in VISION_TYPES}

    def dist(i, j):
        return min(ciede2000(labs[k][i], labs[k][j]) for k in VISION_TYPES)

    first = max(itertools.combinations(range(n), 2), key=lambda p: dist(*p))
    chosen = sorted(first)
    while len(chosen) < n:
        rest = [i for i in range(n) if i not in chosen]
        chosen.append(max(rest, key=lambda i: min(dist(i, j) for j in chosen)))
    order = [0] * n
    for rank, i in enumerate(chosen, start=1):
        order[i] = rank
    return order


def discrete_subset(colors, order, n):
    """The n colors met by rank, kept in ramp sequence."""
    return [c for c, r in zip(colors, order) if r <= n]


def interpolate(colors, n):
    """n colors linearly interpolated along the ramp in sRGB."""
    if n == 1:
        return [colors[0]]
    rgbs = [hex_to_rgb(c) for c in colors]
    out = []
    for i in range(n):
        t = i * (len(colors) - 1) / (n - 1)
        j = min(int(t), len(colors) - 2)
        f = t - j
        out.append(rgb_to_hex(rgbs[j] + (rgbs[j + 1] - rgbs[j]) * f))
    return out


def presence_in_image(hexes, image_path, step=17):
    """How close each color sits to an actual pixel of the source photo.

    Returns {hex: (nearest CIEDE2000, percent of sampled pixels within 8.0)}.
    Evidence that a palette really comes off the artwork instead of being
    invented around it.
    """
    from PIL import Image
    im = Image.open(image_path).convert("RGB")
    im.thumbnail((800, 800))
    lab = rgb_to_lab(np.asarray(im).reshape(-1, 3).astype(float))[::step]
    out = {}
    for h in hexes:
        target = rgb_to_lab(hex_to_rgb(h))
        d = np.array([ciede2000(target, px) for px in lab])
        out[h] = (float(d.min()), float((d < 8).mean() * 100))
    return out


# ------------------------------------------------------------ palette loading

def load_palette(name):
    """Read palettes/<name>.json. Accepts 'Kashan', 'kashan' or a file path."""
    p = pathlib.Path(name)
    if not p.suffix == ".json":
        p = PALETTE_DIR / f"{str(name).lower()}.json"
    if not p.exists():
        options = ", ".join(sorted(f.stem for f in PALETTE_DIR.glob("*.json")))
        raise FileNotFoundError(f"No palette file {p}. Available: {options}")
    pal = json.loads(p.read_text(encoding="utf-8"))
    for key in ("name", "colors", "source"):
        if key not in pal:
            raise KeyError(f"{p} is missing the required key '{key}'")
    return pal


def all_palettes():
    """Every palette, in gallery order.

    Palettes carry a position number assigned in order of addition, so the
    gallery keeps the collection's history instead of shuffling alphabetically
    whenever a new name lands.
    """
    pals = [load_palette(f.stem) for f in sorted(PALETTE_DIR.glob("*.json"))]
    return sorted(pals, key=lambda p: (p.get("position", 10 ** 9), p["name"]))


def fetch_image(url_or_path):
    """Return a local path for an image, downloading into cache/ when needed.

    Accepts a URL, an absolute path, or a path relative to the repo root, which
    is how palette files reference photos committed under sources/.
    """
    p = pathlib.Path(url_or_path)
    if p.exists():
        return p
    rel = REPO_ROOT / str(url_or_path)
    if rel.exists():
        return rel
    CACHE_DIR.mkdir(exist_ok=True)
    local = CACHE_DIR / pathlib.Path(str(url_or_path).split("?")[0]).name
    if not local.exists():
        print(f"downloading {url_or_path}")
        req = urllib.request.Request(str(url_or_path),
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r, open(local, "wb") as f:
            f.write(r.read())
    return local
