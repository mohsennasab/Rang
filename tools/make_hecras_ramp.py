"""Generate importable HEC-RAS custom color-ramp XML files.

The files match the structure exported by the HEC-RAS Surface Fill window.
Each palette gets its own file, and Rang-All.xml contains the full collection.

Run this script directly to rebuild the HEC-RAS folder:

  python tools/make_hecras_ramp.py

The main build calls the same writer whenever a palette is added or changed.
"""
from pathlib import Path
from xml.sax.saxutils import escape

from colorlib import REPO_ROOT, all_palettes, hex_to_argb_int


CUSTOM_COLOR = 16777215
CUSTOM_COLOR_COUNT = 16


def normalized_values(count):
    """Evenly spaced values from zero to one in HEC-RAS export form."""
    if count < 2:
        raise ValueError("a HEC-RAS color ramp needs at least two colors")
    return ",".join(
        f"{index / (count - 1):.6f}".rstrip("0").rstrip(".")
        for index in range(count)
    )


def _attribute(value):
    """Escape an XML attribute while keeping the double-quote export style."""
    return escape(str(value), {'"': "&quot;"})


def surface_fill(palette):
    """Return one user-defined SurfaceFill entry for a Rang palette."""
    colors = palette["colors"]
    attributes = [
        ("Colors", ",".join(str(hex_to_argb_int(color)) for color in colors)),
        ("Values", normalized_values(len(colors))),
        ("Stretched", "True"),
        ("AlphaTag", "255"),
        ("UseDatasetMinMax", "False"),
        ("RegenerateForScreen", "False"),
        ("Name", f'Rang - {palette["name"]}'),
    ]
    values = " ".join(f'{key}="{_attribute(value)}"' for key, value in attributes)
    return f"<SurfaceFill {values} />"


def custom_color_ramps(palettes):
    """Return a complete HEC-RAS custom color-ramp export document."""
    ramps = "".join(surface_fill(palette) for palette in palettes)
    custom_colors = "".join(
        f"<Color>{CUSTOM_COLOR}</Color>" for _ in range(CUSTOM_COLOR_COUNT)
    )
    return (
        f"<Root><UserDefinedColorRamps>{ramps}</UserDefinedColorRamps>"
        f"<CustomColors>{custom_colors}</CustomColors></Root>"
    )


def write_files(palettes, output_dir=None):
    """Write every individual ramp and the combined Rang collection."""
    palettes = list(palettes)
    output_dir = Path(output_dir or REPO_ROOT / "hecras")
    output_dir.mkdir(parents=True, exist_ok=True)

    for palette in palettes:
        output = output_dir / f'Rang-{palette["name"]}.xml'
        output.write_text(custom_color_ramps([palette]), encoding="utf-8")
        print(f"wrote {output}")

    combined = output_dir / "Rang-All.xml"
    combined.write_text(custom_color_ramps(palettes), encoding="utf-8")
    print(f"wrote {combined}")


def main():
    write_files(all_palettes())


if __name__ == "__main__":
    main()
