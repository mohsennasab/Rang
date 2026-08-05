# Palette recipes

A recipe records how a contributor moved from an artwork image to the final
palette. The seven numbered notebooks in [`tools/notebooks`](../tools/notebooks/README.md)
create and replay the file.

One accepted recipe belongs at `recipes/<palette>.json`. Working copies,
region overlays, candidate sheets, and reports stay in the downloaded
workflow ZIP or the ignored `cache/` directory.

A recipe records:

- creator, website, and license holder
- source URL, SHA-256 checksum, and oriented dimensions
- pixel and normalized coordinates for every region
- a label, note, and k value for every region
- fixed CIELAB and k-means settings
- Python, NumPy, Pillow, and scikit-learn versions from the accepted run
- accepted candidates with stable IDs, CIELAB centers, hex colors, and shares
- selected candidates and their source notes
- every LCh adjustment with before and after colors and a reason
- final expected colors

The recipe makes the accepted process repeatable. It does not suggest that
the artistic decisions were inevitable. Another contributor may see different
regions or choose a different good palette from the same artwork.

Created by **Mohsen Tahmasebi Nasab, PhD**. Visit
[hydromohsen.com](https://hydromohsen.com).

Copyright and license holder: Mohsen Tahmasebi Nasab. Recipe structure and
notebook code are licensed under the repository's MIT License. Original
palette values follow the CC0 dedication described in the
[licensing guide](../LICENSES/README.md). Source images keep their own rights
and reuse terms.
