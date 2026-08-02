"""Rang, color palettes from Persian art.

Palettes are stored as a ramp of hex colors plus a pick order. Asking for a
few colors returns a well separated subset, asking for more than the palette
holds interpolates along the ramp.
"""

import operator

from ._palettes import PALETTES

__version__ = "0.1.0"
__all__ = ["rang", "cmap", "list_palettes", "source", "colorblind_friendly", "PALETTES"]


def list_palettes(colorblind_only=False):
    """Names of the available palettes, sorted."""
    names = sorted(PALETTES)
    if colorblind_only:
        names = [n for n in names if PALETTES[n]["colorblind"]]
    return names


def _get(name):
    if name not in PALETTES:
        raise KeyError(f"Unknown palette {name!r}. "
                       f"Available: {', '.join(sorted(PALETTES))}")
    return PALETTES[name]


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _positive_integer(value):
    if isinstance(value, bool):
        raise TypeError("n must be an integer")
    try:
        value = operator.index(value)
    except TypeError as exc:
        raise TypeError("n must be an integer") from exc
    if value < 1:
        raise ValueError("n must be at least 1")
    return value


def _check_direction(direction):
    if direction not in (1, -1):
        raise ValueError("direction must be 1 or -1")


def _interpolate(colors, n):
    if n == 1:
        return [colors[0]]
    rgbs = [_hex_to_rgb(c) for c in colors]
    out = []
    for i in range(n):
        t = i * (len(colors) - 1) / (n - 1)
        j = min(int(t), len(colors) - 2)
        f = t - j
        rgb = tuple(round(a + (b - a) * f) for a, b in zip(rgbs[j], rgbs[j + 1]))
        out.append("#{:02x}{:02x}{:02x}".format(*rgb))
    return out


def rang(name, n=None, kind=None, direction=1, override_order=False):
    """Return a list of hex colors from a palette.

    Parameters
    ----------
    name : palette name, see list_palettes()
    n : how many colors, defaults to the full palette
    kind : "discrete" or "continuous". Defaults to discrete while n fits the
        palette and continuous beyond that.
    direction : 1 for the stored order, -1 to reverse
    override_order : take the first n ramp colors instead of the stored
        pick order
    """
    pal = _get(name)
    colors, order = list(pal["colors"]), list(pal["order"])
    if n is None:
        n = len(colors)
    n = _positive_integer(n)
    _check_direction(direction)
    if kind is None:
        kind = "continuous" if n > len(colors) else "discrete"
    if kind not in ("discrete", "continuous"):
        raise ValueError("kind must be 'discrete' or 'continuous'")

    if kind == "discrete":
        if n > len(colors):
            raise ValueError(f"{name} holds {len(colors)} colors, "
                             f"use kind='continuous' for more")
        out = colors[:n] if override_order else [c for c, r in zip(colors, order) if r <= n]
    else:
        out = _interpolate(colors, n)
    return out[::-1] if direction == -1 else out


def cmap(name, direction=1):
    """A matplotlib colormap built from the palette ramp."""
    _check_direction(direction)
    from matplotlib.colors import LinearSegmentedColormap
    colors = list(_get(name)["colors"])
    if direction == -1:
        colors = colors[::-1]
    return LinearSegmentedColormap.from_list(name, colors)


def source(name):
    """Provenance of the artwork behind a palette."""
    return dict(_get(name)["source"])


def colorblind_friendly(name):
    """Project CVD separation flag, not an accessibility guarantee."""
    return bool(_get(name)["colorblind"])
