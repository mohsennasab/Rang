import importlib
import json
import pathlib
import re
import sqlite3
import sys
import unittest
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "python"))

import colorlib
import rang


class PaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palettes = colorlib.all_palettes()

    def test_schema_order_and_flag(self):
        self.assertEqual([p["name"] for p in self.palettes],
                         ["Kashan", "Golestan", "Termeh"])
        for palette in self.palettes:
            colors = palette["colors"]
            self.assertEqual(palette["order"], colorlib.greedy_order(colors))
            self.assertEqual(palette["colorblind"],
                             colorlib.worst_case(colors) >= colorlib.COLORBLIND_THRESHOLD)

    def test_persian_names(self):
        expected = {"Kashan": "کاشان", "Golestan": "گلستان", "Termeh": "ترمه"}
        self.assertEqual({p["name"]: p["persian"] for p in self.palettes}, expected)

    def test_ciede2000_reference_pairs(self):
        cases = [
            ((50, 2.6772, -79.7751), (50, 0, -82.7485), 2.0425),
            ((50, 3.1571, -77.2803), (50, 0, -82.7485), 2.8615),
            ((50, 2.8361, -74.0200), (50, 0, -82.7485), 3.4412),
        ]
        for first, second, expected in cases:
            self.assertAlmostEqual(colorlib.ciede2000(first, second), expected, places=4)

    def test_python_api(self):
        self.assertEqual(rang.rang("Kashan", 4),
                         ["#7f3020", "#c07049", "#e2cfb1", "#1a3b45"])
        continuous = rang.rang("Termeh", 17, "continuous")
        self.assertEqual((continuous[0], continuous[-1]),
                         ("#e5f0ee", "#274e68"))
        self.assertEqual(rang.rang("Termeh", 4, direction=-1),
                         list(reversed(rang.rang("Termeh", 4))))
        for value in (0, -1):
            with self.assertRaises(ValueError):
                rang.rang("Kashan", value)
        for value in (True, 2.5, "3"):
            with self.assertRaises(TypeError):
                rang.rang("Kashan", value)
        with self.assertRaises(ValueError):
            rang.cmap("Kashan", direction=0)

    def test_python_and_r_data_match_json(self):
        importlib.reload(rang)
        r_text = (ROOT / "r" / "R" / "palettes_data.R").read_text(encoding="utf-8")
        for palette in self.palettes:
            generated = rang.PALETTES[palette["name"]]
            self.assertEqual(list(generated["colors"]), palette["colors"])
            self.assertEqual(list(generated["order"]), palette["order"])
            for color in palette["colors"]:
                self.assertIn(f'"{color}"', r_text)


class OutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palettes = colorlib.all_palettes()

    def test_qgis_style(self):
        root = ET.parse(ROOT / "qgis" / "Rang.xml").getroot()
        ramps = root.findall("./colorramps/colorramp")
        self.assertEqual(len(ramps), len(self.palettes) * 2)
        names = {ramp.attrib["name"] for ramp in ramps}
        for palette in self.palettes:
            self.assertIn(palette["name"], names)
            self.assertIn(f'{palette["name"]} discrete', names)

    def test_gpl_swatches(self):
        for palette in self.palettes:
            lines = (ROOT / "qgis" / f'{palette["name"]}.gpl').read_text(
                encoding="utf-8").splitlines()[4:]
            rgb = [tuple(map(int, line.split()[:3])) for line in lines]
            expected = [tuple(int(v) for v in colorlib.hex_to_rgb(c))
                        for c in palette["colors"]]
            self.assertEqual(rgb, expected)

    def test_hecras_blocks(self):
        for palette in self.palettes:
            text = (ROOT / "hecras" / f'{palette["name"]}.rasmap.xml').read_text(
                encoding="utf-8")
            root = ET.fromstring(f"<root>{text}</root>")
            fills = root.findall("./Symbology/SurfaceFill")
            self.assertEqual(len(fills), 2)
            expected = [str(colorlib.hex_to_argb_int(c)) for c in palette["colors"]]
            self.assertEqual(fills[0].attrib["Colors"].split(","), expected)
            self.assertEqual(fills[1].attrib["Colors"].split(","), expected[::-1])

    def test_arcgis_style_database(self):
        db = sqlite3.connect(ROOT / "arcgis" / "Rang.stylx")
        try:
            rows = db.execute("SELECT CLASS, NAME, CONTENT FROM ITEMS").fetchall()
        finally:
            db.close()
        expected_count = sum(len(p["colors"]) + 2 for p in self.palettes)
        self.assertEqual(len(rows), expected_count)
        self.assertEqual(sum(row[0] == 2 for row in rows), len(self.palettes) * 2)
        for _, _, content in rows:
            self.assertIn("type", json.loads(content))

    def test_image_dimensions(self):
        expected = {"swatch.png": (1600, 360), "card.png": (1600, 450),
                    "preview.png": (1600, 1000)}
        for palette in self.palettes:
            folder = ROOT / "docs" / palette["name"].lower()
            for filename, size in expected.items():
                with Image.open(folder / filename) as image:
                    self.assertEqual(image.size, size)
        with Image.open(ROOT / "logo" / "rang.png") as image:
            self.assertEqual(image.size, (1024, 1024))

    def test_no_embedded_origin_markers(self):
        words = ["cl" + "aude", "anth" + "ropic", "chat" + "g" + "pt",
                 "open" + "ai", "ge" + "mini", "co" + "pilot",
                 "trainedAlgorithmic" + "Media", "g" + "pt" + "-image"]
        ignored = {ROOT / ".git", ROOT / "cache"}
        for path in ROOT.rglob("*"):
            if (not path.is_file() or path.suffix == ".pyc"
                    or "__pycache__" in path.parts
                    or any(parent in ignored for parent in path.parents)):
                continue
            data = path.read_bytes().lower()
            for word in words:
                self.assertNotIn(word.lower().encode(), data, str(path))

    def test_human_documents_use_plain_punctuation(self):
        paths = list(ROOT.rglob("*.md")) + list((ROOT / "r" / "man").glob("*.Rd"))
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for codepoint in (0x2014, 0x2013, 0x3B):
                self.assertNotIn(chr(codepoint), text, str(path))


if __name__ == "__main__":
    unittest.main()
