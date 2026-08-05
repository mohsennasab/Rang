import importlib
import json
import pathlib
import re
import sqlite3
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "python"))

import colorlib
import notebook_workflow
import rang


class PaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.palettes = colorlib.all_palettes()

    def test_schema_order_and_flag(self):
        self.assertEqual([p["name"] for p in self.palettes],
                         ["Kashan", "Golestan", "Termeh", "Khatam", "Nasir",
                          "Mina", "Rostan", "Shahnameh"])
        for palette in self.palettes:
            colors = palette["colors"]
            self.assertEqual(palette["order"], colorlib.greedy_order(colors))
            self.assertEqual(palette["colorblind"],
                             colorlib.worst_case(colors) >= colorlib.COLORBLIND_THRESHOLD)

    def test_persian_names(self):
        expected = {
            "Kashan": "کاشان",
            "Golestan": "گلستان",
            "Termeh": "ترمه",
            "Khatam": "خاتم",
            "Nasir": "نصیر",
            "Mina": "مینا",
            "Rostan": "رستن",
            "Shahnameh": "شاهنامه",
        }
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

    def test_hecras_imports(self):
        expected_files = {f'Rang-{palette["name"]}.xml'
                          for palette in self.palettes}
        expected_files.add("Rang-All.xml")
        self.assertEqual(
            {path.name for path in (ROOT / "hecras").glob("*.xml")},
            expected_files,
        )

        for palette in self.palettes:
            path = ROOT / "hecras" / f'Rang-{palette["name"]}.xml'
            text = path.read_text(encoding="utf-8")
            self.assertEqual(len(text.splitlines()), 1)
            root = ET.fromstring(text)
            fills = root.findall("./UserDefinedColorRamps/SurfaceFill")
            self.assertEqual(len(fills), 1)
            expected = [str(colorlib.hex_to_argb_int(c)) for c in palette["colors"]]
            self.assertEqual(fills[0].attrib["Colors"].split(","), expected)
            self.assertEqual(fills[0].attrib["Name"], f'Rang - {palette["name"]}')
            self.assertEqual(fills[0].attrib["Stretched"], "True")
            self.assertEqual(fills[0].attrib["AlphaTag"], "255")
            self.assertEqual(fills[0].attrib["UseDatasetMinMax"], "False")
            self.assertEqual(fills[0].attrib["RegenerateForScreen"], "False")
            self.assertEqual(len(fills[0].attrib["Values"].split(",")),
                             len(expected))
            custom = root.findall("./CustomColors/Color")
            self.assertEqual([color.text for color in custom], ["16777215"] * 16)

        combined_text = (ROOT / "hecras" / "Rang-All.xml").read_text(
            encoding="utf-8")
        self.assertEqual(len(combined_text.splitlines()), 1)
        combined = ET.fromstring(combined_text)
        fills = combined.findall("./UserDefinedColorRamps/SurfaceFill")
        self.assertEqual(
            [fill.attrib["Name"] for fill in fills],
            [f'Rang - {palette["name"]}' for palette in self.palettes],
        )
        for fill, palette in zip(fills, self.palettes):
            expected = [str(colorlib.hex_to_argb_int(color))
                        for color in palette["colors"]]
            self.assertEqual(fill.attrib["Colors"].split(","), expected)
        custom = combined.findall("./CustomColors/Color")
        self.assertEqual([color.text for color in custom], ["16777215"] * 16)

    def test_geolibre_color_bundle(self):
        bundle = json.loads((ROOT / "geolibre" / "Rang.json").read_text(
            encoding="utf-8"))
        text = (ROOT / "geolibre" / "Rang.txt").read_text(encoding="utf-8")
        self.assertEqual(bundle["format"], "rang-geolibre-colors")
        self.assertEqual(bundle["version"], 1)
        self.assertEqual(bundle["license"], "CC0-1.0")
        self.assertEqual(set(bundle["palettes"]),
                         {palette["name"] for palette in self.palettes})
        for palette in self.palettes:
            entry = bundle["palettes"][palette["name"]]
            self.assertEqual(entry["raster_anchors"], palette["colors"])
            for n in range(2, 13):
                self.assertEqual(entry["graduated"][str(n)],
                                 colorlib.interpolate(palette["colors"], n))
            for n in range(2, len(palette["colors"]) + 1):
                expected = [color for color, rank in
                            zip(palette["colors"], palette["order"]) if rank <= n]
                self.assertEqual(entry["categorical"][str(n)], expected)
            self.assertIn(f'{palette["name"]}\n  raster anchors:', text)

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
        with Image.open(ROOT / "docs" / "termeh" / "samples.png") as image:
            self.assertEqual(image.size, (2100, 1120))

    def test_rostan_card_preserves_the_complete_painting(self):
        with Image.open(ROOT / "docs" / "rostan" / "card.png") as image:
            panel = image.convert("RGB").crop((0, 0, 600, 450))
        white = Image.new("RGB", panel.size, "white")
        self.assertEqual(ImageChops.difference(panel, white).getbbox(),
                         (73, 0, 527, 450))

    def test_stream_network_attributes(self):
        data = json.loads((ROOT / "data" / "streams.json").read_text(
            encoding="utf-8"))
        flowlines = data["flowlines"]
        self.assertGreater(len(flowlines), 100)
        self.assertTrue(all(line["stream_order"] >= 1 for line in flowlines))
        self.assertTrue(all(line["drainage_sq_km"] >= 0 for line in flowlines))
        self.assertGreater(max(line["drainage_sq_km"] for line in flowlines), 300)
        self.assertGreater(len({line["stream_order"] for line in flowlines}), 2)
        self.assertTrue(any(line["main_stem"] for line in flowlines))

    def test_license_scope_and_package_copies(self):
        root_license = (ROOT / "LICENSE").read_text(encoding="utf-8")
        cc0 = (ROOT / "LICENSES" / "CC0-1.0.txt").read_text(encoding="utf-8")
        scope = (ROOT / "LICENSES" / "README.md").read_text(encoding="utf-8")
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        python_license = (ROOT / "python" / "LICENSE").read_text(encoding="utf-8")
        python_cc0 = (ROOT / "python" / "LICENSE-CC0.txt").read_text(
            encoding="utf-8")
        r_cc0 = (ROOT / "r" / "inst" / "LICENSE-CC0.txt").read_text(
            encoding="utf-8")
        self.assertIn("MIT License", root_license)
        self.assertEqual(root_license, python_license)
        self.assertIn("CC0 1.0 Universal", cc0)
        self.assertIn("CC0 1.0 Universal", python_cc0)
        self.assertEqual(python_cc0, r_cc0.replace("R software", "Python software")
                         .replace("identified in DESCRIPTION and LICENSE",
                                  "in LICENSE"))
        self.assertIn("palette names, color values", scope)
        self.assertRegex(notices.lower(), r"all rights\s+are reserved")

    def test_colab_notebooks(self):
        notebooks = {
            "rang_python_colab.ipynb": ("python", "python3"),
            "rang_r_colab.ipynb": ("R", "ir"),
        }
        for filename, (language, kernel) in notebooks.items():
            path = ROOT / "examples" / filename
            notebook = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(notebook["nbformat"], 4)
            self.assertEqual(notebook["metadata"]["kernelspec"]["name"], kernel)
            self.assertEqual(notebook["metadata"]["kernelspec"]["language"], language)
            first_cell = "".join(notebook["cells"][0]["source"])
            self.assertIn("colab-badge.svg", first_cell)
            self.assertIn(f"/examples/{filename}", first_cell)
            for cell in notebook["cells"]:
                if cell["cell_type"] == "code":
                    self.assertEqual(cell["outputs"], [])
                    self.assertIsNone(cell["execution_count"])

    def test_palette_workflow_notebooks(self):
        filenames = [
            "01_define_regions.ipynb",
            "02_extract_colors.ipynb",
            "03_curate_palette.ipynb",
            "04_adjust_colors.ipynb",
            "05_check_palette.ipynb",
            "06_build_palette.ipynb",
            "07_replay_and_verify.ipynb",
        ]
        for folder in ("notebooks", "examole"):
            for filename in filenames:
                path = ROOT / "tools" / folder / filename
                notebook = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(notebook["nbformat"], 4)
                self.assertEqual(notebook["metadata"]["kernelspec"]["name"],
                                 "python3")
                text = "".join("".join(cell["source"])
                               for cell in notebook["cells"])
                self.assertIn("colab-badge.svg", text)
                self.assertIn(f"/tools/{folder}/{filename}", text)
                self.assertIn("Mohsen Tahmasebi Nasab, PhD", text)
                self.assertIn("https://hydromohsen.com", text)
                self.assertIn("license holder", text.lower())
                self.assertIn("Arial", text)
                self.assertIn("files.upload", text)
                self.assertIn("workflow ZIP", text)
                self.assertNotIn("drive.mount", text)
                self.assertNotIn("git clone", text)
                self.assertNotIn("REPO_REF", text)
                self.assertNotIn("github.com/mohsennasab/Rang.git", text)
                tags = {tag for cell in notebook["cells"]
                        for tag in cell.get("metadata", {}).get("tags", [])}
                self.assertIn("user-input", tags)
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "code":
                        self.assertEqual(cell["outputs"], [])
                        self.assertIsNone(cell["execution_count"])

    def test_notebook_recipe_replays(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = pathlib.Path(temporary)
            image_path = folder / "fixture.png"
            image = Image.new("RGB", (100, 20))
            colors = ["#7f3020", "#ab4a47", "#c59b46", "#8a9463", "#345f72"]
            for index, color in enumerate(colors):
                image.paste(color, (index * 20, 0, (index + 1) * 20, 20))
            image.save(image_path)
            recipe_path = folder / "fixture-recipe.json"
            notebook_workflow.create_recipe(
                "Fixture", image_path, image_path,
                [{"id": "color-strip", "label": "Color strip",
                  "box": [0, 0, 100, 20], "k": 5,
                  "note": "Five exact color fields"}],
                recipe_path,
            )
            candidates = notebook_workflow.save_candidates(
                recipe_path, folder, accept=True)
            selections = [
                {"candidate": candidate["id"], "note": candidate["region_label"]}
                for candidate in candidates
            ]
            notebook_workflow.save_curation(recipe_path, selections)
            notebook_workflow.apply_adjustments(
                recipe_path,
                [{"target": "p01", "delta": {"L": 1, "C": 0, "H": 0},
                  "reason": "fixture replay check"}],
            )
            result = notebook_workflow.verify_recipe(recipe_path, folder)
            self.assertTrue(result["verified"])

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

    def test_readmes_avoid_canned_copy(self):
        banned = ["project " + "cvd separation", "screening rule " + "is not"]
        for path in ROOT.rglob("README.md"):
            text = path.read_text(encoding="utf-8").lower()
            for phrase in banned:
                self.assertNotIn(phrase, text, str(path))


if __name__ == "__main__":
    unittest.main()
