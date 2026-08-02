# Rang in HEC-RAS

RAS Mapper stores layer settings in the project's XML based `.rasmap` file.
Every Rang palette ships as a `Symbology` block based on SurfaceFill entries
inspected in RAS Mapper 6.x project files:

| file | contents |
|---|---|
| `<Name>.rasmap.xml` | two paste ready surface fill blocks, the ramp forward and reversed |

Each block looks like this, with colors stored as the signed ARGB integers
RAS Mapper uses:

```xml
<Symbology>
  <SurfaceFill Colors="-8441824,-5551545,-4165559,..." Values="0,0.125,..."
    Stretched="True" AlphaTag="255" UseDatasetMinMax="True"
    RegenerateForScreen="True" />
</Symbology>
```

## Apply to a results layer

1. Close HEC-RAS, and make a copy of the project's `.rasmap` file in case
   you want the old symbology back.
2. Open the `.rasmap` file in a text editor and find the layer you want to
   restyle, for example `<Layer Name="depth" ...>`. Inside it sits a
   `<Symbology>` block with a `SurfaceFill` line.
3. Replace that block with one from `<Name>.rasmap.xml`, save, and reopen
   the project. The layer draws with the palette stretched over its own
   value range, since the shipped blocks set `UseDatasetMinMax="True"`.

The reversed variant runs the ramp light end first, which usually reads
better for depth grids where shallow water should stay light.

## Fixed value ranges

When you want the breaks at specific values instead of the layer's min and
max, generate the block with the ramp script and paste that in:

```
python tools/make_hecras_ramp.py kashan --min 0 --max 30
python tools/make_hecras_ramp.py golestan --min 0 --max 12 -n 12 --reverse
python tools/make_hecras_ramp.py kashan --min 480 --max 520 --alpha 200
```

`-n` interpolates the ramp to any number of stops, `--reverse` flips it, and
`--alpha` sets transparency. The values it writes are evenly spaced across
your range, and you can edit any of them afterward, RAS Mapper accepts
uneven spacing.

## Through the interface instead

If you would rather not touch the file, open **RAS Mapper**, right click the
layer, **Layer Properties**, then **Edit** under the surface fill. Set the
number of colors to the palette size, click each color box and enter the hex
codes from the main README through the color dialog, then save the ramp to
the color list so the project can reuse it. The file route above is faster
and survives across layers with a copy and paste.

HEC does not publish a schema for this part of `.rasmap`, so the format here
mirrors entries inspected in RAS Mapper 6.x project files. If a
future version changes the format, restyle one layer in the interface, look
at what it wrote, and tell us so the generator gets updated.
