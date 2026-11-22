"""Generate crisp light and dark SVG visuals for the landing README chooser.

Reads palettes/*.json and the pixel medallion matrix from tools/make_logo.py
using only the Python standard library, writing deterministic SVGs into
site/readme/.

Usage:
    python tools/make_readme_graphics.py
"""
from __future__ import annotations

import ast
import html
import json
import pathlib
import re
import unicodedata
from typing import Dict, List, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
PALETTE_DIR = REPO_ROOT / "palettes"
MAKE_LOGO_PATH = REPO_ROOT / "tools" / "make_logo.py"
DEFAULT_OUT_DIR = REPO_ROOT / "site" / "readme"

FONT_SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT_FA = "Tahoma, 'Segoe UI', Arial, sans-serif"

HERO_RIBBON = (
    "#7f3020",
    "#ae6259",
    "#cbb11c",
    "#7fb5c1",
    "#d9a545",
    "#4027e1",
    "#56adee",
    "#d63d3b",
    "#4b3d97",
    "#d8c723",
    "#0412cc",
    "#55a67e",
)


def palette_slug(value: str) -> str:
    plain = "".join(
        ch for ch in unicodedata.normalize("NFKD", str(value))
        if not unicodedata.combining(ch)
    )
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def load_palettes() -> List[dict]:
    pals = []
    for path in sorted(PALETTE_DIR.glob("*.json")):
        pal = json.loads(path.read_text(encoding="utf-8"))
        pal["slug"] = palette_slug(pal["name"])
        pals.append(pal)
    return sorted(pals, key=lambda p: (p.get("position", 10 ** 9), p["name"]))


def load_logo_matrix() -> Tuple[Tuple[str, ...], Dict[str, str]]:
    """Extract GRID and hex PALETTE from tools/make_logo.py without Pillow."""
    tree = ast.parse(MAKE_LOGO_PATH.read_text(encoding="utf-8"))
    grid: Tuple[str, ...] = ()
    colors: Dict[str, str] = {"K": "#000000"}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "GRID":
                    grid = tuple(ast.literal_eval(node.value))
                elif isinstance(target, ast.Name) and target.id == "PALETTE":
                    if isinstance(node.value, ast.Dict):
                        for k_node, v_node in zip(node.value.keys, node.value.values):
                            if not isinstance(k_node, ast.Constant):
                                continue
                            key = str(k_node.value)
                            src = ast.get_source_segment(MAKE_LOGO_PATH.read_text(encoding="utf-8"), v_node) or ""
                            m_hex = re.search(r"#[0-9a-fA-F]{6}", src)
                            if m_hex:
                                colors[key] = m_hex.group(0)
                            elif key == "K":
                                colors[key] = "#000000"
    return grid, colors


def render_medallion_svg(
    grid: Tuple[str, ...],
    colors: Dict[str, str],
    x: float,
    y: float,
    size: float,
) -> str:
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    cell = size / cols if cols else 1
    rects: List[str] = []
    for r_idx, row in enumerate(grid):
        for c_idx, sym in enumerate(row):
            col = colors.get(sym)
            if not col:
                continue
            rx = x + c_idx * cell
            ry = y + r_idx * cell
            rects.append(
                f'<rect x="{rx:.2f}" y="{ry:.2f}" width="{cell + 0.15:.2f}" '
                f'height="{cell + 0.15:.2f}" fill="{col}"/>'
            )
    return '<g shape-rendering="crispEdges">\n' + "\n".join(rects) + "\n</g>"


def top_bar_svg(
    clip_id: str,
    width: int,
    height: int,
    radius: int,
    bar_h: int,
    colors: Tuple[str, ...] | List[str],
) -> str:
    n = len(colors)
    seg_w = width / n
    segs = "".join(
        f'<rect x="{i * seg_w:.2f}" y="0" width="{seg_w + 0.5:.2f}" height="{bar_h}" fill="{c}"/>'
        for i, c in enumerate(colors)
    )
    return (
        f'<defs><clipPath id="{clip_id}">'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="{radius}"/>'
        f"</clipPath></defs>\n"
        f'<g clip-path="url(#{clip_id})">{segs}</g>'
    )


def teardrop_path(cx: float, cy: float, r: float, stretch: float = 1.6) -> str:
    tip_y = cy - r * stretch * 1.55
    body_y = cy + r * 0.35
    return (
        f"M {cx:.1f},{tip_y:.1f} "
        f"C {cx + r * 0.55:.1f},{cy - r * 0.45:.1f} {cx + r:.1f},{cy - r * 0.05:.1f} {cx + r:.1f},{body_y:.1f} "
        f"A {r:.1f},{r:.1f} 0 1,1 {cx - r:.1f},{body_y:.1f} "
        f"C {cx - r:.1f},{cy - r * 0.05:.1f} {cx - r * 0.55:.1f},{cy - r * 0.45:.1f} {cx:.1f},{tip_y:.1f} Z"
    )


def build_hero_svg(dark: bool, grid: Tuple[str, ...], logo_colors: Dict[str, str]) -> str:
    w, h = 920, 240
    bg = "#161f2e" if dark else "#ffffff"
    border = "#2c3b54" if dark else "#dce5f2"
    mount_bg = "#1e293d" if dark else "#f4f7fc"
    ink = "#eef2fb" if dark else "#131c2e"
    sub = "#b5c1d8" if dark else "#41506b"
    fa_col = "#68d8e8" if dark else "#0f7b8a"
    sep_col = "#f0b429" if dark else "#e6a817"
    pill_bg = "#1e2a3e" if dark else "#eff4fc"
    pill_ink = "#8fb4ff" if dark else "#2448c8"

    bar = top_bar_svg("hero-clip", w, h, 18, 7, HERO_RIBBON)
    medallion = render_medallion_svg(grid, logo_colors, 40, 56, 120)

    # Glossy drops and splash pools on the right edge
    drops_svg = f"""
  <g opacity="0.95">
    <path d="{teardrop_path(758, 66, 8.5, 1.55)}" fill="#e05336"/>
    <ellipse cx="755.5" cy="67.5" rx="2.0" ry="3.6" fill="#ffffff" opacity="0.45"/>

    <path d="{teardrop_path(802, 108, 11.0, 1.65)}" fill="#4027e1"/>
    <ellipse cx="798.8" cy="110.0" rx="2.5" ry="4.5" fill="#ffffff" opacity="0.42"/>

    <path d="{teardrop_path(848, 78, 9.5, 1.5)}" fill="#efbf15"/>
    <ellipse cx="845.2" cy="79.5" rx="2.1" ry="3.8" fill="#ffffff" opacity="0.48"/>

    <path d="{teardrop_path(882, 134, 8.0, 1.5)}" fill="#55a67e"/>
    <ellipse cx="879.7" cy="135.4" rx="1.8" ry="3.2" fill="#ffffff" opacity="0.44"/>

    <path d="{teardrop_path(774, 158, 7.2, 1.45)}" fill="#56adee"/>
    <ellipse cx="772.0" cy="159.2" rx="1.6" ry="2.8" fill="#ffffff" opacity="0.45"/>
  </g>
  <g clip-path="url(#hero-clip)">
    <circle cx="744" cy="212" r="4.2" fill="#e05336" opacity="0.85"/>
    <circle cx="792" cy="204" r="3.4" fill="#efbf15" opacity="0.88"/>
    <circle cx="835" cy="196" r="4.8" fill="#56adee" opacity="0.85"/>
    <circle cx="876" cy="206" r="3.8" fill="#55a67e" opacity="0.85"/>
    <path d="M 712,240 C 722,221 738,220 748,228 C 756,216 774,218 782,230 C 794,216 812,218 820,240 Z" fill="#4027e1" opacity="0.88"/>
    <path d="M 762,240 C 770,224 786,223 794,231 C 804,214 824,216 832,229 C 844,219 860,224 866,240 Z" fill="#56adee" opacity="0.90"/>
    <path d="M 818,240 C 826,222 842,221 852,229 C 862,212 882,214 890,228 C 899,220 912,224 918,240 Z" fill="#efbf15" opacity="0.90"/>
    <path d="M 678,240 C 686,227 702,225 712,233 C 722,222 738,225 744,240 Z" fill="#e05336" opacity="0.88"/>
  </g>"""

    dots = "".join(
        f'<circle cx="{196 + i * 20}" cy="186" r="6" fill="{c}"/>'
        for i, c in enumerate(HERO_RIBBON[:8])
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Rang color palettes banner">
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="{bg}" stroke="{border}"/>
  {bar}
  <g clip-path="url(#hero-clip)" opacity="{0.14 if dark else 0.22}">
    <circle cx="96" cy="24" r="140" fill="#74ecf9"/>
    <circle cx="848" cy="28" r="150" fill="#efbf15"/>
  </g>
  <rect x="28" y="44" width="144" height="144" rx="14" fill="{mount_bg}" stroke="{border}"/>
  {medallion}
  <text x="192" y="88" font-family="{FONT_SANS}" font-size="40" font-weight="800" fill="{ink}" letter-spacing="-0.8">Rang <tspan fill="{sep_col}" font-weight="500">|</tspan> <tspan font-family="{FONT_FA}" font-size="34" font-weight="700" fill="{fa_col}">رنگ</tspan></text>
  <text x="192" y="124" font-family="{FONT_SANS}" font-size="16" font-weight="500" fill="{sub}">Color palettes drawn from Persian, Iranian, and Persianate art and culture.</text>
  <text x="192" y="148" font-family="{FONT_SANS}" font-size="15.5" font-weight="400" fill="{sub}">Practical color schemes for Python, R, ArcGIS Pro, QGIS, GeoLibre, and HEC-RAS.</text>
  {dots}
  <rect x="362" y="172" width="142" height="28" rx="14" fill="{pill_bg}" stroke="{border}"/>
  <text x="433" y="191" text-anchor="middle" font-family="{FONT_SANS}" font-size="12.5" font-weight="700" fill="{pill_ink}">12 curated palettes</text>
  {drops_svg}
</svg>
"""


def build_card_website_svg(dark: bool) -> str:
    w, h = 448, 236
    bg = "#161f2e" if dark else "#ffffff"
    border = "#2c3b54" if dark else "#d5e0f2"
    win_bg = "#101826" if dark else "#f4f7fc"
    ink = "#eef2fb" if dark else "#131c2e"
    sub = "#b5c1d8" if dark else "#41506b"
    pill_bg = "#1b2d4a" if dark else "#eaf1ff"
    pill_fg = "#8fb4ff" if dark else "#1e43c2"
    cta_bg = "#3b6df0" if dark else "#2448c8"
    cta_fg = "#ffffff"

    bar = top_bar_svg("cw-clip", w, h, 16, 6, ("#3b1261", "#4027e1", "#518ffd", "#74ecf9", "#50a877", "#6dd96f", "#ebc05c", "#f04a23"))

    mini = f"""
  <g transform="translate(306, 22)">
    <rect x="0" y="0" width="118" height="62" rx="8" fill="{win_bg}" stroke="{border}"/>
    <rect x="0" y="0" width="118" height="14" rx="8" fill="{pill_bg}"/>
    <circle cx="10" cy="7" r="2.2" fill="#e05336"/>
    <circle cx="18" cy="7" r="2.2" fill="#efbf15"/>
    <circle cx="26" cy="7" r="2.2" fill="#50a877"/>
    <rect x="9" y="21" width="100" height="8" rx="3" fill="#4027e1" opacity="0.22"/>
    <rect x="9" y="21" width="20" height="8" rx="3" fill="#4027e1"/>
    <rect x="29" y="21" width="20" height="8" fill="#518ffd"/>
    <rect x="49" y="21" width="20" height="8" fill="#74ecf9"/>
    <rect x="69" y="21" width="20" height="8" fill="#ebc05c"/>
    <rect x="89" y="21" width="20" height="8" rx="3" fill="#f04a23"/>
    <path d="{teardrop_path(28, 46, 3.8, 1.4)}" fill="#518ffd"/>
    <path d="{teardrop_path(59, 49, 4.2, 1.45)}" fill="#ebc05c"/>
    <path d="{teardrop_path(90, 45, 3.8, 1.4)}" fill="#f04a23"/>
    <path d="M 14,62 C 19,55 28,55 34,58 C 40,53 50,55 56,62 Z" fill="#518ffd"/>
    <path d="M 48,62 C 55,54 65,54 71,59 C 78,53 90,54 96,62 Z" fill="#ebc05c"/>
    <path d="M 78,62 C 84,56 95,55 104,62 Z" fill="#f04a23"/>
  </g>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Interactive Website card">
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{bg}" stroke="{border}"/>
  {bar}
  <rect x="24" y="24" width="124" height="24" rx="12" fill="{pill_bg}"/>
  <text x="86" y="40" text-anchor="middle" font-family="{FONT_MONO}" font-size="10.5" font-weight="700" fill="{pill_fg}" letter-spacing="0.6">INTERACTIVE SITE</text>
  {mini}
  <text x="24" y="108" font-family="{FONT_SANS}" font-size="23" font-weight="800" fill="{ink}" letter-spacing="-0.4">Interactive Website</text>
  <text x="24" y="136" font-family="{FONT_SANS}" font-size="13.5" fill="{sub}">Browse all 12 palettes with click-to-copy hex swatches,</text>
  <text x="24" y="156" font-family="{FONT_SANS}" font-size="13.5" fill="{sub}">paint drop splashes, light and dark mode, and full plates.</text>
  <rect x="24" y="178" width="252" height="36" rx="9" fill="{cta_bg}"/>
  <text x="138" y="201" text-anchor="middle" font-family="{FONT_SANS}" font-size="13.5" font-weight="700" fill="{cta_fg}">Open hydromohsen.com/Rang</text>
  <path d="M 248,196 h12 m-4,-4 l4,4 l-4,4" fill="none" stroke="{cta_fg}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def build_card_github_svg(dark: bool) -> str:
    w, h = 448, 236
    bg = "#161f2e" if dark else "#ffffff"
    border = "#2c3b54" if dark else "#d5e0f2"
    doc_bg = "#101826" if dark else "#f7f3eb"
    doc_line = "#2c3b54" if dark else "#d6cbb8"
    ink = "#eef2fb" if dark else "#131c2e"
    sub = "#b5c1d8" if dark else "#41506b"
    pill_bg = "#2d2122" if dark else "#faece9"
    pill_fg = "#f09988" if dark else "#7f3020"
    cta_bg = "#273549" if dark else "#1a2832"
    cta_fg = "#ffffff"

    bar = top_bar_svg("cg-clip", w, h, 16, 6, ("#7f3020", "#ab4a47", "#c07049", "#c59b46", "#ccac7e", "#e2cfb1", "#8a9463", "#345f72", "#1a3b45"))

    mini = f"""
  <g transform="translate(306, 22)">
    <rect x="0" y="0" width="118" height="62" rx="8" fill="{doc_bg}" stroke="{border}"/>
    <text x="10" y="18" font-family="{FONT_MONO}" font-size="11" font-weight="700" fill="#c07049"># Rang</text>
    <rect x="10" y="24" width="66" height="4" rx="2" fill="{doc_line}"/>
    <rect x="10" y="32" width="98" height="10" rx="3" fill="#7f3020" opacity="0.2"/>
    <rect x="10" y="32" width="19" height="10" rx="2" fill="#7f3020"/>
    <rect x="30" y="32" width="19" height="10" fill="#c07049"/>
    <rect x="50" y="32" width="19" height="10" fill="#c59b46"/>
    <rect x="70" y="32" width="19" height="10" fill="#8a9463"/>
    <rect x="90" y="32" width="18" height="10" rx="2" fill="#345f72"/>
    <rect x="10" y="48" width="84" height="4" rx="2" fill="{doc_line}"/>
  </g>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Traditional GitHub README card">
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{bg}" stroke="{border}"/>
  {bar}
  <rect x="24" y="24" width="120" height="24" rx="12" fill="{pill_bg}"/>
  <text x="84" y="40" text-anchor="middle" font-family="{FONT_MONO}" font-size="10.5" font-weight="700" fill="{pill_fg}" letter-spacing="0.6">GITHUB MARKDOWN</text>
  {mini}
  <text x="24" y="108" font-family="{FONT_SANS}" font-size="23" font-weight="800" fill="{ink}" letter-spacing="-0.4">Traditional GitHub README</text>
  <text x="24" y="136" font-family="{FONT_SANS}" font-size="13.5" fill="{sub}">Read the classic single-page Markdown guide directly</text>
  <text x="24" y="156" font-family="{FONT_SANS}" font-size="13.5" fill="{sub}">on GitHub with every palette, install step, and credit.</text>
  <rect x="24" y="178" width="230" height="36" rx="9" fill="{cta_bg}"/>
  <text x="128" y="201" text-anchor="middle" font-family="{FONT_SANS}" font-size="13.5" font-weight="700" fill="{cta_fg}">Read README-GITHUB.md</text>
  <path d="M 226,196 h12 m-4,-4 l4,4 l-4,4" fill="none" stroke="{cta_fg}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""


def build_palette_strip_svg(dark: bool, pals: List[dict]) -> str:
    w, h = 920, 224
    bg = "#161f2e" if dark else "#ffffff"
    border = "#2c3b54" if dark else "#dce5f2"
    tile_bg = "#1c273a" if dark else "#f7f9fd"
    ink = "#eef2fb" if dark else "#131c2e"
    muted = "#95a4bf" if dark else "#62728b"

    cols = 4
    pad_x = 18
    pad_y = 16
    gap_x = 12
    gap_y = 12
    tile_w = (w - 2 * pad_x - (cols - 1) * gap_x) / cols
    tile_h = (h - 2 * pad_y - 2 * gap_y) / 3

    tiles: List[str] = []
    for idx, pal in enumerate(pals[:12]):
        col_i = idx % cols
        row_i = idx // cols
        tx = pad_x + col_i * (tile_w + gap_x)
        ty = pad_y + row_i * (tile_h + gap_y)
        colors = pal["colors"]
        bar_w = tile_w - 20
        seg_w = bar_w / len(colors)
        clip_id = f"pstrip-{idx}"
        segs = "".join(
            f'<rect x="{10 + c_idx * seg_w:.2f}" y="30" width="{seg_w + 0.4:.2f}" height="15" fill="{c}"/>'
            for c_idx, c in enumerate(colors)
        )
        tiles.append(f"""
  <g transform="translate({tx:.1f}, {ty:.1f})">
    <rect x="0" y="0" width="{tile_w:.1f}" height="{tile_h:.1f}" rx="10" fill="{tile_bg}" stroke="{border}"/>
    <text x="11" y="20" font-family="{FONT_SANS}" font-size="12.5" font-weight="700" fill="{ink}">{html.escape(pal["name"])}</text>
    <text x="{tile_w - 11:.1f}" y="20" text-anchor="end" font-family="{FONT_FA}" font-size="11.5" fill="{muted}">{html.escape(pal.get("persian", ""))}</text>
    <clipPath id="{clip_id}"><rect x="10" y="30" width="{bar_w:.1f}" height="15" rx="4"/></clipPath>
    <g clip-path="url(#{clip_id})">{segs}</g>
  </g>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="All 12 Rang color palettes">
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="{bg}" stroke="{border}"/>
  {''.join(tiles)}
</svg>
"""


def generate_readme_graphics(out_dir: pathlib.Path = DEFAULT_OUT_DIR) -> List[pathlib.Path]:
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pals = load_palettes()
    grid, logo_colors = load_logo_matrix()

    outputs = {
        "hero-light.svg": build_hero_svg(False, grid, logo_colors),
        "hero-dark.svg": build_hero_svg(True, grid, logo_colors),
        "card-website-light.svg": build_card_website_svg(False),
        "card-website-dark.svg": build_card_website_svg(True),
        "card-github-light.svg": build_card_github_svg(False),
        "card-github-dark.svg": build_card_github_svg(True),
        "palette-strip-light.svg": build_palette_strip_svg(False, pals),
        "palette-strip-dark.svg": build_palette_strip_svg(True, pals),
    }

    written: List[pathlib.Path] = []
    for name, svg in outputs.items():
        dest = out_dir / name
        dest.write_text(svg, encoding="utf-8")
        written.append(dest)
    return written


def main() -> None:
    written = generate_readme_graphics()
    print(f"Wrote {len(written)} SVG files -> {DEFAULT_OUT_DIR}")


if __name__ == "__main__":
    main()
