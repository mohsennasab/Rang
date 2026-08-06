# Reusable Colab notebooks

The contribution path uses two notebooks.

1. [`rang_palette_workflow.ipynb`](rang_palette_workflow.ipynb) contains the
   seven-stage artistic workflow. Upload the artwork once, draw the sampling
   regions, curate the colors, and download a verified workflow ZIP.
2. [`rang_submission_builder.ipynb`](rang_submission_builder.ipynb) accepts
   that workflow ZIP, shows missing artwork metadata as warnings, and creates
   one submission ZIP with repository-ready files, documentation images,
   palette-specific software files, review material, and a pull request draft.
   Its optional update dictionary starts empty, which keeps recovered values.

[![Open notebook 1 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/notebooks/rang_palette_workflow.ipynb)

[![Open notebook 2 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mohsennasab/Rang/blob/main/tools/notebooks/rang_submission_builder.ipynb)

No cloud storage connection or repository checkout is needed inside Colab.
Notebook 2 keeps its ArcGIS Pro, QGIS, HEC-RAS, and GeoLibre files separate
from the repository-ready folder because the collection-wide files must be
rebuilt after the palette is added.

Yellow **YOUR INPUT** cells collect factual information. Blue **YOUR DECISION**
cells ask you to choose regions, candidates, and adjustments. Each decision
cell includes its own format example and a specific error when an entry cannot
be read. All figures request Arial, with Liberation Sans as the Colab fallback
when Arial is not installed.

Created by **Mohsen Tahmasebi Nasab, PhD**. Visit
[hydromohsen.com](https://hydromohsen.com).

Copyright and license holder: Mohsen Tahmasebi Nasab. Notebook code is
licensed under the MIT License in the repository root.
