from __future__ import annotations

from html.parser import HTMLParser
import json
import pathlib
import re
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_site


class PageInspector(HTMLParser):
    """Collect text, element IDs, hrefs, and srcs from an HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []
        self.srcs: list[str] = []
        self.imgs: list[dict[str, str | None]] = []
        self.text_parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        if attr_map.get("id"):
            self.ids.add(attr_map["id"])
        if tag in ("a", "link") and attr_map.get("href"):
            self.hrefs.append(attr_map["href"])
        if tag in ("img", "script") and attr_map.get("src"):
            self.srcs.append(attr_map["src"])
        if tag == "img":
            self.imgs.append({
                "src": attr_map.get("src"),
                "width": attr_map.get("width"),
                "height": attr_map.get("height"),
            })
        if tag in ("script", "style"):
            self._skip_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self.text_parts.append(data)

    def plain_text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.text_parts)).strip()


def inspect_page(path: pathlib.Path) -> PageInspector:
    parser = PageInspector()
    parser.feed(path.read_text(encoding="utf-8"))
    parser.close()
    return parser


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.out = pathlib.Path(cls._tmpdir.name) / "site"
        cls.summary = build_site.build_site(cls.out)
        cls.palettes = build_site.load_all_palettes()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def test_expected_files_and_assets_exist(self) -> None:
        self.assertEqual(self.summary["pages"], 14)
        self.assertTrue((self.out / ".nojekyll").is_file())
        self.assertTrue((self.out / "index.html").is_file())
        self.assertTrue((self.out / "language-and-scope" / "index.html").is_file())
        for rel in ("assets/style.css", "assets/site.js", "assets/logo.png"):
            self.assertTrue((self.out / rel).is_file(), rel)

        for pal in self.palettes:
            slug = pal["slug"]
            self.assertTrue((self.out / "palettes" / slug / "index.html").is_file(), slug)
            for png in ("card.png", "swatch.png", "preview.png", "regions.png", "samples.png"):
                self.assertTrue((self.out / "assets" / "palettes" / slug / png).is_file(), f"{slug}/{png}")
            ctx = pal.get("source", {}).get("context_image")
            if ctx:
                ctx_name = pathlib.Path(ctx).name
                self.assertTrue((self.out / "assets" / "sources" / slug / ctx_name).is_file(), f"{slug}/{ctx_name}")

    def test_all_internal_links_anchors_and_images_resolve(self) -> None:
        html_files = sorted(self.out.rglob("*.html"))
        self.assertEqual(len(html_files), 14)

        parsed_by_rel = {
            p.relative_to(self.out).as_posix(): inspect_page(p)
            for p in html_files
        }

        for page_path in html_files:
            rel_page = page_path.relative_to(self.out).as_posix()
            info = parsed_by_rel[rel_page]

            for src in info.srcs:
                if src.startswith(("http://", "https://", "data:")):
                    continue
                self.assertFalse(src.startswith("/"), f"{rel_page}: root-relative src {src!r}")
                target = (page_path.parent / src).resolve()
                self.assertTrue(target.is_file(), f"{rel_page}: missing src {src!r}")

            for img in info.imgs:
                src = img["src"] or ""
                if src.startswith("data:"):
                    continue
                self.assertTrue(
                    img["width"] and img["width"].isdigit() and int(img["width"]) > 0,
                    f"{rel_page}: image {src!r} missing numeric width",
                )
                self.assertTrue(
                    img["height"] and img["height"].isdigit() and int(img["height"]) > 0,
                    f"{rel_page}: image {src!r} missing numeric height",
                )

            for href in info.hrefs:
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                self.assertFalse(href.startswith("/"), f"{rel_page}: root-relative href {href!r}")
                path_part, sep, frag = href.partition("#")
                if not path_part:
                    self.assertIn(frag, info.ids, f"{rel_page}: missing anchor #{frag}")
                    continue

                resolved = (page_path.parent / path_part).resolve()
                if resolved.is_dir():
                    resolved = resolved / "index.html"
                self.assertTrue(resolved.is_file(), f"{rel_page}: broken href {href!r}")
                if sep and frag:
                    target_rel = resolved.relative_to(self.out).as_posix()
                    self.assertIn(
                        frag,
                        parsed_by_rel[target_rel].ids,
                        f"{rel_page}: missing anchor #{frag} on {target_rel}",
                    )

    def test_landing_page_preserves_readme_content_verbatim(self) -> None:
        index_text = inspect_page(self.out / "index.html").plain_text()
        self.assertNotIn("[!NOTE]", index_text)
        self.assertNotIn("\\(", index_text)
        self.assertNotIn("2020\\.", index_text)
        self.assertIn("2020.", index_text)
        self.assertIn("Iranian vitreous enamel, cropped", index_text)

        expected_phrases = [
            "Rang is a collection of color palettes drawn from Persian, Iranian, and Persianate art and culture.",
            "Created by Mohsen Tahmasebi Nasab, PhD.",
            "Every palette traces to a documented source photograph.",
            "Use Rang with Python, R, ArcGIS Pro, QGIS, GeoLibre and HEC-RAS.",
            "pip install rang",
            'remotes::install_github("mohsennasab/Rang", subdir = "r")',
            "One build command regenerates the Python, R, ArcGIS, QGIS, GeoLibre and HEC-RAS files",
            "Rang source code is licensed under the MIT License.",
            "dedicated to the public domain under CC0 1.0 Universal.",
        ]
        for phrase in expected_phrases:
            self.assertIn(phrase, index_text)

        for pal in self.palettes:
            self.assertIn(pal["name"], index_text)
            self.assertIn(pal["persian"], index_text)
            if pal["name"] != "Confusion":
                self.assertIn(pal["pronunciation"], index_text)
            else:
                self.assertIn("sar-dar-go-MEE", index_text)
            for hx in pal["colors"]:
                self.assertIn(hx, index_text)
            if pal.get("about"):
                self.assertIn(re.sub(r"\s+", " ", pal["about"]).strip(), index_text)

    def test_palette_and_language_pages_preserve_content_verbatim(self) -> None:
        lang_text = inspect_page(self.out / "language-and-scope" / "index.html").plain_text()
        for heading in ("Persian", "Iranian", "Persianate", "How Rang uses these terms", "References"):
            self.assertIn(heading, lang_text)
        self.assertIn("Rang welcomes palettes from Persian, Iranian, and Persianate art and culture.", lang_text)

        for pal in self.palettes:
            slug = pal["slug"]
            page_text = inspect_page(self.out / "palettes" / slug / "index.html").plain_text()
            self.assertIn(pal["name"], page_text)
            self.assertIn(pal["persian"], page_text)
            self.assertIn(pal["pronunciation"], page_text)
            expected_source = pal["source"].get("citation") or pal["source"]["title"]
            self.assertIn(re.sub(r"\s+", " ", expected_source).strip(), page_text)
            for hx, note in zip(pal["colors"], pal["notes"]):
                self.assertIn(hx, page_text)
                self.assertIn(re.sub(r"\s+", " ", note).strip(), page_text)
            if pal.get("about"):
                self.assertIn(re.sub(r"\s+", " ", pal["about"]).strip(), page_text)

    def test_mina_escaped_wikimedia_url_is_unescaped(self) -> None:
        raw_index = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            "https://commons.wikimedia.org/wiki/File:Iranian_vitreous_enamel_(cropped).JPG",
            raw_index,
        )
        self.assertNotIn("Iranian_vitreous_enamel_\\", raw_index)

    def test_code_highlighter_preserves_exact_text(self) -> None:
        sample = 'import rang\nrang.rang("Termeh", 100, "continuous") # smooth ramp\n'
        highlighted = build_site.highlight_code(sample, "python")
        stripped = re.sub(r"<[^>]+>", "", highlighted)
        self.assertEqual(stripped, sample)

    def test_modern_fonts_and_paint_canvas_markup(self) -> None:
        raw_index = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn("Bricolage+Grotesque", raw_index)
        self.assertIn("Plus+Jakarta+Sans", raw_index)
        self.assertNotIn("Cormorant+Garamond", raw_index)
        self.assertIn('id="paint-canvas"', raw_index)
        self.assertIn("data-paint-toggle", raw_index)
        self.assertIn("data-splash-color", raw_index)
        self.assertIn("data-splash-palette", raw_index)
        self.assertIn("plate-color-bar", raw_index)

        raw_kashan = (self.out / "palettes" / "kashan" / "index.html").read_text(encoding="utf-8")
        self.assertIn('data-palette-colors="#7f3020,', raw_kashan)
        self.assertIn('id="paint-canvas"', raw_kashan)


if __name__ == "__main__":
    unittest.main()
