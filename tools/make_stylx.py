"""Build arcgis/Rang.stylx, an ArcGIS Pro style holding every palette.

A .stylx is a SQLite database of style items whose content is CIM JSON. This
script writes the tables and item structures used by a style inspected in
ArcGIS Pro 3.x. Esri does not publish the internal database schema. Each
palette contributes its colors, a smooth scheme, and a fixed scheme with the
exact palette steps.

Import once in Pro through the Catalog pane, Styles, Add, Add Style File.
The schemes then appear in every color scheme dropdown and the colors in
every color picker, no integer raster required.

Runs on its own or through tools/build.py.

  python tools/make_stylx.py
"""
import json
import sqlite3

from colorlib import REPO_ROOT, all_palettes, hex_to_rgb

# the class catalog ArcGIS Pro writes into user styles
CLASSES = [(1, "Color"), (2, "Color Scheme"), (3, "Point Symbol"),
           (4, "Line Symbol"), (5, "Polygon Symbol"), (6, "Text Symbol"),
           (7, "North Arrow"), (8, "Scale Bar"), (9, "Standard Label Placement"),
           (10, "Maplex Label Placement"), (11, "Grid"), (12, "Mesh Symbol"),
           (13, "Legend"), (14, "Table Frame"), (15, "Map Surround"),
           (17, "Legend Item"), (18, "Table Frame Field")]

META = [("version", "1.0"), ("cim_version", "3.0.0"), ("build", "36057"),
        ("content", "json"), ("colorModel", "RGB"),
        ("RGBColorProfile", "sRGB IEC61966-2.1"),
        ("CMYKColorProfile", "U.S. Web Coated (SWOP) v2")]


def cim_color(hexcode):
    r, g, b = (int(v) for v in hex_to_rgb(hexcode))
    return {"type": "CIMRGBColor", "values": [r, g, b, 100]}


def continuous_ramp(colors):
    segments = [{"type": "CIMLinearContinuousColorRamp",
                 "colorSpace": {"type": "CIMICCColorSpace", "url": "Default RGB"},
                 "fromColor": cim_color(a),
                 "toColor": cim_color(b)}
                for a, b in zip(colors, colors[1:])]
    return {"type": "CIMMultipartColorRamp", "colorRamps": segments,
            "weights": [1] * len(segments)}


def fixed_ramp(colors):
    return {"type": "CIMFixedColorRamp", "colors": [cim_color(c) for c in colors]}


def write_stylx(pals, out=None):
    out = out or REPO_ROOT / "arcgis" / "Rang.stylx"
    temp = out.with_name(out.name + ".tmp")
    if temp.exists():
        temp.unlink()
    db = sqlite3.connect(temp)
    cur = db.cursor()
    cur.executescript("""
        CREATE TABLE ITEMS (ID INTEGER PRIMARY KEY, CLASS INTEGER,
            CATEGORY TEXT, NAME TEXT, TAGS TEXT, CONTENT TEXT, KEY TEXT UNIQUE);
        CREATE INDEX ITEMS_ID ON ITEMS (ID);
        CREATE INDEX ITEMS_CLASS ON ITEMS (CLASS);
        CREATE INDEX ITEMS_KEY ON ITEMS (KEY);
        CREATE TABLE CLASSES (ID INTEGER PRIMARY KEY, NAME TEXT);
        CREATE INDEX CLASSES_ID ON CLASSES (ID);
        CREATE TABLE meta (key TEXT, value TEXT);
        CREATE TABLE BINARY_CLASSES (ID INTEGER PRIMARY KEY, NAME TEXT);
        CREATE INDEX BINARY_CLASSES_ID ON BINARY_CLASSES (ID);
        CREATE TABLE BINARIES (ID INTEGER PRIMARY KEY, MD5 STRING UNIQUE,
            CLASS INTEGER, CONTENT BLOB);
        CREATE INDEX BINARIES_ID ON BINARIES (ID);
        CREATE INDEX BINARIES_MD5 ON BINARIES (MD5);
        CREATE INDEX BINARIES_CLASS ON BINARIES (CLASS);
        CREATE TABLE STYLE_ITEM_BINARY_REFERENCES (ID INTEGER PRIMARY KEY,
            ITEMS_ID INTEGER NOT NULL, BINARIES_ID INTEGER NOT NULL,
            FOREIGN KEY(ITEMS_ID) REFERENCES ITEMS(ID),
            FOREIGN KEY(BINARIES_ID) REFERENCES BINARIES(ID),
            UNIQUE(ITEMS_ID, BINARIES_ID));
    """)
    cur.executemany("INSERT INTO meta VALUES (?, ?)", META)
    cur.executemany("INSERT INTO CLASSES VALUES (?, ?)", CLASSES)

    items = []
    for p in pals:
        name = p["name"]
        tags = f"Rang, Persian art, {name}"
        if p.get("persian"):
            tags += f', {p["persian"]}'
        for i, c in enumerate(p["colors"], start=1):
            items.append((1, "Rang", f"Rang - {name} {i:02d} ({c})", tags,
                          json.dumps(cim_color(c))))
        items.append((2, "Rang", f"Rang - {name}", tags,
                      json.dumps(continuous_ramp(p["colors"]))))
        items.append((2, "Rang", f"Rang - {name} discrete", tags,
                      json.dumps(fixed_ramp(p["colors"]))))

    cur.executemany(
        "INSERT INTO ITEMS (CLASS, CATEGORY, NAME, TAGS, CONTENT) VALUES (?, ?, ?, ?, ?)",
        items)
    db.commit()
    db.close()
    try:
        temp.replace(out)
    except PermissionError:
        temp.unlink()
        print(f"skipped {out}, another program is holding it open. "
              "ArcGIS Pro locks styles it has loaded, close Pro or remove "
              "the style there and rerun the build to refresh the file.")
        return False
    print(f"wrote {out} ({len(items)} style items, {len(pals)} palettes)")
    return True


if __name__ == "__main__":
    write_stylx(all_palettes())
