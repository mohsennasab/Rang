"""Build the static website for Rang from the repository documentation.

Reads README.md, palettes/*.json, docs/language-and-scope.md, docs/*/README.md,
the generated palette figures under docs/<name>/, context photographs under
sources/<name>/, and the medallion logo under logo/ to produce a self-contained
static site under build/site (or a custom --output path).

Usage:
    python tools/build_site.py
    python tools/build_site.py --output build/site
"""
from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import shutil
import struct
import unicodedata
from typing import Dict, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE_ASSETS_DIR = REPO_ROOT / "site" / "assets"
PALETTE_DIR = REPO_ROOT / "palettes"
DOCS_DIR = REPO_ROOT / "docs"
LOGO_PATH = REPO_ROOT / "logo" / "rang_pixel_medallion_logo.png"

DEFAULT_OUTPUT_DIR = REPO_ROOT / "build" / "site"
DEFAULT_REPO_URL = "https://github.com/mohsennasab/Rang"

RIBBON_COLORS = (
    "#7f3020",
    "#c07049",
    "#c59b46",
    "#6d866a",
    "#5d95a8",
    "#3263ac",
    "#1a3b45",
    "#6b2654",
    "#d9a545",
)

GALLERY_START = "<!-- gallery:start -->"
GALLERY_END = "<!-- gallery:end -->"

PERSIAN_RUN_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+"
    r"(?:[\u200C\u200D ]+[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]+)*"
)

TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')"
    r"|(?P<keyword>\b(?:import|from|as|library|TRUE|FALSE|None)\b)"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
)


def palette_slug(value: str) -> str:
    """Return an ASCII directory slug matching tools/colorlib.py."""
    plain = "".join(
        ch for ch in unicodedata.normalize("NFKD", str(value))
        if not unicodedata.combining(ch)
    )
    slug = re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")
    if not slug:
        raise ValueError(f"invalid palette name: {value!r}")
    return slug


def load_all_palettes() -> List[dict]:
    """Load palettes/*.json in gallery position order."""
    pals = []
    for path in sorted(PALETTE_DIR.glob("*.json")):
        pal = json.loads(path.read_text(encoding="utf-8"))
        pal["slug"] = palette_slug(pal["name"])
        pals.append(pal)
    return sorted(pals, key=lambda p: (p.get("position", 10 ** 9), p["name"]))


def slugify_heading(title: str) -> str:
    """Produce GitHub-style heading anchor slugs."""
    text = title.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s]+", "-", text)
    return text.strip("-")


def star_svg() -> str:
    """Minimalist eight-pointed geometric star motif."""
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.75" aria-hidden="true">'
        '<polygon points="12,2 15,9 22,12 15,15 12,22 9,15 2,12 9,9"/>'
        '<rect x="7.5" y="7.5" width="9" height="9" transform="rotate(45 12 12)"/>'
        "</svg>"
    )


def arrow_right_svg() -> str:
    return (
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true">'
        '<path d="M3 8h10M9 4l4 4-4 4"/></svg>'
    )


def zoom_svg() -> str:
    return (
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true">'
        '<circle cx="7" cy="7" r="4.5"/>'
        '<path d="M10.5 10.5L14 14M7 5v4M5 7h4"/></svg>'
    )


# ------------------------------------------------------------ Link & Image Mapping

def normalize_repo_path(target: str, source_rel_dir: str) -> str:
    """Resolve a relative markdown path against source_rel_dir inside REPO_ROOT."""
    parts = [p for p in source_rel_dir.split("/") if p]
    for seg in target.split("/"):
        if not seg or seg == ".":
            continue
        if seg == "..":
            if parts:
                parts.pop()
        else:
            parts.append(seg)
    return "/".join(parts)


def rewrite_href(
    href: str,
    source_rel_dir: str,
    root_prefix: str,
    repo_url: str,
) -> Tuple[str, bool]:
    """Map markdown hrefs to site-relative routes or GitHub repository URLs.

    Returns (rewritten_href, is_external).
    """
    href = href.strip()
    if href.startswith("#"):
        return href, False
    if re.match(r"^https?://", href):
        return href, True

    path_part, sep, frag = href.partition("#")
    suffix = f"#{frag}" if sep else ""
    norm = normalize_repo_path(path_part, source_rel_dir)

    if norm == "docs/language-and-scope.md":
        return f"{root_prefix}language-and-scope/{suffix}", False

    m = re.fullmatch(r"docs/([a-z0-9-]+)/README\.md", norm)
    if m:
        return f"{root_prefix}palettes/{m.group(1)}/{suffix}", False

    if norm in ("", "README.md"):
        return f"{root_prefix}{suffix}" or "./", False

    target_fs = REPO_ROOT / norm
    repo_base = repo_url.rstrip("/")
    if target_fs.is_dir() or path_part.endswith("/"):
        clean = norm.rstrip("/")
        return f"{repo_base}/tree/main/{clean}{suffix}", True
    return f"{repo_base}/blob/main/{norm}{suffix}", True


def rewrite_image_src(
    src: str,
    source_rel_dir: str,
    root_prefix: str,
) -> str:
    """Map repo image paths to built assets paths."""
    norm = normalize_repo_path(src.strip(), source_rel_dir)
    if norm == "logo/rang_pixel_medallion_logo.png":
        return f"{root_prefix}assets/logo.png"
    m_doc = re.fullmatch(r"docs/([a-z0-9-]+)/([^/]+)", norm)
    if m_doc:
        return f"{root_prefix}assets/palettes/{m_doc.group(1)}/{m_doc.group(2)}"
    m_src = re.fullmatch(r"sources/([a-z0-9-]+)/([^/]+)", norm)
    if m_src:
        return f"{root_prefix}assets/sources/{m_src.group(1)}/{m_src.group(2)}"
    raise ValueError(f"Unmapped image asset in markdown: {norm!r}")


def image_dimensions(path: pathlib.Path) -> Optional[Tuple[int, int]]:
    """Read intrinsic pixel (width, height) from PNG or JPEG headers using stdlib only."""
    if not path.is_file():
        return None
    with path.open("rb") as fh:
        head = fh.read(24)
        if len(head) >= 24 and head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
            w, h = struct.unpack(">II", head[16:24])
            return int(w), int(h)
        if len(head) >= 2 and head[:2] == b"\xff\xd8":
            fh.seek(2)
            while True:
                marker_head = fh.read(2)
                if len(marker_head) < 2:
                    break
                while marker_head[0] != 0xFF:
                    b = fh.read(1)
                    if not b:
                        return None
                    marker_head = bytes([marker_head[1], b[0]])
                while marker_head[1] == 0xFF:
                    b = fh.read(1)
                    if not b:
                        return None
                    marker_head = bytes([0xFF, b[0]])
                marker = marker_head[1]
                if marker in (0xD8, 0xD9, 0x01) or (0xD0 <= marker <= 0xD7):
                    continue
                seg_len_bytes = fh.read(2)
                if len(seg_len_bytes) < 2:
                    break
                seg_len = struct.unpack(">H", seg_len_bytes)[0]
                if seg_len < 2:
                    break
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    sof = fh.read(5)
                    if len(sof) < 5:
                        break
                    h, w = struct.unpack(">HH", sof[1:5])
                    return int(w), int(h)
                fh.seek(seg_len - 2, 1)
    return None


def image_dim_attrs(src: str, source_rel_dir: str) -> str:
    """Return ' width="..." height="..."' for a markdown image path when readable."""
    norm = normalize_repo_path(src.strip(), source_rel_dir)
    dims = image_dimensions(REPO_ROOT / norm)
    if not dims:
        return ""
    return f' width="{dims[0]}" height="{dims[1]}"'


# ------------------------------------------------------------ Inline Markdown

def _unescape_md_text(text: str) -> str:
    return re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", r"\1", text)


def _unescape_md_url(url: str) -> str:
    return re.sub(r"\\([()\\])", r"\1", url)


def _scan_markdown_links(text: str) -> List[Tuple[str, Optional[Tuple[str, str]]]]:
    """Split text into plain chunks and (label, url) links, supporting balanced & escaped parens."""
    out: List[Tuple[str, Optional[Tuple[str, str]]]] = []
    i = 0
    n = len(text)
    buf: List[str] = []

    while i < n:
        if text[i] == "[" and (i == 0 or text[i - 1] != "!"):
            # Find matching ] for label
            j = i + 1
            depth_b = 1
            while j < n and depth_b > 0:
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if text[j] == "[":
                    depth_b += 1
                elif text[j] == "]":
                    depth_b -= 1
                j += 1
            if depth_b == 0 and j < n and text[j] == "(":
                # Scan balanced parens for URL
                k = j + 1
                depth_p = 1
                while k < n and depth_p > 0:
                    if text[k] == "\\" and k + 1 < n:
                        k += 2
                        continue
                    if text[k] == "(":
                        depth_p += 1
                    elif text[k] == ")":
                        depth_p -= 1
                    k += 1
                if depth_p == 0:
                    if buf:
                        out.append(("".join(buf), None))
                        buf = []
                    label = text[i + 1 : j - 1]
                    url = text[j + 1 : k - 1]
                    out.append(("", (label, url)))
                    i = k
                    continue
        buf.append(text[i])
        i += 1

    if buf:
        out.append(("".join(buf), None))
    return out


def _wrap_persian_in_html(fragment: str) -> str:
    """Wrap Persian script runs in <span class='fa' lang='fa' dir='rtl'>, skipping tags & code."""
    parts = re.split(r"(<code\b[^>]*>.*?</code>|<[^>]+>)", fragment, flags=re.DOTALL)
    out: List[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("<"):
            out.append(part)
        else:
            out.append(
                PERSIAN_RUN_RE.sub(
                    lambda m: f'<span class="fa" lang="fa" dir="rtl">{m.group(0)}</span>',
                    part,
                )
            )
    return "".join(out)


def _render_emphasis_and_escapes(text: str) -> str:
    escaped = html.escape(_unescape_md_text(text), quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", escaped)
    return escaped


def render_inline(
    text: str,
    source_rel_dir: str,
    root_prefix: str,
    repo_url: str,
) -> str:
    """Render inline code, links, bold/italic, escapes, and Persian runs to safe HTML."""
    # Step 1: protect inline code spans
    code_slots: List[str] = []

    def _stash_code(match: re.Match[str]) -> str:
        idx = len(code_slots)
        code_slots.append(f"<code>{html.escape(match.group(1), quote=False)}</code>")
        return f"\x00CODE{idx}\x00"

    protected = re.sub(r"`([^`]+)`", _stash_code, text)

    # Step 2: scan links with balanced / escaped parens
    link_slots: List[str] = []
    pieces: List[str] = []
    for chunk, link_pair in _scan_markdown_links(protected):
        if link_pair is None:
            pieces.append(chunk)
        else:
            raw_label, raw_url = link_pair
            label_html = _render_emphasis_and_escapes(raw_label)
            # restore any code tokens inside label
            for idx, code_html in enumerate(code_slots):
                label_html = label_html.replace(f"\x00CODE{idx}\x00", code_html)
            clean_url = _unescape_md_url(raw_url)
            href, is_ext = rewrite_href(clean_url, source_rel_dir, root_prefix, repo_url)
            ext_attrs = ' target="_blank" rel="noopener noreferrer"' if is_ext else ""
            idx = len(link_slots)
            link_slots.append(
                f'<a href="{html.escape(href, quote=True)}"{ext_attrs}>{label_html}</a>'
            )
            pieces.append(f"\x00LINK{idx}\x00")

    rendered = _render_emphasis_and_escapes("".join(pieces))
    for idx, link_html in enumerate(link_slots):
        rendered = rendered.replace(f"\x00LINK{idx}\x00", link_html)
    for idx, code_html in enumerate(code_slots):
        rendered = rendered.replace(f"\x00CODE{idx}\x00", code_html)

    return _wrap_persian_in_html(rendered)


# ------------------------------------------------------------ Code Formatting

def highlight_code(code: str, lang: str) -> str:
    """Apply subtle, safe token spans for Python, R, and shell code blocks."""
    lang_low = (lang or "").lower()
    if lang_low not in ("python", "r", "sh", "bash", "shell", ""):
        return html.escape(code, quote=False)

    out: List[str] = []
    last = 0
    for m in TOKEN_RE.finditer(code):
        if m.start() > last:
            out.append(html.escape(code[last : m.start()], quote=False))
        kind = m.lastgroup
        token = html.escape(m.group(0), quote=False)
        cls_map = {
            "comment": "tok-cmt",
            "string": "tok-str",
            "keyword": "tok-kw",
            "number": "tok-num",
        }
        out.append(f'<span class="{cls_map[kind]}">{token}</span>')
        last = m.end()
    if last < len(code):
        out.append(html.escape(code[last:], quote=False))
    return "".join(out)


def render_code_block(code: str, lang: str) -> str:
    display_lang = lang.lower() if lang else "shell"
    body = highlight_code(code.rstrip("\n"), lang)
    return (
        '<div class="code-block">'
        '<div class="code-head">'
        f'<span class="code-lang">{html.escape(display_lang)}</span>'
        '<button type="button" class="copy-code-btn" data-copy-code>'
        '<span data-copy-label>Copy</span></button>'
        "</div>"
        f"<pre><code>{body}</code></pre>"
        "</div>"
    )


# ------------------------------------------------------------ Block Markdown Parser

def parse_table_row(line: str) -> List[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def is_table_sep(line: str) -> bool:
    cells = parse_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def parse_blocks(md_text: str) -> List[dict]:
    """Parse markdown text into structured AST blocks."""
    lines = md_text.splitlines()
    blocks: List[dict] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Fenced code block
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            i += 1
            code_lines: List[str] = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                i += 1
            blocks.append({"type": "code", "lang": lang, "text": "\n".join(code_lines)})
            continue

        # Horizontal rule
        if re.fullmatch(r"(\*{3,}|-{3,})", stripped):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Headings
        hm = re.match(r"^(#{1,4})\s+(.*)$", line)
        if hm:
            blocks.append({"type": "heading", "level": len(hm.group(1)), "text": hm.group(2).strip()})
            i += 1
            continue

        # Blockquote / GitHub note callout
        if stripped.startswith(">"):
            q_lines: List[str] = []
            while i < n and lines[i].strip().startswith(">"):
                q_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append({"type": "blockquote", "lines": q_lines})
            continue

        # Pipe table
        if "|" in line and i + 1 < n and is_table_sep(lines[i + 1]):
            headers = parse_table_row(line)
            i += 2
            rows: List[List[str]] = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(parse_table_row(lines[i]))
                i += 1
            blocks.append({"type": "table", "headers": headers, "rows": rows})
            continue

        # Ordered list (with indented continuations)
        if re.match(r"^\d+\.\s+", line):
            items: List[str] = []
            while i < n:
                om = re.match(r"^\d+\.\s+(.*)$", lines[i])
                if om:
                    buf = [om.group(1).strip()]
                    i += 1
                    while i < n and lines[i].strip() and (lines[i].startswith("   ") or lines[i].startswith("\t")):
                        buf.append(lines[i].strip())
                        i += 1
                    items.append(" ".join(buf))
                elif not lines[i].strip():
                    # Look ahead for next list item
                    if i + 1 < n and re.match(r"^\d+\.\s+", lines[i + 1]):
                        i += 1
                        continue
                    break
                else:
                    break
            blocks.append({"type": "ol", "items": items})
            continue

        # Unordered list
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < n:
                um = re.match(r"^[-*]\s+(.*)$", lines[i])
                if um:
                    buf = [um.group(1).strip()]
                    i += 1
                    while i < n and lines[i].strip() and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                        buf.append(lines[i].strip())
                        i += 1
                    items.append(" ".join(buf))
                elif not lines[i].strip():
                    if i + 1 < n and re.match(r"^[-*]\s+", lines[i + 1]):
                        i += 1
                        continue
                    break
                else:
                    break
            blocks.append({"type": "ul", "items": items})
            continue

        # Standalone image line
        im = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if im:
            blocks.append({"type": "image", "alt": im.group(1), "src": im.group(2)})
            i += 1
            continue

        # Paragraph
        p_lines: List[str] = []
        while i < n:
            cur = lines[i]
            cur_s = cur.strip()
            if (
                not cur_s
                or cur_s.startswith("```")
                or re.match(r"^#{1,4}\s+", cur)
                or cur_s.startswith(">")
                or re.fullmatch(r"(\*{3,}|-{3,})", cur_s)
                or re.match(r"^\d+\.\s+", cur)
                or re.match(r"^[-*]\s+", cur)
                or re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", cur_s)
                or ("|" in cur and i + 1 < n and is_table_sep(lines[i + 1]))
            ):
                break
            p_lines.append(cur_s)
            i += 1
        blocks.append({"type": "paragraph", "text": " ".join(p_lines)})

    return blocks


def render_table(
    headers: List[str],
    rows: List[List[str]],
    source_rel_dir: str,
    root_prefix: str,
    repo_url: str,
    enhance_hex_col: bool = False,
) -> str:
    th_html = "".join(
        f"<th>{render_inline(h, source_rel_dir, root_prefix, repo_url)}</th>"
        for h in headers
    )
    body_rows: List[str] = []
    for row in rows:
        tds: List[str] = []
        for idx, cell in enumerate(row):
            if enhance_hex_col and idx == 1:
                m_hex = re.fullmatch(r"`?(#[0-9a-fA-F]{6})`?", cell.strip())
                if m_hex:
                    hx = m_hex.group(1)
                    tds.append(
                        '<td><span class="color-cell-hex">'
                        f'<button type="button" class="hex-chip" data-copy="{html.escape(hx, quote=True)}" '
                        f'title="Copy {html.escape(hx, quote=True)}">'
                        f'<span class="swatch-dot" style="--swatch:{html.escape(hx, quote=True)}"></span>'
                        f'<span data-copy-label>{html.escape(hx)}</span></button>'
                        "</span></td>"
                    )
                    continue
            cls = ' class="col-fa" lang="fa" dir="rtl"' if headers[idx].strip().lower() == "persian" else ""
            inner = (
                html.escape(cell.strip())
                if cls
                else render_inline(cell, source_rel_dir, root_prefix, repo_url)
            )
            tds.append(f"<td{cls}>{inner}</td>")
        body_rows.append(f"<tr>{''.join(tds)}</tr>")
    return (
        '<div class="table-wrap"><table class="data-table">'
        f"<thead><tr>{th_html}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
    )


def render_callout(
    q_lines: List[str],
    source_rel_dir: str,
    root_prefix: str,
    repo_url: str,
) -> str:
    """Render GitHub [!NOTE] blockquotes cleanly without exposing raw [!NOTE] syntax."""
    lines = list(q_lines)
    title = ""
    if lines and lines[0].strip().upper() == "[!NOTE]":
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines:
        m = re.fullmatch(r"\*\*(.+?)\*\*", lines[0].strip())
        if m:
            title = m.group(1)
            lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)

    body_text = " ".join(l.strip() for l in lines if l.strip())
    title_html = (
        f'<div class="note-callout-title">{star_svg()}'
        f"<span>{render_inline(title, source_rel_dir, root_prefix, repo_url)}</span></div>"
        if title
        else ""
    )
    body_html = f"<p>{render_inline(body_text, source_rel_dir, root_prefix, repo_url)}</p>" if body_text else ""
    return f'<aside class="note-callout">{title_html}{body_html}</aside>'


def render_blocks_html(
    blocks: List[dict],
    source_rel_dir: str,
    root_prefix: str,
    repo_url: str,
    list_class: str = "",
) -> str:
    out: List[str] = []
    for blk in blocks:
        btype = blk["type"]
        if btype == "paragraph":
            out.append(f'<p>{render_inline(blk["text"], source_rel_dir, root_prefix, repo_url)}</p>')
        elif btype == "heading":
            lvl = blk["level"]
            hid = slugify_heading(blk["text"])
            out.append(
                f'<h{lvl} id="{html.escape(hid, quote=True)}">'
                f'{render_inline(blk["text"], source_rel_dir, root_prefix, repo_url)}</h{lvl}>'
            )
        elif btype == "code":
            out.append(render_code_block(blk["text"], blk["lang"]))
        elif btype == "blockquote":
            out.append(render_callout(blk["lines"], source_rel_dir, root_prefix, repo_url))
        elif btype == "table":
            out.append(render_table(blk["headers"], blk["rows"], source_rel_dir, root_prefix, repo_url))
        elif btype == "ol":
            cls = f' class="{list_class}"' if list_class else ""
            lis = "".join(
                f'<li>{render_inline(item, source_rel_dir, root_prefix, repo_url)}</li>'
                for item in blk["items"]
            )
            out.append(f"<ol{cls}>{lis}</ol>")
        elif btype == "ul":
            lis = "".join(
                f'<li>{render_inline(item, source_rel_dir, root_prefix, repo_url)}</li>'
                for item in blk["items"]
            )
            out.append(f"<ul>{lis}</ul>")
        elif btype == "hr":
            out.append("<hr>")
        elif btype == "image":
            img_src = rewrite_image_src(blk["src"], source_rel_dir, root_prefix)
            dim_attrs = image_dim_attrs(blk["src"], source_rel_dir)
            out.append(
                f'<figure class="plate-frame">'
                f'<img src="{html.escape(img_src, quote=True)}" '
                f'alt="{html.escape(blk["alt"], quote=True)}"{dim_attrs} loading="lazy">'
                f"</figure>"
            )
    return "\n".join(out)


# ------------------------------------------------------------ Shared Chrome

def render_shell(
    *,
    title: str,
    description: str,
    root_prefix: str,
    repo_url: str,
    main_html: str,
    include_lightbox: bool = False,
    body_colors: Optional[List[str]] = None,
) -> str:
    ribbon = "".join(
        f'<button type="button" class="ribbon-swatch" style="background:{c}" '
        f'data-splash-color="{c}" aria-label="Drop {c} paint"></button>'
        for c in RIBBON_COLORS
    )
    palette_attr = html.escape(",".join(body_colors or list(RIBBON_COLORS)), quote=True)
    home_href = root_prefix or "./"
    nav_items = [
        ("Palettes", f"{root_prefix}#palettes", False),
        ("Names", f"{root_prefix}#saying-the-names", False),
        ("Install", f"{root_prefix}#install", False),
        ("Use", f"{root_prefix}#use-the-palettes", False),
        ("How they are made", f"{root_prefix}#how-palettes-are-made", False),
        ("Contribute", f"{root_prefix}#contributing", False),
        ("Credits", f"{root_prefix}#credits-and-license", False),
        ("GitHub", repo_url, True),
    ]
    nav_links_html = "\n".join(
        f'<a href="{html.escape(href, quote=True)}"'
        + (' class="nav-repo" target="_blank" rel="noopener noreferrer"' if ext else "")
        + f">{html.escape(label)}</a>"
        for label, href, ext in nav_items
    )

    lightbox_html = ""
    if include_lightbox:
        lightbox_html = """
<dialog id="plate-lightbox" class="lightbox" aria-label="Enlarged plate preview">
  <div class="lightbox-inner">
    <div class="lightbox-head">
      <span class="lightbox-caption" data-lightbox-caption></span>
      <button type="button" class="lightbox-close" data-lightbox-close>Close</button>
    </div>
    <div class="lightbox-stage">
      <img src="data:," alt="" data-lightbox-img>
    </div>
  </div>
</dialog>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="icon" type="image/png" href="{root_prefix}assets/logo.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700;12..96,800&family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Vazirmatn:wght@400;500;600&display=swap">
  <script>try{{if(localStorage.getItem("rang-theme")==="dark")document.documentElement.dataset.theme="dark";}}catch(e){{}}</script>
  <link rel="stylesheet" href="{root_prefix}assets/style.css">
</head>
<body data-palette-colors="{palette_attr}">
  <div class="pigment-ribbon" role="group" aria-label="Rang pigment drop bar">{ribbon}</div>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="{html.escape(home_href, quote=True)}">
        <img class="brand-mark" src="{root_prefix}assets/logo.png" alt="Rang logo" width="30" height="30">
        <span class="brand-name">Rang</span>
        <span class="brand-fa" lang="fa" dir="rtl">رنگ</span>
      </a>
      <div class="header-actions">
        <nav class="site-nav" id="site-nav" data-nav-menu aria-label="Primary navigation">
          {nav_links_html}
        </nav>
        <button type="button" class="icon-btn" data-paint-toggle aria-pressed="true" aria-label="Toggle paint drop animation">
          <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M8 1.5C6.3 4.1 3.5 7.3 3.5 10a4.5 4.5 0 0 0 9 0c0-2.7-2.8-5.9-4.5-8.5z"/></svg>
          <span class="paint-label">Paint</span>
        </button>
        <button type="button" class="icon-btn" data-theme-toggle aria-pressed="false" aria-label="Toggle color theme">
          <svg data-icon-moon viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M13.5 9.8A5.5 5.5 0 0 1 6.2 2.5a5.5 5.5 0 1 0 7.3 7.3z"/></svg>
          <svg data-icon-sun viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true" style="display:none"><circle cx="8" cy="8" r="3"/><path d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M12.6 3.4l-1.1 1.1M4.5 11.5l-1.1 1.1"/></svg>
          <span class="theme-label">Dark</span>
        </button>
        <button type="button" class="icon-btn nav-toggle" data-nav-toggle aria-expanded="false" aria-controls="site-nav" aria-label="Menu">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h11"/></svg>
        </button>
      </div>
    </div>
  </header>

  <main>
{main_html}
  </main>

  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <img src="{root_prefix}assets/logo.png" alt="" width="22" height="22">
        <span>Rang (<span class="fa" lang="fa" dir="rtl">رنگ</span>) · Mohsen Tahmasebi Nasab, PhD</span>
      </div>
      <div class="footer-links">
        <a href="{html.escape(home_href, quote=True)}">Collection</a>
        <a href="{root_prefix}language-and-scope/">Persian, Iranian, and Persianate</a>
        <a href="{html.escape(repo_url, quote=True)}" target="_blank" rel="noopener noreferrer">GitHub</a>
        <a href="{html.escape(repo_url, quote=True)}/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">MIT License</a>
        <a href="{html.escape(repo_url, quote=True)}/blob/main/LICENSES/CC0-1.0.txt" target="_blank" rel="noopener noreferrer">CC0 1.0 (Palettes)</a>
      </div>
    </div>
  </footer>
  <div id="copy-announcer" class="sr-only" aria-live="polite"></div>
  {lightbox_html}
  <canvas id="paint-canvas" class="paint-canvas" aria-hidden="true"></canvas>
  <script src="{root_prefix}assets/site.js" defer></script>
</body>
</html>
"""


# ------------------------------------------------------------ Helpers

def split_markdown_sections(md_text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Split markdown into preamble before first ## and list of (heading, body)."""
    lines = md_text.splitlines()
    in_code = False
    preamble: List[str] = []
    sections: List[Tuple[str, List[str]]] = []
    current_title: Optional[str] = None
    current_lines: List[str] = []

    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("## "):
            if current_title is not None:
                sections.append((current_title, current_lines))
            current_title = line[3:].strip()
            current_lines = []
        else:
            if current_title is None:
                preamble.append(line)
            else:
                current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, current_lines))

    return "\n".join(preamble), [(t, "\n".join(b).strip()) for t, b in sections]


def section_divider_html() -> str:
    return f'<div class="section-divider">{star_svg()}</div>'


def render_hex_chips(colors: List[str], include_copy_all: bool = True) -> str:
    chips = []
    for c in colors:
        esc = html.escape(c)
        chips.append(
            f'<button type="button" class="hex-chip" data-copy="{esc}" '
            f'title="Copy {esc}">'
            f'<span class="swatch-dot" style="--swatch:{esc}"></span>'
            f'<span data-copy-label>{esc}</span></button>'
        )
    if include_copy_all:
        joined = html.escape(" ".join(colors))
        csv = html.escape(",".join(colors))
        chips.append(
            f'<button type="button" class="copy-all-btn" data-copy="{joined}" '
            f'title="Copy all hex colors">'
            f'<span data-copy-label>Copy all</span></button>'
        )
        chips.append(
            f'<button type="button" class="splash-btn" data-splash-palette="{csv}" '
            f'title="Drop this palette\'s colors">'
            f'<svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">'
            f'<path d="M8 1.5C6.3 4.1 3.5 7.3 3.5 10a4.5 4.5 0 0 0 9 0c0-2.7-2.8-5.9-4.5-8.5z"/></svg>'
            f'<span>Splash</span></button>'
        )
    return '<div class="hex-bar">' + "".join(chips) + "</div>"


# ------------------------------------------------------------ Landing Page

def parse_readme_gallery_entries(gallery_md: str) -> List[dict]:
    """Parse entries between gallery:start and gallery:end without dropping any copy."""
    chunks = re.split(r"\n\*{3,}\n", gallery_md.strip())
    entries: List[dict] = []
    for chunk in chunks:
        blocks = parse_blocks(chunk.strip())
        if not blocks:
            continue
        name = ""
        image = None
        hex_line = ""
        detail_link = None
        prose: List[dict] = []
        for blk in blocks:
            if blk["type"] == "heading" and blk["level"] == 3 and not name:
                name = blk["text"]
            elif blk["type"] == "image" and image is None:
                image = blk
            elif blk["type"] == "paragraph":
                txt = blk["text"].strip()
                m_hex = re.fullmatch(r"`((?:#[0-9a-fA-F]{6}\s*)+)`", txt)
                m_link = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", txt)
                if m_hex:
                    hex_line = m_hex.group(1)
                elif m_link:
                    detail_link = (m_link.group(1), m_link.group(2))
                else:
                    prose.append(blk)
            else:
                prose.append(blk)
        entries.append({
            "name": name,
            "slug": palette_slug(name),
            "image": image,
            "prose": prose,
            "hex_colors": hex_line.split() if hex_line else [],
            "detail_link": detail_link,
        })
    return entries


def render_contents_bar(body_md: str, source_rel_dir: str, root_prefix: str, repo_url: str) -> str:
    links = [p.strip() for p in body_md.strip().split("|") if p.strip()]
    parts = [
        render_inline(item, source_rel_dir, root_prefix, repo_url)
        for item in links
    ]
    joined = '<span class="contents-sep" aria-hidden="true">/</span>'.join(parts)
    return (
        '<nav class="contents-bar" aria-label="Page sections">'
        '<span class="contents-label">Contents</span>'
        f'<div class="contents-links">{joined}</div>'
        "</nav>"
    )


def render_tool_subsections(
    section_id: str,
    heading: str,
    body_md: str,
    source_rel_dir: str,
    root_prefix: str,
    repo_url: str,
) -> str:
    """Render Install and Use sections while preserving every word and code snippet."""
    lines = body_md.splitlines()
    intro_lines: List[str] = []
    sub_sections: List[Tuple[str, List[str]]] = []
    cur_sub: Optional[str] = None
    cur_lines: List[str] = []
    in_code = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("### "):
            if cur_sub is not None:
                sub_sections.append((cur_sub, cur_lines))
            cur_sub = line[4:].strip()
            cur_lines = []
        else:
            if cur_sub is None:
                intro_lines.append(line)
            else:
                cur_lines.append(line)
    if cur_sub is not None:
        sub_sections.append((cur_sub, cur_lines))

    intro_html = ""
    if "\n".join(intro_lines).strip():
        intro_html = (
            '<div class="prose-col">'
            + render_blocks_html(parse_blocks("\n".join(intro_lines)), source_rel_dir, root_prefix, repo_url)
            + "</div>"
        )

    code_cards: List[str] = []
    gis_cards: List[str] = []
    for title, s_lines in sub_sections:
        s_md = "\n".join(s_lines).strip()
        blocks = parse_blocks(s_md)
        has_code = any(b["type"] == "code" for b in blocks)
        rendered = render_blocks_html(blocks, source_rel_dir, root_prefix, repo_url)
        if has_code:
            code_cards.append(
                f'<div class="sub-block">'
                f'<h3 class="subhead" id="{slugify_heading(title)}">{html.escape(title)}</h3>'
                f"{rendered}</div>"
            )
        else:
            gis_cards.append(
                f'<div class="tool-card">'
                f'<h3 id="{slugify_heading(title)}">{html.escape(title)}</h3>'
                f"{rendered}</div>"
            )

    grid_html = f'<div class="tool-grid">{"".join(gis_cards)}</div>' if gis_cards else ""
    return (
        f'<section class="page-section" id="{html.escape(section_id, quote=True)}">'
        f"{section_divider_html()}"
        f'<h2 class="section-heading">{html.escape(heading)}</h2>'
        f"{intro_html}"
        f"{''.join(code_cards)}"
        f"{grid_html}"
        "</section>"
    )


def build_index(
    readme_text: str,
    palettes: List[dict],
    repo_url: str,
) -> str:
    pal_by_slug = {p["slug"]: p for p in palettes}
    preamble, sections = split_markdown_sections(readme_text)

    # Parse hero preamble (remove the inline <img align="right"...> from H1 and place it in hero-specimen)
    preamble_lines = preamble.splitlines()
    h1_line = preamble_lines[0] if preamble_lines else "# Rang | رنگ"
    h1_clean = re.sub(r"<img\b[^>]*>", "", h1_line).strip().lstrip("#").strip()
    hero_body_md = "\n".join(preamble_lines[1:]).strip()
    hero_blocks = parse_blocks(hero_body_md)
    hero_copy_html = render_blocks_html(hero_blocks, "", "", repo_url)

    # Format H1 cleanly: "Rang | رنگ"
    if "|" in h1_clean:
        left_h, right_h = [p.strip() for p in h1_clean.split("|", 1)]
        title_html = (
            f'{html.escape(left_h)} '
            f'<span class="title-sep" aria-hidden="true">|</span> '
            f'<span class="fa" lang="fa" dir="rtl">{html.escape(right_h)}</span>'
        )
    else:
        title_html = _wrap_persian_in_html(html.escape(h1_clean))

    # Build 12-row visual pigment index (palette name + color strip jumping to each plate)
    index_rows = []
    for p in palettes:
        strips = "".join(
            f'<span style="background:{html.escape(c)}"></span>' for c in p["colors"]
        )
        index_rows.append(
            f'<a class="pigment-index-row" href="#palette-{p["slug"]}" '
            f'title="{html.escape(p["name"])}">'
            f'<span class="pigment-index-name">{html.escape(p["name"])}</span>'
            f'<span class="pigment-strip">{strips}</span></a>'
        )

    hero_html = f"""<section class="hero">
  <div class="container">
    <div class="hero-grid">
      <div class="hero-copy">
        <h1 class="hero-title">{title_html}</h1>
        {hero_copy_html}
      </div>
      <div class="hero-specimen">
        <div class="medallion-mount">
          <img class="medallion-img" src="assets/logo.png" alt="Rang pixel medallion logo" width="192" height="192">
        </div>
        <nav class="pigment-index" aria-label="Palette color index">
          {''.join(index_rows)}
        </nav>
      </div>
    </div>"""

    # Render sections in README order
    sec_html: List[str] = []
    contents_bar_html = ""

    for heading, body_md in sections:
        hid = slugify_heading(heading)
        if heading == "Contents":
            contents_bar_html = render_contents_bar(body_md, "", "", repo_url)
            continue

        if heading == "Palettes":
            before_gal, _, rest = body_md.partition(GALLERY_START)
            gal_md, _, after_gal = rest.partition(GALLERY_END)
            intro_html = (
                '<div class="section-intro">'
                + render_blocks_html(parse_blocks(before_gal.strip()), "", "", repo_url)
                + "</div>"
            )
            entries = parse_readme_gallery_entries(gal_md)
            plates: List[str] = []
            for idx, entry in enumerate(entries, start=1):
                slug = entry["slug"]
                pal = pal_by_slug.get(slug, {})
                persian = pal.get("persian", "")
                detail_href = f"palettes/{slug}/"
                if entry["detail_link"]:
                    detail_href, _ = rewrite_href(entry["detail_link"][1], "", "", repo_url)
                    detail_label = entry["detail_link"][0]
                else:
                    detail_label = "Sample plots and full details"

                img_src = rewrite_image_src(entry["image"]["src"], "", "") if entry["image"] else f"assets/palettes/{slug}/card.png"
                img_alt = entry["image"]["alt"] if entry["image"] else f"{entry['name']}, the artwork and its palette"

                prose_html_parts: List[str] = []
                for p_idx, blk in enumerate(entry["prose"]):
                    cls = "plate-citation" if p_idx == 0 else "plate-about"
                    prose_html_parts.append(
                        f'<p class="{cls}">{render_inline(blk["text"], "", "", repo_url)}</p>'
                    )

                persian_span = (
                    f'<span class="fa plate-persian" lang="fa" dir="rtl">{html.escape(persian)}</span>'
                    if persian
                    else ""
                )
                plate_colors = entry["hex_colors"] or pal.get("colors", [])
                plate_colors_attr = html.escape(",".join(plate_colors), quote=True)
                plate_bar = "".join(
                    f'<span style="background:{html.escape(c)}"></span>' for c in plate_colors
                )
                plates.append(f"""<article class="palette-plate" id="palette-{slug}" data-colors="{plate_colors_attr}">
  <div class="plate-color-bar" aria-hidden="true">{plate_bar}</div>
  <div class="plate-head">
    <div class="plate-title-group">
      <span class="plate-num">{idx:02d}</span>
      <h3 class="plate-title"><a href="{html.escape(detail_href, quote=True)}">{html.escape(entry["name"])}</a></h3>
      {persian_span}
    </div>
  </div>
  <a class="plate-frame" href="{html.escape(detail_href, quote=True)}">
    <img src="{html.escape(img_src, quote=True)}" alt="{html.escape(img_alt, quote=True)}" width="1600" height="450" loading="lazy">
  </a>
  <div class="plate-body">
    {''.join(prose_html_parts)}
    {render_hex_chips(plate_colors)}
  </div>
  <div class="plate-footer">
    <a class="plate-detail-link" href="{html.escape(detail_href, quote=True)}">
      <span>{html.escape(detail_label)}</span>{arrow_right_svg()}
    </a>
  </div>
</article>""")

            after_html = (
                '<div class="prose-col">'
                + render_blocks_html(parse_blocks(after_gal.strip()), "", "", repo_url)
                + "</div>"
                if after_gal.strip()
                else ""
            )
            sec_html.append(
                f'<section class="page-section" id="{hid}">'
                f"{section_divider_html()}"
                f'<h2 class="section-heading">{html.escape(heading)}</h2>'
                f"{intro_html}"
                f'<div class="gallery-list">{"".join(plates)}</div>'
                f"{after_html}</section>"
            )

        elif heading in ("Install", "Use the palettes"):
            sec_html.append(render_tool_subsections(hid, heading, body_md, "", "", repo_url))

        elif heading == "How palettes are made":
            inner = render_blocks_html(
                parse_blocks(body_md), "", "", repo_url, list_class="process-list"
            )
            sec_html.append(
                f'<section class="page-section" id="{hid}">'
                f"{section_divider_html()}"
                f'<h2 class="section-heading">{html.escape(heading)}</h2>'
                f"{inner}</section>"
            )

        elif heading == "Repository layout":
            blocks = parse_blocks(body_md)
            parts: List[str] = []
            for blk in blocks:
                if blk["type"] == "code":
                    rows = []
                    for line in blk["text"].splitlines():
                        if not line.strip():
                            continue
                        m_row = re.match(r"^(\S+)\s{2,}(.+)$", line)
                        if m_row:
                            rows.append(
                                '<div class="repo-row">'
                                f'<span class="repo-path">{html.escape(m_row.group(1))}</span>'
                                f'<span class="repo-desc">{html.escape(m_row.group(2))}</span>'
                                "</div>"
                            )
                    parts.append(f'<div class="repo-ledger">{"".join(rows)}</div>')
                else:
                    parts.append(render_blocks_html([blk], "", "", repo_url))
            sec_html.append(
                f'<section class="page-section" id="{hid}">'
                f"{section_divider_html()}"
                f'<h2 class="section-heading">{html.escape(heading)}</h2>'
                f"{''.join(parts)}</section>"
            )

        else:
            blocks = parse_blocks(body_md)
            has_table = any(b["type"] == "table" for b in blocks)
            body_html = render_blocks_html(blocks, "", "", repo_url)
            wrapped = body_html if has_table else f'<div class="prose-col">{body_html}</div>'
            sec_html.append(
                f'<section class="page-section" id="{hid}">'
                f"{section_divider_html()}"
                f'<h2 class="section-heading">{html.escape(heading)}</h2>'
                f"{wrapped}</section>"
            )

    hero_html += f"\n    {contents_bar_html}\n  </div>\n</section>"
    main_html = hero_html + '\n<div class="container">\n' + "\n".join(sec_html) + "\n</div>"

    return render_shell(
        title="Rang | رنگ - Persian, Iranian, and Persianate Color Palettes",
        description="Rang is a collection of color palettes drawn from Persian, Iranian, and Persianate art and culture for Python, R, ArcGIS Pro, QGIS, GeoLibre, and HEC-RAS.",
        root_prefix="",
        repo_url=repo_url,
        main_html=main_html,
        include_lightbox=False,
    )


# ------------------------------------------------------------ Palette Detail Pages

def render_zoomable_plate(
    img_src: str,
    alt_text: str,
    extra_class: str = "",
    dim_attrs: str = "",
) -> str:
    cls = f"plate-frame {extra_class}".strip()
    return (
        f'<div class="{cls}">'
        f'<button type="button" class="plate-zoom" '
        f'data-zoom-src="{html.escape(img_src, quote=True)}" '
        f'data-zoom-alt="{html.escape(alt_text, quote=True)}" '
        f'aria-label="Enlarge {html.escape(alt_text, quote=True)}">'
        f'<img src="{html.escape(img_src, quote=True)}" '
        f'alt="{html.escape(alt_text, quote=True)}"{dim_attrs} loading="lazy">'
        f'<span class="plate-zoom-hint">{zoom_svg()}<span>Enlarge</span></span>'
        "</button></div>"
    )


def build_palette_page(
    pal: dict,
    pal_index: int,
    palettes: List[dict],
    doc_text: str,
    repo_url: str,
) -> str:
    slug = pal["slug"]
    src_rel_dir = f"docs/{slug}"
    root_prefix = "../../"

    preamble, sections = split_markdown_sections(doc_text)
    preamble_blocks = parse_blocks(preamble)

    h1_text = pal["name"]
    swatch_img = None
    about_paragraphs: List[dict] = []
    for blk in preamble_blocks:
        if blk["type"] == "heading" and blk["level"] == 1:
            h1_text = blk["text"]
        elif blk["type"] == "image" and swatch_img is None:
            swatch_img = blk
        else:
            about_paragraphs.append(blk)

    # Split "Kashan (Persian: کاشان, say it kah-SHAHN)" cleanly into title + subtitle
    m_title = re.match(r"^([^(]+?)\s*\((.+)\)$", h1_text.strip())
    if m_title:
        heading_main = m_title.group(1).strip()
        subtitle_raw = m_title.group(2).strip()
        subtitle_html = f'<p class="specimen-subtitle">{_wrap_persian_in_html(html.escape(subtitle_raw))}</p>'
    else:
        heading_main = h1_text.strip()
        subtitle_html = ""

    swatch_src = (
        rewrite_image_src(swatch_img["src"], src_rel_dir, root_prefix)
        if swatch_img
        else f"{root_prefix}assets/palettes/{slug}/swatch.png"
    )
    swatch_alt = swatch_img["alt"] if swatch_img else f"{pal['name']} swatch"

    about_html = ""
    if about_paragraphs:
        about_html = (
            '<div class="specimen-about">'
            + render_blocks_html(about_paragraphs, src_rel_dir, root_prefix, repo_url)
            + "</div>"
        )

    jump_links = " ".join(
        f'<a href="#{slugify_heading(title)}">{html.escape(title)}</a>'
        for title, _ in sections
    )

    sec_html: List[str] = []
    for heading, body_md in sections:
        hid = slugify_heading(heading)
        blocks = parse_blocks(body_md)

        if heading == "Source":
            inner = render_blocks_html(blocks, src_rel_dir, root_prefix, repo_url)
            content_html = f'<div class="source-card">{inner}</div>'

        elif heading == "The setting":
            parts: List[str] = []
            for blk in blocks:
                if blk["type"] == "image":
                    img_src = rewrite_image_src(blk["src"], src_rel_dir, root_prefix)
                    dims = image_dim_attrs(blk["src"], src_rel_dir)
                    parts.append(render_zoomable_plate(img_src, blk["alt"], "setting-plate", dims))
                elif blk["type"] == "paragraph":
                    parts.append(
                        f'<p class="setting-caption">'
                        f'{render_inline(blk["text"], src_rel_dir, root_prefix, repo_url)}</p>'
                    )
                else:
                    parts.append(render_blocks_html([blk], src_rel_dir, root_prefix, repo_url))
            content_html = "\n".join(parts)

        elif heading == "Colors":
            parts = []
            for blk in blocks:
                if blk["type"] == "table":
                    parts.append(
                        render_table(
                            blk["headers"], blk["rows"],
                            src_rel_dir, root_prefix, repo_url,
                            enhance_hex_col=True,
                        )
                    )
                else:
                    parts.append(
                        f'<div class="prose-col">{render_blocks_html([blk], src_rel_dir, root_prefix, repo_url)}</div>'
                    )
            content_html = "\n".join(parts)

        elif heading in ("The palette beside the artwork", "Extraction regions", "Sample plots"):
            parts = []
            for blk in blocks:
                if blk["type"] == "image":
                    img_src = rewrite_image_src(blk["src"], src_rel_dir, root_prefix)
                    dims = image_dim_attrs(blk["src"], src_rel_dir)
                    parts.append(render_zoomable_plate(img_src, blk["alt"], dim_attrs=dims))
                else:
                    parts.append(
                        f'<div class="prose-col">{render_blocks_html([blk], src_rel_dir, root_prefix, repo_url)}</div>'
                    )
            content_html = "\n".join(parts)

        elif heading == "Use it":
            formatted_blocks: List[dict] = []
            for idx_b, blk in enumerate(blocks):
                if (
                    blk["type"] == "paragraph"
                    and blk["text"].strip() in ("Python", "R")
                    and idx_b + 1 < len(blocks)
                    and blocks[idx_b + 1]["type"] == "code"
                ):
                    formatted_blocks.append({"type": "heading", "level": 3, "text": blk["text"].strip()})
                else:
                    formatted_blocks.append(blk)
            content_html = render_blocks_html(formatted_blocks, src_rel_dir, root_prefix, repo_url)

        else:
            has_table = any(b["type"] == "table" for b in blocks)
            rendered = render_blocks_html(blocks, src_rel_dir, root_prefix, repo_url)
            content_html = rendered if has_table else f'<div class="prose-col">{rendered}</div>'

        sec_html.append(
            f'<section class="page-section" id="{hid}">'
            f"{section_divider_html()}"
            f'<h2 class="section-heading">{html.escape(heading)}</h2>'
            f"{content_html}</section>"
        )

    # Prev / Next pager
    prev_pal = palettes[(pal_index - 1) % len(palettes)]
    next_pal = palettes[(pal_index + 1) % len(palettes)]

    def pager_card(target: dict, is_next: bool) -> str:
        strips = "".join(
            f'<span style="background:{html.escape(c)}"></span>' for c in target["colors"]
        )
        dir_label = "Next palette" if is_next else "Previous palette"
        cls = "pager-card is-next" if is_next else "pager-card"
        return (
            f'<a class="{cls}" href="{root_prefix}palettes/{target["slug"]}/">'
            f'<span class="pager-dir">{dir_label}</span>'
            f'<span class="pager-name">{html.escape(target["name"])} '
            f'<span class="fa" lang="fa" dir="rtl">{html.escape(target.get("persian", ""))}</span></span>'
            f'<span class="pager-strip">{strips}</span></a>'
        )

    main_html = f"""<div class="container">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="{root_prefix}">Rang</a>
    <span aria-hidden="true">/</span>
    <a href="{root_prefix}#palettes">Palettes</a>
    <span aria-hidden="true">/</span>
    <span>{html.escape(pal["name"])}</span>
  </nav>

  <header class="specimen-header">
    <h1>{html.escape(heading_main)}</h1>
    {subtitle_html}
    <div class="plate-frame">
      <img src="{html.escape(swatch_src, quote=True)}" alt="{html.escape(swatch_alt, quote=True)}" width="1600" height="360">
    </div>
    {render_hex_chips(pal["colors"])}
    {about_html}
    <nav class="section-jump" aria-label="Palette sections">
      {jump_links}
    </nav>
  </header>

  {''.join(sec_html)}

  <nav class="palette-pager" aria-label="Palette navigation">
    {pager_card(prev_pal, is_next=False)}
    {pager_card(next_pal, is_next=True)}
  </nav>
</div>"""

    return render_shell(
        title=f"{pal['name']} ({pal.get('persian', '')}) | Rang",
        description=pal.get("about") or f"{pal['name']} color palette in Rang, {pal['source']['title']}.",
        root_prefix=root_prefix,
        repo_url=repo_url,
        main_html=main_html,
        include_lightbox=True,
        body_colors=pal["colors"],
    )


# ------------------------------------------------------------ Language & Scope Page

def build_language_page(doc_text: str, repo_url: str) -> str:
    root_prefix = "../"
    blocks = parse_blocks(doc_text)
    h1_text: Optional[str] = None
    body_blocks: List[dict] = []
    for blk in blocks:
        if blk["type"] == "heading" and blk["level"] == 1 and h1_text is None:
            h1_text = blk["text"]
        else:
            body_blocks.append(blk)
    h1_text = h1_text or "Persian, Iranian, and Persianate"

    inner = render_blocks_html(body_blocks, "docs", root_prefix, repo_url)
    main_html = f"""<div class="container">
  <nav class="breadcrumb" aria-label="Breadcrumb">
    <a href="{root_prefix}">Rang</a>
    <span aria-hidden="true">/</span>
    <span>Persian, Iranian, and Persianate</span>
  </nav>
  <article class="essay">
    <h1>{html.escape(h1_text)}</h1>
    {inner}
  </article>
</div>"""

    return render_shell(
        title="Persian, Iranian, and Persianate | Rang",
        description="A note on language and cultural scope for the Rang color palette collection.",
        root_prefix=root_prefix,
        repo_url=repo_url,
        main_html=main_html,
        include_lightbox=False,
    )


# ------------------------------------------------------------ Site Orchestrator

def build_site(output_dir: pathlib.Path, repo_url: str = DEFAULT_REPO_URL) -> dict:
    """Build the complete static site into output_dir and return a file summary."""
    output_dir = pathlib.Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy core assets
    assets_out = output_dir / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SITE_ASSETS_DIR / "style.css", assets_out / "style.css")
    shutil.copy2(SITE_ASSETS_DIR / "site.js", assets_out / "site.js")
    shutil.copy2(LOGO_PATH, assets_out / "logo.png")
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    palettes = load_all_palettes()

    # Copy palette visual plates and context photographs
    for pal in palettes:
        slug = pal["slug"]
        pal_doc_dir = DOCS_DIR / slug
        pal_assets = assets_out / "palettes" / slug
        pal_assets.mkdir(parents=True, exist_ok=True)
        for png_name in ("card.png", "swatch.png", "preview.png", "regions.png", "samples.png"):
            src_png = pal_doc_dir / png_name
            if src_png.is_file():
                shutil.copy2(src_png, pal_assets / png_name)

        ctx_rel = pal.get("source", {}).get("context_image")
        if ctx_rel:
            ctx_path = REPO_ROOT / ctx_rel
            if ctx_path.is_file():
                src_assets = assets_out / "sources" / slug
                src_assets.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ctx_path, src_assets / ctx_path.name)

    # Render landing page
    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    (output_dir / "index.html").write_text(
        build_index(readme_text, palettes, repo_url),
        encoding="utf-8",
    )

    # Render language & scope page
    lang_text = (DOCS_DIR / "language-and-scope.md").read_text(encoding="utf-8")
    lang_dir = output_dir / "language-and-scope"
    lang_dir.mkdir(parents=True, exist_ok=True)
    (lang_dir / "index.html").write_text(
        build_language_page(lang_text, repo_url),
        encoding="utf-8",
    )

    # Render each palette page
    for idx, pal in enumerate(palettes):
        slug = pal["slug"]
        doc_text = (DOCS_DIR / slug / "README.md").read_text(encoding="utf-8")
        p_out_dir = output_dir / "palettes" / slug
        p_out_dir.mkdir(parents=True, exist_ok=True)
        (p_out_dir / "index.html").write_text(
            build_palette_page(pal, idx, palettes, doc_text, repo_url),
            encoding="utf-8",
        )

    return {
        "output_dir": str(output_dir),
        "palettes": [p["name"] for p in palettes],
        "pages": 2 + len(palettes),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--repo-url",
        default=DEFAULT_REPO_URL,
        help=f"GitHub repository base URL (default: {DEFAULT_REPO_URL})",
    )
    args = parser.parse_args()
    summary = build_site(args.output, repo_url=args.repo_url)
    print(f"Built {summary['pages']} pages ({len(summary['palettes'])} palettes) -> {summary['output_dir']}")


if __name__ == "__main__":
    main()
