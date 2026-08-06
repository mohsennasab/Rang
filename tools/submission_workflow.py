"""Build a reviewable Rang submission package from a workflow ZIP.

Created by Mohsen Tahmasebi Nasab, PhD
https://hydromohsen.com

Copyright (c) 2026 Mohsen Tahmasebi Nasab
Licensed under the MIT License in the repository root.
"""
import json
import pathlib
import re
import shutil
import zipfile
from xml.sax.saxutils import escape

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps

import make_hecras_ramp
import make_preview
import make_samples
import make_stylx
from colorlib import (COLORBLIND_THRESHOLD, VISION_LABELS, VISION_TYPES,
                      discrete_subset, hex_to_rgb, interpolate,
                      pairwise_min_mean, worst_case)
from notebook_workflow import (palette_slug, read_json, verify_recipe,
                               write_json)


KNOWN_REVIEW_FILES = (
    "regions.png",
    "candidates.json",
    "candidates.png",
    "adjustments.png",
    "check-report.json",
)

PALETTE_PLACEHOLDERS = {
    "name": "YourPalette",
    "persian": "نام فارسی",
    "pronunciation": "how to say it",
    "about": "A short, personal description of the palette",
}

SOURCE_PLACEHOLDERS = {
    "title": "Artwork title",
    "artist": "Artist when known",
    "date": "Date",
    "geography": "Place",
    "medium": "Materials",
    "museum": "Museum or collection",
    "accession": "Accession number",
    "credit": "Credit line",
    "url": "OBJECT PAGE URL",
    "image": "SOURCE IMAGE URL",
}


def _safe_extract(archive_path, output_dir):
    """Extract a workflow ZIP without accepting nested or unsafe paths."""
    archive_path = pathlib.Path(archive_path)
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        total_size = sum(member.file_size for member in members)
        if total_size > 250 * 1024 * 1024:
            raise ValueError("The workflow ZIP expands beyond 250 MB")
        for member in members:
            path = pathlib.PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
                raise ValueError(
                    f'The workflow ZIP contains an unsafe path: "{member.filename}"'
                )
            if member.is_dir():
                continue
            target = output_dir / path.name
            with archive.open(member) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)


def load_workflow_archive(archive_path, output_dir):
    """Extract one completed workflow and locate its required files."""
    output_dir = pathlib.Path(output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    _safe_extract(archive_path, output_dir)
    recipes = sorted(output_dir.glob("*-recipe.json"))
    palettes = sorted(output_dir.glob("*-palette.json"))
    if len(recipes) != 1:
        raise ValueError(
            f"The workflow ZIP needs exactly one *-recipe.json file. Found {len(recipes)}"
        )
    if len(palettes) != 1:
        raise ValueError(
            f"The workflow ZIP needs exactly one *-palette.json file. Found {len(palettes)}"
        )
    recipe = read_json(recipes[0])
    source_name = pathlib.Path(str(recipe.get("source", {}).get("image", ""))).name
    source_path = output_dir / source_name
    if not source_name or not source_path.is_file():
        raise ValueError(
            "The workflow ZIP is missing the source image recorded by the recipe"
        )
    try:
        with Image.open(source_path) as image:
            image.verify()
    except Exception as error:
        raise ValueError("The source image in the workflow ZIP cannot be opened") from error
    return {
        "archive": pathlib.Path(archive_path),
        "work_dir": output_dir,
        "recipe_path": recipes[0],
        "palette_path": palettes[0],
        "source_path": source_path,
        "recipe": recipe,
        "palette": read_json(palettes[0]),
    }


def apply_metadata_updates(bundle, updates):
    """Apply builder edits while recovering values already known by the recipe."""
    if not isinstance(updates, dict):
        raise ValueError("METADATA_UPDATES must be a dictionary")
    allowed_palette = {"name", "persian", "pronunciation", "about"}
    allowed_source = {
        "title", "artist", "date", "geography", "medium", "museum", "site",
        "department", "accession", "credit", "url", "image", "download_url",
        "reference_label", "rights", "public_domain", "preserve_aspect",
    }
    unknown_palette = set(updates) - allowed_palette - {"source"}
    if unknown_palette:
        raise ValueError(
            "METADATA_UPDATES has unknown palette fields: "
            + ", ".join(sorted(unknown_palette))
        )
    source_updates = updates.get("source", {})
    if not isinstance(source_updates, dict):
        raise ValueError('METADATA_UPDATES["source"] must be a dictionary')
    unknown_source = set(source_updates) - allowed_source
    if unknown_source:
        raise ValueError(
            "METADATA_UPDATES source has unknown fields: "
            + ", ".join(sorted(unknown_source))
        )

    palette = json.loads(json.dumps(bundle["palette"]))
    source = palette.setdefault("source", {})
    recipe = bundle["recipe"]

    if (not palette.get("name")
            or palette.get("name") == PALETTE_PLACEHOLDERS["name"]):
        palette["name"] = recipe.get("palette", "")
    reference = recipe.get("source", {}).get("reference", "")
    if (not source.get("url") or source.get("url") == SOURCE_PLACEHOLDERS["url"]):
        if isinstance(reference, str) and reference.startswith("https://"):
            source["url"] = reference
    if (not source.get("image")
            or source.get("image") == SOURCE_PLACEHOLDERS["image"]):
        slug = palette_slug(palette.get("name", recipe.get("palette", "palette")))
        suffix = bundle["source_path"].suffix.lower() or ".jpg"
        source["image"] = f"sources/{slug}/source{suffix}"

    for key, value in updates.items():
        if key == "source":
            continue
        if value is None:
            continue
        if not isinstance(value, str):
            raise ValueError(f"METADATA_UPDATES {key} must be text")
        if value.strip():
            palette[key] = value.strip()
    for key, value in source_updates.items():
        if value is None:
            continue
        if key in {"public_domain", "preserve_aspect"}:
            if not isinstance(value, bool):
                raise ValueError(f"source.{key} must be True, False, or None")
            source[key] = value
        else:
            if not isinstance(value, str):
                raise ValueError(f"source.{key} must be text")
            if value.strip():
                source[key] = value.strip()

    for key, placeholder in PALETTE_PLACEHOLDERS.items():
        if palette.get(key) == placeholder:
            palette.pop(key)
    for key, placeholder in SOURCE_PLACEHOLDERS.items():
        if source.get(key) == placeholder:
            source.pop(key)

    write_json(bundle["palette_path"], palette)
    bundle["palette"] = palette
    return bundle


def validate_submission_input(bundle):
    """Return clear problems that must be fixed before packaging."""
    recipe = bundle["recipe"]
    palette = bundle["palette"]
    problems = []
    name = palette.get("name")
    if (not isinstance(name, str) or not name.strip()
            or name == PALETTE_PLACEHOLDERS["name"]):
        problems.append("Palette name is missing or still uses YourPalette")
    elif not re.fullmatch(r"[A-Z][A-Za-z]*", name):
        problems.append("Palette name must be one capitalized ASCII word")
    for field in ("persian", "pronunciation"):
        value = palette.get(field)
        if (not isinstance(value, str) or not value.strip()
                or value == PALETTE_PLACEHOLDERS[field]):
            problems.append(f"Palette field {field} is missing or still uses placeholder text")
    if recipe.get("palette") != name:
        problems.append("The palette name does not match PALETTE_NAME from notebook 1")
    if palette.get("about") == PALETTE_PLACEHOLDERS["about"]:
        problems.append("Palette field about still uses placeholder text")
    colors = palette.get("colors")
    if not isinstance(colors, list) or not 5 <= len(colors) <= 12:
        problems.append("Palette colors must contain between 5 and 12 entries")
        colors = []
    for number, color in enumerate(colors, start=1):
        if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            problems.append(f"Palette color {number} is not a six-digit hex color")
    if len({str(color).lower() for color in colors}) != len(colors):
        problems.append("Palette colors must be unique")
    if colors != recipe.get("expected", {}).get("colors", []):
        problems.append("Palette colors do not match the verified recipe colors")
    notes = palette.get("notes")
    if not isinstance(notes, list) or len(notes) != len(colors):
        problems.append("Palette needs one source note for every color")
    elif any(not isinstance(note, str) or not note.strip() for note in notes):
        problems.append("Every palette color needs a specific source note")
    order = palette.get("order")
    if not isinstance(order, list) or sorted(order) != list(range(1, len(colors) + 1)):
        problems.append("Palette order must use every number from 1 to the color count")
    source = palette.get("source")
    if not isinstance(source, dict):
        problems.append("Palette metadata is missing the source record")
        source = {}
    for field in ("title", "date", "geography", "medium", "url", "image"):
        value = source.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"Source field {field} is missing")
        elif value == SOURCE_PLACEHOLDERS[field]:
            problems.append(f"Source field {field} still uses placeholder text")
    url = str(source.get("url", ""))
    if url and not url.startswith("https://"):
        problems.append("Source field url must use an HTTPS address")
    image_value = str(source.get("image", ""))
    image_path = pathlib.PurePosixPath(image_value.replace("\\", "/"))
    if (image_value and not image_value.startswith("https://")
            and (image_path.is_absolute() or ".." in image_path.parts)):
        problems.append("Source field image must use HTTPS or a safe relative path")
    if not isinstance(source.get("public_domain"), bool):
        problems.append("source.public_domain must be true or false")
    if source.get("public_domain") is False:
        for field in ("credit", "rights"):
            value = source.get(field)
            if (not isinstance(value, str) or not value.strip()
                    or value == SOURCE_PLACEHOLDERS.get(field)):
                problems.append(f"A non-public-domain source needs source.{field}")
    elif source.get("public_domain") is True:
        for field in ("museum", "accession"):
            value = source.get(field)
            if (not isinstance(value, str) or not value.strip()
                    or value == SOURCE_PLACEHOLDERS[field]):
                problems.append(f"A public-domain museum source needs source.{field}")
    if not (bundle["work_dir"] / "check-report.json").is_file():
        problems.append("The workflow ZIP is missing check-report.json from step 05")
    return problems


def validate_proposal_details(why_this_work, maintainer_notes):
    """Check the short contributor-written proposal fields."""
    if not isinstance(why_this_work, str) or not why_this_work.strip():
        raise ValueError(
            "WHY_THIS_WORK is empty. Write one or two sentences about the artwork and palette"
        )
    if not isinstance(maintainer_notes, str):
        raise ValueError("MAINTAINER_NOTES must be text. Use an empty string when none")


def _rgb_ints(hexcode):
    return tuple(int(value) for value in hex_to_rgb(hexcode))


def _qgis_ramp(name, colors, discrete):
    count = len(colors)
    if discrete:
        positions = [(index / count, colors[index])
                     for index in range(1, count)]
    else:
        positions = [(index / (count - 1), colors[index])
                     for index in range(1, count - 1)]
    stops = ":".join(
        "{};{},{},{},255".format(round(position, 6), *_rgb_ints(color))
        for position, color in positions
    )
    first = "{},{},{},255".format(*_rgb_ints(colors[0]))
    last = "{},{},{},255".format(*_rgb_ints(colors[-1]))
    return "\n".join([
        f'    <colorramp type="gradient" name="{escape(name)}" tags="Rang">',
        f'      <prop k="color1" v="{first}"/>',
        f'      <prop k="color2" v="{last}"/>',
        f'      <prop k="discrete" v="{1 if discrete else 0}"/>',
        '      <prop k="rampType" v="gradient"/>',
        f'      <prop k="stops" v="{stops}"/>',
        "    </colorramp>",
    ])


def _write_qgis(palette, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    name = palette["name"]
    colors = palette["colors"]
    ramps = [
        _qgis_ramp(name, colors, False),
        _qgis_ramp(f"{name} discrete", colors, True),
    ]
    xml = "\n".join([
        "<!DOCTYPE qgis_style>",
        '<qgis_style version="2">',
        "  <symbols/>",
        "  <colorramps>",
        *ramps,
        "  </colorramps>",
        "</qgis_style>",
        "",
    ])
    xml_path = output_dir / f"Rang-{name}.xml"
    xml_path.write_text(xml, encoding="utf-8")
    gpl = ["GIMP Palette", f"Name: Rang {name}", "Columns: 0", "#"]
    for number, color in enumerate(colors, start=1):
        red, green, blue = _rgb_ints(color)
        gpl.append(f"{red:3d} {green:3d} {blue:3d} {name} {number}")
    gpl_path = output_dir / f"{name}.gpl"
    gpl_path.write_text("\n".join(gpl) + "\n", encoding="utf-8")
    return xml_path, gpl_path


def _geolibre_payload(palette):
    colors = palette["colors"]
    order = palette["order"]
    categories = {
        str(number): discrete_subset(colors, order, number)
        for number in range(2, len(colors) + 1)
    }
    graduated = {
        str(number): interpolate(colors, number)
        for number in range(2, 13)
    }
    return {
        "format": "rang-geolibre-colors",
        "version": 1,
        "license": "CC0-1.0",
        "palettes": {
            palette["name"]: {
                "raster_anchors": colors,
                "graduated": graduated,
                "categorical": categories,
            }
        },
    }


def _write_geolibre(palette, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    name = palette["name"]
    payload = _geolibre_payload(palette)
    json_path = output_dir / f"Rang-{name}.json"
    write_json(json_path, payload)
    entry = payload["palettes"][name]
    lines = [
        f"Rang - {name}",
        "",
        "Raster anchors",
        ", ".join(entry["raster_anchors"]),
        "",
    ]
    for number, colors in entry["graduated"].items():
        lines.append(f'Graduated {number}: {", ".join(colors)}')
    lines.append("")
    for number, colors in entry["categorical"].items():
        lines.append(f'Categorical {number}: {", ".join(colors)}')
    text_path = output_dir / f"Rang-{name}.txt"
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, text_path


def _save_source_card(source_path, output):
    image = ImageOps.exif_transpose(Image.open(source_path)).convert("RGB")
    image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, quality=90, optimize=True)


def _write_images(palette, source_path, docs_dir, source_card):
    render_palette = json.loads(json.dumps(palette))
    render_palette["source"]["image"] = str(source_path)
    render_palette["source"]["card_image"] = str(source_card)
    docs_dir.mkdir(parents=True, exist_ok=True)
    make_preview.make_swatch(render_palette, docs_dir / "swatch.png")
    make_preview.make_card(render_palette, docs_dir / "card.png")
    make_preview.make_preview(render_palette, docs_dir / "preview.png")
    figure = make_samples.standard_page(
        render_palette, np.random.default_rng(make_samples.SEED), None
    )
    figure.savefig(docs_dir / "samples.png", facecolor="white",
                   metadata={"Software": "Rang"})
    plt.close(figure)


def _source_text(source):
    parts = [f'{source["title"]}, {source["date"]}.']
    if source.get("artist"):
        parts.append(f'{source["artist"]}.')
    if source.get("geography"):
        parts.append(f'{source["geography"]}.')
    if source.get("medium"):
        parts.append(f'{source["medium"]}.')
    holder = source.get("museum") or source.get("site")
    if holder:
        parts.append(f"{holder}.")
    if source.get("credit"):
        parts.append(f'{source["credit"]}.')
    if source.get("public_domain"):
        parts.append(
            f'[Object page]({source["url"]}) and '
            f'[source image]({source["image"]}), listed as public domain or open access.'
        )
    else:
        parts.append(f'[Object page]({source["url"]}). {source["rights"]}')
    return "\n\n".join(parts)


def _docs_page(palette, report):
    name = palette["name"]
    heading = name
    labels = []
    if palette.get("persian"):
        labels.append(f'Persian: {palette["persian"]}')
    if palette.get("pronunciation"):
        labels.append(f'say it {palette["pronunciation"]}')
    if labels:
        heading += f' ({", ".join(labels)})'
    rows = [
        "| position | hex | drawn from | nearest sample |",
        "|---|---|---|---|",
    ]
    presence = report["source_presence"]
    for number, (color, note) in enumerate(
            zip(palette["colors"], palette["notes"]), start=1):
        nearest = presence.get(color, {}).get("nearest", "")
        rows.append(f"| {number} | `{color}` | {note} | {nearest} |")
    cvd = ["| vision | min CIEDE2000 | mean |", "|---|---|---|"]
    for kind in VISION_TYPES:
        minimum, mean = pairwise_min_mean(palette["colors"], kind)
        cvd.append(f"| {VISION_LABELS[kind]} | {minimum:.1f} | {mean:.1f} |")
    lowest = worst_case(palette["colors"])
    separation = (
        f"The lowest separation is {lowest:.1f}. Rang uses {COLORBLIND_THRESHOLD:.0f} "
        "as a practical review point. Check the finished figure when color "
        "distinction matters."
    )
    optional = []
    if palette.get("about"):
        optional.append(palette["about"])
    for title, key in (("The story", "story"), ("The craft", "craft")):
        value = palette.get(key)
        if value:
            paragraphs = value if isinstance(value, list) else [value]
            optional.append(f'## {title}\n\n' + "\n\n".join(paragraphs))
    optional_text = "\n\n".join(optional)
    return f"""# {heading}

![{name} swatch](swatch.png)

{optional_text}

## Source

{_source_text(palette["source"])}

## Colors

{chr(10).join(rows)}

Lower nearest-sample values indicate a closer match to the uploaded artwork.

## The palette beside the artwork

![{name} preview](preview.png)

## Sample plots

![{name} samples](samples.png)

These proposal samples use the standard offline test fields. The repository
build recreates them with the shared Rang data.

## Separation and color vision

{chr(10).join(cvd)}

{separation}

## Use it

Python

```python
import rang
rang.rang("{name}", 5)
rang.cmap("{name}")
```

R

```r
library(Rang)
rang("{name}", 5)
```

The proposal package also contains palette-specific files for ArcGIS Pro,
QGIS, HEC-RAS, and GeoLibre. The maintainer will regenerate the combined Rang
files before merging.
"""


def _usage_examples(palette, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    name = palette["name"]
    (output_dir / f"{palette_slug(name)}_python.py").write_text(
        f'"""Try the proposed {name} palette."""\n'
        'import rang\n\n'
        f'colors = rang.rang("{name}", 5)\n'
        f'cmap = rang.cmap("{name}")\n',
        encoding="utf-8",
    )
    (output_dir / f"{palette_slug(name)}_r.R").write_text(
        f'# Try the proposed {name} palette\nlibrary(Rang)\n\n'
        f'colors <- rang("{name}", 5)\n',
        encoding="utf-8",
    )


def _pull_request_text(palette, report, why_this_work, maintainer_notes):
    name = palette["name"]
    source = palette["source"]
    checks = [
        f'{color}: nearest {values["nearest"]:.1f}, '
        f'{values["share_within_8"]:.2f}% within 8'
        for color, values in report["source_presence"].items()
    ]
    notes = maintainer_notes.strip() or "No additional notes."
    return f"""# New palette

- Palette name: {name}
- Object page: {source["url"]}
- Why this work: {why_this_work.strip()}

## Checklist

- [x] Photo reuse status and exact license are recorded in `source.public_domain` and `source.rights` when needed
- [x] `palettes/{palette_slug(name)}.json` has the required fields and one note per color
- [x] The saved recipe replayed successfully
- [ ] Run `python tools/check_palette.py --palette {palette_slug(name)}` after copying the proposal into the repository
- [ ] Run `python tools/build.py {palette_slug(name)}` and commit the combined generated files
- [ ] Read the sample page and inspect all four viewing rows in the preview

## Workflow check output

```text
verified: True
color vision flag: {report["colorblind"]}
{chr(10).join(checks)}
```

## Notes

{notes}
"""


def _manifest_text(palette):
    name = palette["name"]
    slug = palette_slug(name)
    return f"""# {name} submission package

This package was prepared from the verified Rang notebook workflow.

Workflow created by Mohsen Tahmasebi Nasab, PhD,
[hydromohsen.com](https://hydromohsen.com). Notebook and tool code follow the
Rang MIT License. Palette data follows the Rang CC0 dedication. The source
image keeps the rights recorded in the palette file.

## Repository-ready files

- `repository/palettes/{slug}.json`
- `repository/recipes/{slug}.json`
- `repository/sources/{slug}/` with the gallery card and a local source copy when needed
- `repository/docs/{slug}/` with the page and four preview images

Copy these files into the matching folders in a local Rang checkout. Then run:

```text
python tools/check_palette.py --palette {slug}
python tools/build.py {slug}
```

The build command updates the shared Python, R, ArcGIS Pro, QGIS, HEC-RAS,
GeoLibre, documentation, and gallery files.

## Palette-specific review files

The `software` folder lets reviewers test this palette before it enters the
combined collection. Do not copy these one-palette files over the repository's
combined files.

- `software/arcgis/Rang-{name}.stylx`
- `software/qgis/Rang-{name}.xml` and `{name}.gpl`
- `software/hecras/Rang-{name}.xml`
- `software/geolibre/Rang-{name}.json` and `Rang-{name}.txt`
- `software/examples/` with Python and R examples

The `review` folder contains the extraction figures, report, and source image.
Use `PULL_REQUEST.md` as the starting description for the contribution.
"""


def _zip_tree(folder, archive_path):
    folder = pathlib.Path(folder)
    archive_path = pathlib.Path(archive_path)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(folder))
    return archive_path


def build_submission(bundle, output_base, why_this_work, maintainer_notes=""):
    """Create repository files, review files, software tests, and one ZIP."""
    validate_proposal_details(why_this_work, maintainer_notes)
    problems = validate_submission_input(bundle)
    if problems:
        raise ValueError("Fix these workflow fields:\n- " + "\n- ".join(problems))
    verification = verify_recipe(bundle["recipe_path"], bundle["work_dir"])
    if not verification["verified"]:
        raise ValueError("Notebook 1 recipe verification failed. Return to notebook 1")

    palette = json.loads(json.dumps(bundle["palette"]))
    name = palette["name"]
    slug = palette_slug(name)
    root = pathlib.Path(output_base) / f"{slug}-submission"
    if root.exists():
        shutil.rmtree(root)
    repository = root / "repository"
    docs_dir = repository / "docs" / slug
    source_card = repository / "sources" / slug / "card.jpg"
    review = root / "review"
    software = root / "software"
    for folder in (docs_dir, source_card.parent, review, software):
        folder.mkdir(parents=True, exist_ok=True)

    _save_source_card(bundle["source_path"], source_card)
    palette["source"]["card_image"] = f"sources/{slug}/card.jpg"
    source_asset = None
    if not str(palette["source"]["image"]).startswith("https://"):
        suffix = bundle["source_path"].suffix.lower() or ".jpg"
        source_asset = source_card.parent / f"source{suffix}"
        shutil.copy2(bundle["source_path"], source_asset)
        palette["source"]["image"] = f"sources/{slug}/{source_asset.name}"
    palette_path = repository / "palettes" / f"{slug}.json"
    write_json(palette_path, palette)
    recipe_path = repository / "recipes" / f"{slug}.json"
    recipe_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundle["recipe_path"], recipe_path)

    _write_images(palette, bundle["source_path"], docs_dir, source_card)
    report = read_json(bundle["work_dir"] / "check-report.json")
    (docs_dir / "README.md").write_text(
        _docs_page(palette, report), encoding="utf-8"
    )

    arcgis_dir = software / "arcgis"
    arcgis_dir.mkdir(parents=True, exist_ok=True)
    if not make_stylx.write_stylx([palette], arcgis_dir / f"Rang-{name}.stylx"):
        raise ValueError("The ArcGIS proposal style could not be written")
    qgis_files = _write_qgis(palette, software / "qgis")
    hecras_dir = software / "hecras"
    hecras_dir.mkdir(parents=True, exist_ok=True)
    hecras_path = hecras_dir / f"Rang-{name}.xml"
    hecras_path.write_text(
        make_hecras_ramp.custom_color_ramps([palette]), encoding="utf-8"
    )
    geolibre_files = _write_geolibre(palette, software / "geolibre")
    _usage_examples(palette, software / "examples")

    for filename in KNOWN_REVIEW_FILES:
        source = bundle["work_dir"] / filename
        if source.is_file():
            shutil.copy2(source, review / filename)
    shutil.copy2(bundle["source_path"], review / bundle["source_path"].name)
    (root / "PULL_REQUEST.md").write_text(
        _pull_request_text(palette, report, why_this_work, maintainer_notes),
        encoding="utf-8",
    )
    (root / "README.md").write_text(_manifest_text(palette), encoding="utf-8")

    archive = pathlib.Path(output_base) / f"{slug}-submission.zip"
    _zip_tree(root, archive)
    repository_files = [palette_path, recipe_path, source_card, docs_dir]
    if source_asset is not None:
        repository_files.append(source_asset)
    return {
        "root": root,
        "archive": archive,
        "palette": palette,
        "report": report,
        "verification": verification,
        "repository_files": repository_files,
        "software_files": [
            arcgis_dir / f"Rang-{name}.stylx",
            *qgis_files,
            hecras_path,
            *geolibre_files,
        ],
    }
