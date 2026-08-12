"""Export a Glyphs source through the installed BDF file-format plug-in."""

import os
import sys

from Foundation import NSClassFromString
from GlyphsApp import Glyphs


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: export_bdf.py OUTPUT.bdf")

    if len(Glyphs.fonts) != 1:
        raise RuntimeError("exactly one Glyphs source must be loaded")

    plugin_class = NSClassFromString("BDFFileFormat")
    if plugin_class is None:
        raise RuntimeError(
            "BDF plug-in not found; install BDF.glyphsFileFormat in Glyphs 3"
        )

    output_path = os.path.abspath(sys.argv[1])
    temporary_path = output_path + ".tmp.bdf"
    exporter = plugin_class.alloc().init()
    try:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)
        success, error = exporter.export(Glyphs.fonts[0], temporary_path)
        if not success:
            raise RuntimeError(error or "BDF export failed")
        if not os.path.isfile(temporary_path) or os.path.getsize(temporary_path) == 0:
            raise RuntimeError("BDF plug-in did not produce an output file")
        os.replace(temporary_path, output_path)
    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)

    print(f"Exported BDF to {output_path}")


if __name__ == "__main__":
    main()
