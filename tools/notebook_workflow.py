"""Shared functions for the numbered Rang contribution notebooks.

Created by Mohsen Tahmasebi Nasab, PhD
https://hydromohsen.com

Copyright (c) 2026 Mohsen Tahmasebi Nasab
Licensed under the MIT License in the repository root.
"""
import base64
import hashlib
import io
import json
import pathlib
import platform
import re
import urllib.parse
import urllib.request
import zipfile

import matplotlib.pyplot as plt
import numpy as np
import PIL
import sklearn
from matplotlib.patches import Rectangle
from PIL import Image, ImageOps
from sklearn.cluster import KMeans

from adjust_colors import apply_edit
from colorlib import (COLORBLIND_THRESHOLD, VISION_LABELS, VISION_TYPES,
                      greedy_order, hex_to_rgb, lab_to_rgb, pairwise_min_mean,
                      presence_in_image, rgb_to_hex, rgb_to_lab, worst_case)

CREATOR = "Mohsen Tahmasebi Nasab, PhD"
WEBSITE = "https://hydromohsen.com"
LICENSE_HOLDER = "Mohsen Tahmasebi Nasab"
RECIPE_VERSION = 1


def use_arial():
    """Use Arial when installed and a close open fallback in Colab."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Liberation Sans", "DejaVu Sans"],
        "figure.dpi": 120,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def palette_slug(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not slug:
        raise ValueError("palette name must contain a letter or number")
    return slug


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


def make_workflow_archive(recipe_path, work_dir, archive_path):
    """Bundle only the source and known workflow outputs."""
    recipe_path = pathlib.Path(recipe_path)
    work_dir = pathlib.Path(work_dir)
    archive_path = pathlib.Path(archive_path)
    recipe = read_json(recipe_path)

    source_name = pathlib.Path(recipe["source"]["image"]).name
    if not source_name or source_name != recipe["source"]["image"]:
        raise ValueError("the recipe source must be a filename in the workflow folder")

    prefix = recipe_path.name.removesuffix("-recipe.json")
    allowed_names = {
        recipe_path.name,
        source_name,
        "regions.png",
        "candidates.json",
        "candidates.png",
        "adjustments.png",
        "check-report.json",
        f"{prefix}-palette.json",
    }
    members = [work_dir / name for name in sorted(allowed_names)
               if (work_dir / name).is_file()]
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for member in members:
            archive.write(member, member.name)
    return archive_path


def _source_suffix(source):
    suffix = pathlib.Path(urllib.parse.urlparse(str(source)).path).suffix.lower()
    return suffix if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff"} else ".img"


def obtain_source(source, work_dir):
    """Return a local source path, downloading an HTTPS image when needed."""
    work_dir = pathlib.Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    source = str(source)
    if source.startswith("http://"):
        raise ValueError("remote source images must use HTTPS")
    if source.startswith("https://"):
        path = work_dir / f"source{_source_suffix(source)}"
        if not path.exists():
            request = urllib.request.Request(source, headers={"User-Agent": "Rang/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read(100 * 1024 * 1024 + 1)
            if len(data) > 100 * 1024 * 1024:
                raise ValueError("source image is larger than 100 MB")
            path.write_bytes(data)
        return path
    path = pathlib.Path(source).expanduser()
    if not path.is_absolute():
        path = pathlib.Path(work_dir) / path
    if not path.exists():
        raise FileNotFoundError(f"source image was not found: {source}")
    return path.resolve()


def image_sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def open_rgb(path):
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def show_source(path, title="Source image"):
    use_arial()
    image = open_rgb(path)
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.imshow(image)
    ax.set_title(f"{title}, {image.width} x {image.height} pixels")
    ax.set_xlabel("x coordinate in pixels")
    ax.set_ylabel("y coordinate in pixels")
    ax.grid(color="white", linewidth=0.5, alpha=0.35)
    fig.tight_layout()
    return fig


def draw_regions_interactively(path, initial_regions=None, maximum_size=(1000, 850)):
    """Draw and describe rectangular regions on an image in Google Colab."""
    try:
        from google.colab.output import eval_js
        from IPython.display import Javascript, display
    except ImportError as error:
        raise RuntimeError(
            "interactive region drawing is available in Google Colab"
        ) from error

    image = open_rgb(path)
    preview = image.copy()
    preview.thumbnail(maximum_size, Image.Resampling.LANCZOS)
    stream = io.BytesIO()
    preview.save(stream, format="JPEG", quality=90, optimize=True)
    data_url = "data:image/jpeg;base64," + base64.b64encode(
        stream.getvalue()).decode("ascii")

    starting = []
    for number, region in enumerate(initial_regions or [], start=1):
        starting.append({
            "id": str(region.get("id", f"region-{number:02d}")),
            "label": str(region.get("label", f"Region {number}")),
            "box": [int(value) for value in region["box"]],
            "k": int(region.get("k", 8)),
            "note": str(region.get("note", "")),
        })

    payload = {
        "image": data_url,
        "imageWidth": image.width,
        "imageHeight": image.height,
        "previewWidth": preview.width,
        "previewHeight": preview.height,
        "regions": starting,
    }
    script = r'''
async function rangDrawRegions(input) {
  return await new Promise((resolve) => {
  if (google.colab.output.setIframeHeight) {
    google.colab.output.setIframeHeight(0, true, {maxHeight: 5000})
  }
  const colors = ['#d73027', '#4575b4', '#1a9850', '#984ea3', '#ff7f00',
                  '#00a6a6', '#a65628', '#f781bf', '#4d4d4d', '#66c2a5']
  const root = document.createElement('div')
  root.style.cssText = 'font-family:Arial,sans-serif;max-width:1050px;padding:12px;background:white;border:1px solid #d5d5d5;border-radius:8px'
  const help = document.createElement('p')
  help.textContent = 'Drag across the image to draw a region. Use the fields below the image to name it and choose k.'
  root.appendChild(help)

  const canvas = document.createElement('canvas')
  canvas.width = input.previewWidth
  canvas.height = input.previewHeight
  canvas.style.cssText = 'display:block;max-width:100%;height:auto;border:1px solid #777;cursor:crosshair;touch-action:none'
  root.appendChild(canvas)
  const context = canvas.getContext('2d')

  const controls = document.createElement('div')
  controls.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;margin:10px 0'
  const undo = document.createElement('button')
  undo.textContent = 'Undo last box'
  const clear = document.createElement('button')
  clear.textContent = 'Clear all'
  const finish = document.createElement('button')
  finish.textContent = 'Use these regions'
  finish.style.cssText = 'background:#146c43;color:white;border:0;border-radius:4px;padding:7px 12px;font-weight:bold'
  controls.append(undo, clear, finish)
  root.appendChild(controls)

  const status = document.createElement('div')
  status.style.cssText = 'min-height:24px;color:#8b1a1a;font-weight:bold'
  root.appendChild(status)
  const list = document.createElement('div')
  root.appendChild(list)
  document.body.appendChild(root)

  const image = new Image()
  let drawing = false
  let start = null
  let current = null
  let regions = input.regions.map((region) => ({
    id: region.id,
    label: region.label,
    k: region.k,
    note: region.note,
    box: [
      region.box[0] * input.previewWidth / input.imageWidth,
      region.box[1] * input.previewHeight / input.imageHeight,
      region.box[2] * input.previewWidth / input.imageWidth,
      region.box[3] * input.previewHeight / input.imageHeight
    ]
  }))

  function point(event) {
    const bounds = canvas.getBoundingClientRect()
    return [
      (event.clientX - bounds.left) * canvas.width / bounds.width,
      (event.clientY - bounds.top) * canvas.height / bounds.height
    ]
  }

  function redraw() {
    context.clearRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
    regions.forEach((region, index) => {
      const box = region.box
      const color = colors[index % colors.length]
      context.strokeStyle = color
      context.lineWidth = 3
      context.strokeRect(box[0], box[1], box[2] - box[0], box[3] - box[1])
      context.fillStyle = color
      context.fillRect(box[0], box[1], 28, 24)
      context.fillStyle = 'white'
      context.font = 'bold 15px Arial'
      context.fillText(String(index + 1), box[0] + 8, box[1] + 17)
    })
    if (drawing && start && current) {
      context.strokeStyle = '#111'
      context.lineWidth = 2
      context.setLineDash([7, 5])
      context.strokeRect(start[0], start[1], current[0] - start[0], current[1] - start[1])
      context.setLineDash([])
    }
  }

  function field(value, width, type='text') {
    const element = document.createElement('input')
    element.type = type
    element.value = value
    element.style.width = width
    element.style.padding = '5px'
    return element
  }

  function refreshList() {
    list.innerHTML = ''
    regions.forEach((region, index) => {
      const row = document.createElement('div')
      row.style.cssText = 'display:grid;grid-template-columns:28px minmax(110px,1fr) minmax(130px,1.5fr) 65px minmax(150px,2fr) auto;gap:7px;align-items:center;margin:7px 0'
      const number = document.createElement('strong')
      number.textContent = String(index + 1)
      number.style.color = colors[index % colors.length]
      const id = field(region.id, '100%')
      const label = field(region.label, '100%')
      const k = field(region.k, '100%', 'number')
      k.min = 2
      k.max = 20
      const note = field(region.note, '100%')
      const remove = document.createElement('button')
      remove.textContent = 'Delete'
      id.setAttribute('aria-label', `Region ${index + 1} ID`)
      label.setAttribute('aria-label', `Region ${index + 1} name`)
      k.setAttribute('aria-label', `Region ${index + 1} k value`)
      note.setAttribute('aria-label', `Region ${index + 1} note`)
      id.oninput = () => { region.id = id.value }
      label.oninput = () => { region.label = label.value }
      k.oninput = () => { region.k = Number(k.value) }
      note.oninput = () => { region.note = note.value }
      remove.onclick = () => {
        regions.splice(index, 1)
        refreshList()
        redraw()
      }
      row.append(number, id, label, k, note, remove)
      list.appendChild(row)
    })
    if (regions.length) {
      const headings = document.createElement('div')
      headings.style.cssText = 'display:grid;grid-template-columns:28px minmax(110px,1fr) minmax(130px,1.5fr) 65px minmax(150px,2fr) auto;gap:7px;font-size:12px;color:#555;margin-top:10px'
      ;['', 'ID', 'Name', 'k', 'Note', ''].forEach((value) => {
        const item = document.createElement('span')
        item.textContent = value
        headings.appendChild(item)
      })
      list.prepend(headings)
    }
  }

  canvas.onpointerdown = (event) => {
    event.preventDefault()
    drawing = true
    start = point(event)
    current = start
    canvas.setPointerCapture(event.pointerId)
    redraw()
  }
  canvas.onpointermove = (event) => {
    if (!drawing) return
    current = point(event)
    redraw()
  }
  canvas.onpointerup = (event) => {
    if (!drawing) return
    current = point(event)
    drawing = false
    const x0 = Math.max(0, Math.min(start[0], current[0]))
    const y0 = Math.max(0, Math.min(start[1], current[1]))
    const x1 = Math.min(canvas.width, Math.max(start[0], current[0]))
    const y1 = Math.min(canvas.height, Math.max(start[1], current[1]))
    if (x1 - x0 >= 6 && y1 - y0 >= 6) {
      const number = regions.length + 1
      regions.push({
        id: `region-${String(number).padStart(2, '0')}`,
        label: `Region ${number}`,
        k: 8,
        note: '',
        box: [x0, y0, x1, y1]
      })
      status.textContent = ''
      refreshList()
    }
    start = null
    current = null
    redraw()
  }
  undo.onclick = () => {
    regions.pop()
    refreshList()
    redraw()
  }
  clear.onclick = () => {
    regions = []
    refreshList()
    redraw()
  }
  finish.onclick = () => {
    status.textContent = ''
    if (!regions.length) {
      status.textContent = 'Draw at least one region.'
      return
    }
    const ids = new Set()
    for (const region of regions) {
      if (!/^[a-z][a-z0-9-]*$/.test(region.id)) {
        status.textContent = `Use lowercase letters, numbers, and hyphens for the ID: ${region.id}`
        return
      }
      if (ids.has(region.id)) {
        status.textContent = `Each region needs a different ID: ${region.id}`
        return
      }
      ids.add(region.id)
      if (!region.label.trim()) {
        status.textContent = `Give ${region.id} a name.`
        return
      }
      if (!Number.isInteger(region.k) || region.k < 2 || region.k > 20) {
        status.textContent = `Choose a whole k value from 2 to 20 for ${region.id}.`
        return
      }
    }
    const output = regions.map((region) => ({
      id: region.id,
      label: region.label.trim(),
      box: [
        Math.round(region.box[0] * input.imageWidth / input.previewWidth),
        Math.round(region.box[1] * input.imageHeight / input.previewHeight),
        Math.round(region.box[2] * input.imageWidth / input.previewWidth),
        Math.round(region.box[3] * input.imageHeight / input.previewHeight)
      ],
      k: region.k,
      note: region.note.trim()
    }))
    finish.disabled = true
    finish.textContent = 'Regions saved'
    resolve(JSON.stringify(output))
  }
  image.onload = () => {
    refreshList()
    redraw()
  }
  image.src = input.image
  })
}
'''
    display(Javascript(script))
    call = "rangDrawRegions(" + json.dumps(payload, ensure_ascii=False) + ")"
    result = eval_js(call)
    regions = json.loads(result) if isinstance(result, str) else result
    return _validate_regions(regions, image.width, image.height)


def _validate_regions(regions, width, height):
    if not regions:
        raise ValueError("define at least one region")
    seen = set()
    cleaned = []
    for region in regions:
        region_id = str(region.get("id", "")).strip()
        if not re.fullmatch(r"[a-z][a-z0-9-]*", region_id):
            raise ValueError(f"bad region id: {region_id!r}")
        if region_id in seen:
            raise ValueError(f"duplicate region id: {region_id}")
        seen.add(region_id)
        box = region.get("box")
        if (not isinstance(box, (list, tuple)) or len(box) != 4
                or any(isinstance(value, bool) or not isinstance(value, int)
                       for value in box)):
            raise ValueError(f"{region_id}: box must contain four pixel integers")
        x0, y0, x1, y1 = box
        if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
            raise ValueError(f"{region_id}: box lies outside the source image")
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"{region_id}: box is empty or reversed")
        k = int(region.get("k", 8))
        if not 2 <= k <= 20:
            raise ValueError(f"{region_id}: k must be from 2 to 20")
        cleaned.append({
            "id": region_id,
            "label": str(region.get("label", region_id)).strip(),
            "box": [x0, y0, x1, y1],
            "normalized": [round(x0 / width, 6), round(y0 / height, 6),
                           round(x1 / width, 6), round(y1 / height, 6)],
            "k": k,
            "note": str(region.get("note", "")).strip(),
        })
    return cleaned


def create_recipe(palette_name, source, source_path, regions, recipe_path):
    image = open_rgb(source_path)
    recipe = {
        "schema_version": RECIPE_VERSION,
        "palette": palette_name,
        "creator": CREATOR,
        "website": WEBSITE,
        "license_holder": LICENSE_HOLDER,
        "source": {
            "image": str(source),
            "sha256": image_sha256(source_path),
            "oriented_width": image.width,
            "oriented_height": image.height,
            "color_handling": "EXIF orientation followed by RGB conversion",
        },
        "regions": _validate_regions(regions, image.width, image.height),
        "extraction": {
            "color_space": "CIELAB",
            "white_point": "D65",
            "algorithm": "sklearn.cluster.KMeans",
            "random_state": 0,
            "n_init": 20,
            "algorithm_mode": "lloyd",
            "maximum_region_size": 400,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pillow": PIL.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }
    write_json(recipe_path, recipe)
    return recipe


def region_overlay(recipe_path, work_dir, output=None):
    use_arial()
    recipe = read_json(recipe_path)
    source_path = obtain_source(recipe["source"]["image"], work_dir)
    _verify_source(recipe, source_path)
    image = open_rgb(source_path)
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.imshow(image)
    colors = plt.cm.tab10(np.linspace(0, 1, len(recipe["regions"])))
    for number, (region, color) in enumerate(zip(recipe["regions"], colors), start=1):
        x0, y0, x1, y1 = region["box"]
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                               fill=False, edgecolor=color, linewidth=3))
        ax.text(x0 + 12, y0 + 28, f'{number}. {region["label"]}, k={region["k"]}',
                color="black", fontsize=10,
                bbox={"facecolor": "white", "edgecolor": color, "alpha": 0.9})
    ax.set_title(f'{recipe["palette"]} extraction regions')
    ax.set_xlabel("x coordinate in pixels")
    ax.set_ylabel("y coordinate in pixels")
    fig.tight_layout()
    if output:
        output = pathlib.Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, facecolor="white", bbox_inches="tight")
    return fig


def _verify_source(recipe, source_path):
    actual = image_sha256(source_path)
    expected = recipe["source"]["sha256"]
    if actual != expected:
        raise ValueError("source checksum does not match the saved recipe")
    image = open_rgb(source_path)
    size = (recipe["source"]["oriented_width"],
            recipe["source"]["oriented_height"])
    if image.size != size:
        raise ValueError("source dimensions do not match the saved recipe")


def _cluster_region(image, box, k, settings):
    crop = image.crop(tuple(box))
    crop.thumbnail((settings["maximum_region_size"],
                    settings["maximum_region_size"]), Image.Resampling.LANCZOS)
    pixels = np.asarray(crop).reshape(-1, 3).astype(float)
    model = KMeans(
        n_clusters=k,
        n_init=settings["n_init"],
        random_state=settings["random_state"],
        algorithm=settings["algorithm_mode"],
    ).fit(rgb_to_lab(pixels))
    counts = np.bincount(model.labels_, minlength=k)
    rows = []
    for index in range(k):
        lab = model.cluster_centers_[index]
        rows.append({
            "lab": [round(float(value), 4) for value in lab],
            "hex": rgb_to_hex(lab_to_rgb(lab)),
            "share": round(float(counts[index] / len(model.labels_) * 100), 4),
        })
    rows.sort(key=lambda row: (-row["share"], *row["lab"]))
    return rows


def compute_candidates(recipe_path, work_dir):
    recipe = read_json(recipe_path)
    source_path = obtain_source(recipe["source"]["image"], work_dir)
    _verify_source(recipe, source_path)
    image = open_rgb(source_path)
    candidates = []
    for region in recipe["regions"]:
        rows = _cluster_region(image, region["box"], region["k"],
                               recipe["extraction"])
        for number, row in enumerate(rows, start=1):
            row.update({
                "id": f'{region["id"]}:c{number:02d}',
                "region": region["id"],
                "region_label": region["label"],
            })
            candidates.append(row)
    return candidates


def save_candidates(recipe_path, work_dir, accept=True):
    recipe_path = pathlib.Path(recipe_path)
    work_dir = pathlib.Path(work_dir)
    candidates = compute_candidates(recipe_path, work_dir)
    write_json(work_dir / "candidates.json", {"candidates": candidates})
    if accept:
        recipe = read_json(recipe_path)
        recipe["accepted_candidates"] = candidates
        write_json(recipe_path, recipe)
    candidate_sheet(candidates, work_dir / "candidates.png")
    return candidates


def candidate_sheet(candidates, output=None):
    use_arial()
    region_names = []
    for candidate in candidates:
        if candidate["region_label"] not in region_names:
            region_names.append(candidate["region_label"])
    rows = []
    for name in region_names:
        rows.append([item for item in candidates if item["region_label"] == name])
    columns = max(len(row) for row in rows)
    fig, axes = plt.subplots(len(rows), 1, figsize=(max(10, columns * 1.35),
                                                   max(2.1, len(rows) * 1.9)),
                             squeeze=False)
    for ax, name, row in zip(axes[:, 0], region_names, rows):
        ax.set_xlim(0, columns)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.text(-0.02, 0.5, name, ha="right", va="center", fontsize=10)
        for column, candidate in enumerate(row):
            ax.add_patch(Rectangle((column, 0.28), 0.95, 0.62,
                                   facecolor=candidate["hex"], edgecolor="white"))
            ax.text(column + 0.475, 0.18, candidate["id"].split(":")[-1],
                    ha="center", va="center", fontsize=8)
            ax.text(column + 0.475, 0.05, candidate["hex"],
                    ha="center", va="center", fontsize=8)
    fig.suptitle("K-means candidates, largest cluster first", fontsize=14)
    fig.tight_layout()
    if output:
        output = pathlib.Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, facecolor="white", bbox_inches="tight")
    return fig


def save_curation(recipe_path, selections):
    recipe = read_json(recipe_path)
    candidates = {item["id"]: item for item in recipe.get("accepted_candidates", [])}
    colors = []
    for number, selection in enumerate(selections, start=1):
        candidate_id = selection["candidate"]
        if candidate_id not in candidates:
            raise ValueError(f"candidate was not found: {candidate_id}")
        candidate = candidates[candidate_id]
        colors.append({
            "id": f"p{number:02d}",
            "from": candidate_id,
            "source_hex": candidate["hex"],
            "current": candidate["hex"],
            "note": str(selection.get("note", "")).strip(),
        })
    if not 5 <= len(colors) <= 12:
        raise ValueError("choose from 5 to 12 colors")
    recipe["curation"] = {
        "colors": colors,
        "operations": [],
        "final_order": [item["id"] for item in colors],
    }
    recipe["expected"] = {"colors": [item["current"] for item in colors]}
    write_json(recipe_path, recipe)
    return recipe


def _apply_one(color, adjustment):
    if "replace" in adjustment:
        replacement = str(adjustment["replace"]).lower()
        if not re.fullmatch(r"#[0-9a-f]{6}", replacement):
            raise ValueError(f"bad replacement color: {replacement}")
        return replacement, "replace", {"hex": replacement}
    delta = adjustment.get("delta", {})
    changes = {key: float(delta.get(key, 0)) for key in ("L", "C", "H")}
    return apply_edit(color, changes), "adjust_lch", changes


def apply_adjustments(recipe_path, adjustments, output=None, reset=False):
    recipe = read_json(recipe_path)
    curation = recipe.get("curation")
    if not curation:
        raise ValueError("save the candidate choices before adjusting colors")
    if reset:
        for item in curation["colors"]:
            item["current"] = item["source_hex"]
        curation["operations"] = []
    before_palette = [item["current"] for item in curation["colors"]]
    by_id = {item["id"]: item for item in curation["colors"]}
    for adjustment in adjustments:
        target = adjustment["target"]
        if target not in by_id:
            raise ValueError(f"palette color was not found: {target}")
        reason = str(adjustment.get("reason", "")).strip()
        if not reason:
            raise ValueError(f"{target}: give a short reason for the adjustment")
        item = by_id[target]
        before = item["current"]
        after, operation, detail = _apply_one(before, adjustment)
        record = {
            "id": f'a{len(curation["operations"]) + 1:03d}',
            "op": operation,
            "target": target,
            "before": before,
            "after": after,
            "reason": reason,
        }
        record.update(detail)
        curation["operations"].append(record)
        item["current"] = after
    after_palette = [item["current"] for item in curation["colors"]]
    recipe["expected"] = {"colors": after_palette}
    write_json(recipe_path, recipe)
    before_after_sheet(before_palette, after_palette, output)
    return recipe


def before_after_sheet(before, after, output=None):
    use_arial()
    fig, axes = plt.subplots(2, 1, figsize=(max(9, len(before) * 1.25), 2.8))
    for ax, colors, label in zip(axes, (before, after), ("Before", "After")):
        ax.set_xlim(0, len(colors))
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.text(-0.1, 0.5, label, ha="right", va="center")
        for index, color in enumerate(colors):
            ax.add_patch(Rectangle((index, 0), 1, 1,
                                   facecolor=color, edgecolor="white"))
            ax.text(index + 0.5, -0.12, color, ha="center", va="top", fontsize=8)
    fig.tight_layout()
    if output:
        output = pathlib.Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, facecolor="white", bbox_inches="tight")
    return fig


def check_recipe(recipe_path, work_dir, output=None):
    recipe = read_json(recipe_path)
    colors = recipe.get("expected", {}).get("colors", [])
    if len(colors) < 2:
        raise ValueError("curate at least two colors before checking the recipe")
    source_path = obtain_source(recipe["source"]["image"], work_dir)
    _verify_source(recipe, source_path)
    viewing = {}
    for kind in VISION_TYPES:
        minimum, mean = pairwise_min_mean(colors, kind)
        viewing[VISION_LABELS[kind]] = {
            "minimum": round(minimum, 4),
            "mean": round(mean, 4),
        }
    presence = {
        color: {"nearest": round(values[0], 4), "share_within_8": round(values[1], 4)}
        for color, values in presence_in_image(colors, source_path).items()
    }
    report = {
        "palette": recipe["palette"],
        "colors": colors,
        "suggested_pick_order": greedy_order(colors),
        "colorblind": worst_case(colors) >= COLORBLIND_THRESHOLD,
        "viewing": viewing,
        "source_presence": presence,
    }
    if output:
        write_json(output, report)
    return report


def palette_draft(recipe_path, metadata, output):
    recipe = read_json(recipe_path)
    curation = recipe.get("curation")
    if not curation:
        raise ValueError("curate the colors before writing a palette draft")
    colors = recipe["expected"]["colors"]
    draft = {}
    for key in ("name", "persian", "pronunciation", "position", "about",
                "story", "craft", "samples"):
        if key in metadata:
            draft[key] = metadata[key]
    draft["name"] = metadata.get("name", recipe["palette"])
    draft["colors"] = colors
    draft["notes"] = [item["note"] for item in curation["colors"]]
    draft["order"] = greedy_order(colors)
    draft["colorblind"] = worst_case(colors) >= COLORBLIND_THRESHOLD
    if "source" not in metadata:
        raise ValueError("palette metadata must include the source record")
    draft["source"] = metadata["source"]
    write_json(output, draft)
    return draft


def verify_recipe(recipe_path, work_dir):
    recipe = read_json(recipe_path)
    accepted = recipe.get("accepted_candidates", [])
    fresh = compute_candidates(recipe_path, work_dir)
    candidate_match = [item["id"] for item in accepted] == [item["id"] for item in fresh]
    hex_match = [item["hex"] for item in accepted] == [item["hex"] for item in fresh]
    centers_match = (len(accepted) == len(fresh)
                     and all(np.allclose(saved["lab"], current["lab"], atol=0.02)
                             for saved, current in zip(accepted, fresh)))
    shares_match = (len(accepted) == len(fresh)
                    and all(abs(saved["share"] - current["share"]) <= 0.02
                            for saved, current in zip(accepted, fresh)))
    curation = recipe.get("curation", {})
    state = {item["id"]: item["source_hex"] for item in curation.get("colors", [])}
    replay_errors = []
    for operation in curation.get("operations", []):
        target = operation["target"]
        if state.get(target) != operation["before"]:
            replay_errors.append(f'{operation["id"]}: before color does not match')
            continue
        if operation["op"] == "replace":
            after = operation["hex"]
        else:
            after = apply_edit(state[target], operation)
        if after != operation["after"]:
            replay_errors.append(f'{operation["id"]}: after color does not replay')
        state[target] = after
    order = curation.get("final_order", [])
    replayed = [state[item] for item in order if item in state]
    expected = recipe.get("expected", {}).get("colors", [])
    return {
        "candidate_ids_match": candidate_match,
        "candidate_hex_match": hex_match,
        "candidate_centers_match": centers_match,
        "candidate_shares_match": shares_match,
        "replayed_colors_match": replayed == expected,
        "replay_errors": replay_errors,
        "verified": candidate_match and hex_match and centers_match
                    and shares_match and replayed == expected and not replay_errors,
    }
