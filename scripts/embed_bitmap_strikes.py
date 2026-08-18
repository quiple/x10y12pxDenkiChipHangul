"""Embed scaled monochrome bitmap strikes in an existing TrueType font."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables.BitmapGlyphMetrics import SmallGlyphMetrics
from fontTools.ttLib.tables.E_B_D_T_ import ebdt_bitmap_format_1
from fontTools.ttLib.tables.E_B_L_C_ import (
    SbitLineMetrics,
    Strike,
    eblc_index_sub_table_1,
)


DEFAULT_SIZES = (12, 24, 36, 48, 60)


@dataclass(frozen=True)
class BDFGlyph:
    name: str
    encoding: int | None
    advance: int
    width: int
    height: int
    offset_x: int
    offset_y: int
    rows: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class BDFFont:
    pixel_size: int
    ascent: int
    descent: int
    glyphs: tuple[BDFGlyph, ...]


def parse_sizes(value: str) -> tuple[int, ...]:
    try:
        sizes = tuple(int(item) for item in value.split(","))
    except ValueError as error:
        raise argparse.ArgumentTypeError("sizes must be comma-separated integers") from error
    if not sizes or any(size <= 0 or size > 255 for size in sizes):
        raise argparse.ArgumentTypeError("sizes must be between 1 and 255")
    if len(set(sizes)) != len(sizes):
        raise argparse.ArgumentTypeError("sizes must not contain duplicates")
    return tuple(sorted(sizes))


def _bitmap_row(row: str, width: int, glyph_name: str) -> tuple[int, ...]:
    if width == 0:
        if row:
            raise ValueError(f"{glyph_name}: a zero-width bitmap must have empty rows")
        return ()
    if not row or any(character not in "0123456789ABCDEFabcdef" for character in row):
        raise ValueError(f"{glyph_name}: invalid bitmap row {row!r}")
    padded_width = len(row) * 4
    if padded_width < width:
        raise ValueError(f"{glyph_name}: bitmap row is narrower than BBX")
    value = int(row, 16)
    return tuple(
        (value >> (padded_width - column - 1)) & 1 for column in range(width)
    )


def parse_bdf(path: Path) -> BDFFont:
    lines = path.read_text(encoding="ascii").splitlines()
    pixel_size = None
    ascent = None
    descent = None
    glyphs: list[BDFGlyph] = []
    glyph_names: set[str] = set()

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("SIZE "):
            pixel_size = int(line.split()[1])
        elif line.startswith("FONT_ASCENT "):
            ascent = int(line.split()[1])
        elif line.startswith("FONT_DESCENT "):
            descent = int(line.split()[1])
        elif line.startswith("STARTCHAR "):
            name = line[len("STARTCHAR ") :]
            encoding = None
            advance = None
            bounds = None
            bitmap_rows = None
            index += 1
            while index < len(lines) and lines[index] != "ENDCHAR":
                glyph_line = lines[index]
                if glyph_line.startswith("ENCODING "):
                    value = int(glyph_line.split()[1])
                    encoding = value if value >= 0 else None
                elif glyph_line.startswith("DWIDTH "):
                    advance = int(glyph_line.split()[1])
                elif glyph_line.startswith("BBX "):
                    bounds = tuple(int(value) for value in glyph_line.split()[1:])
                    if len(bounds) != 4:
                        raise ValueError(f"{name}: invalid BBX")
                elif glyph_line == "BITMAP":
                    if bounds is None:
                        raise ValueError(f"{name}: BITMAP appears before BBX")
                    height = bounds[1]
                    bitmap_rows = lines[index + 1 : index + 1 + height]
                    index += height
                index += 1

            if index >= len(lines) or lines[index] != "ENDCHAR":
                raise ValueError(f"{name}: missing ENDCHAR")
            if advance is None or bounds is None or bitmap_rows is None:
                raise ValueError(f"{name}: missing DWIDTH, BBX, or BITMAP")
            width, height, offset_x, offset_y = bounds
            if width < 0 or height < 0:
                raise ValueError(f"{name}: negative BBX dimensions")
            if len(bitmap_rows) != height:
                raise ValueError(f"{name}: BITMAP row count does not match BBX")
            if name in glyph_names:
                raise ValueError(f"duplicate BDF glyph name: {name}")
            glyph_names.add(name)
            glyphs.append(
                BDFGlyph(
                    name=name,
                    encoding=encoding,
                    advance=advance,
                    width=width,
                    height=height,
                    offset_x=offset_x,
                    offset_y=offset_y,
                    rows=tuple(
                        _bitmap_row(row, width, name) for row in bitmap_rows
                    ),
                )
            )
        index += 1

    if pixel_size is None or ascent is None or descent is None:
        raise ValueError("BDF is missing SIZE, FONT_ASCENT, or FONT_DESCENT")
    if not glyphs:
        raise ValueError("BDF contains no glyphs")
    return BDFFont(pixel_size, ascent, descent, tuple(glyphs))


def _check_metric(value: int, minimum: int, maximum: int, label: str) -> int:
    if not minimum <= value <= maximum:
        raise ValueError(f"{label}={value} is outside {minimum}..{maximum}")
    return value


def _glyph_metrics(glyph: BDFGlyph, scale: int) -> SmallGlyphMetrics:
    metrics = SmallGlyphMetrics()
    metrics.height = _check_metric(glyph.height * scale, 0, 255, "height")
    metrics.width = _check_metric(glyph.width * scale, 0, 255, "width")
    metrics.BearingX = _check_metric(
        glyph.offset_x * scale, -128, 127, "bearingX"
    )
    metrics.BearingY = _check_metric(
        (glyph.offset_y + glyph.height) * scale, -128, 127, "bearingY"
    )
    metrics.Advance = _check_metric(glyph.advance * scale, 0, 255, "advance")
    return metrics


def _scale_bitmap(glyph: BDFGlyph, scale: int) -> bytes:
    scaled_width = glyph.width * scale
    row_bytes = (scaled_width + 7) // 8
    row_padding = row_bytes * 8 - scaled_width
    repeated_bits = (1 << scale) - 1
    output = bytearray()

    for row in glyph.rows:
        row_value = 0
        for bit in row:
            row_value = (row_value << scale) | (repeated_bits if bit else 0)
        row_data = (row_value << row_padding).to_bytes(row_bytes, "big")
        for _ in range(scale):
            output.extend(row_data)
    return bytes(output)


def _line_metrics(
    source: BDFFont, metrics: tuple[SmallGlyphMetrics, ...], scale: int
) -> SbitLineMetrics:
    line = SbitLineMetrics()
    line.ascender = _check_metric(source.ascent * scale, -128, 127, "ascender")
    line.descender = _check_metric(
        -source.descent * scale, -128, 127, "descender"
    )
    line.widthMax = _check_metric(
        max(metric.Advance for metric in metrics), 0, 255, "widthMax"
    )
    line.caretSlopeNumerator = 1
    line.caretSlopeDenominator = 0
    line.caretOffset = 0
    line.minOriginSB = _check_metric(
        min(metric.BearingX for metric in metrics), -128, 127, "minOriginSB"
    )
    line.minAdvanceSB = _check_metric(
        min(
            metric.Advance - metric.BearingX - metric.width for metric in metrics
        ),
        -128,
        127,
        "minAdvanceSB",
    )
    line.maxBeforeBL = _check_metric(
        max(metric.BearingY for metric in metrics), -128, 127, "maxBeforeBL"
    )
    line.minAfterBL = _check_metric(
        min(metric.BearingY - metric.height for metric in metrics),
        -128,
        127,
        "minAfterBL",
    )
    line.pad1 = 0
    line.pad2 = 0
    return line


def _empty_line_metrics() -> SbitLineMetrics:
    line = SbitLineMetrics()
    for name in (
        "ascender",
        "descender",
        "widthMax",
        "caretSlopeNumerator",
        "caretSlopeDenominator",
        "caretOffset",
        "minOriginSB",
        "minAdvanceSB",
        "maxBeforeBL",
        "minAfterBL",
        "pad1",
        "pad2",
    ):
        setattr(line, name, 0)
    return line


def _map_glyphs(font: TTFont, source: BDFFont) -> tuple[tuple[str, BDFGlyph], ...]:
    glyph_order = font.getGlyphOrder()
    glyph_names = set(glyph_order)
    glyph_indices = {name: index for index, name in enumerate(glyph_order)}

    # Glyphs may replace source names with production names when exporting TTF.
    # Its BDF and TTF exporters retain the same glyph order, so use that order
    # when a substantial set of unchanged names confirms it.
    if len(source.glyphs) == len(glyph_order):
        order_matches = True
        confirmed_positions = 0
        for index, glyph in enumerate(source.glyphs):
            if glyph.name in glyph_indices:
                if glyph_indices[glyph.name] != index:
                    order_matches = False
                    break
                confirmed_positions += 1
        if order_matches and confirmed_positions >= min(32, len(glyph_order)):
            return tuple(zip(glyph_order, source.glyphs))

    cmap = font.getBestCmap() or {}
    mapped: dict[str, BDFGlyph] = {}

    for glyph in source.glyphs:
        target_name = glyph.name if glyph.name in glyph_names else None
        if target_name is None and glyph.encoding is not None:
            target_name = cmap.get(glyph.encoding)
        if target_name is None:
            raise ValueError(f"BDF glyph is missing from TTF: {glyph.name}")
        if target_name in mapped:
            raise ValueError(f"multiple BDF glyphs map to TTF glyph {target_name}")
        mapped[target_name] = glyph

    return tuple((name, mapped[name]) for name in glyph_order if name in mapped)


def add_bitmap_strikes(
    font: TTFont, source: BDFFont, sizes: tuple[int, ...]
) -> dict[int, int]:
    for size in sizes:
        if size % source.pixel_size:
            raise ValueError(
                f"strike size {size} is not an integer multiple of BDF size "
                f"{source.pixel_size}"
            )

    mapped_glyphs = _map_glyphs(font, source)
    if not mapped_glyphs:
        raise ValueError("no BDF glyphs could be mapped to the TTF")

    ebdt = newTable("EBDT")
    ebdt.version = 2.0
    ebdt.strikeData = []
    eblc = newTable("EBLC")
    eblc.version = 2.0
    eblc.strikes = []
    glyph_counts = {}

    for size in sizes:
        scale = size // source.pixel_size
        strike_glyphs = []
        strike_metrics = {}
        for glyph_name, glyph in mapped_glyphs:
            try:
                metrics = _glyph_metrics(glyph, scale)
            except ValueError as error:
                raise ValueError(f"{glyph.name} at {size}px: {error}") from error
            strike_glyphs.append((glyph_name, glyph))
            strike_metrics[glyph_name] = metrics

        if not strike_glyphs:
            raise ValueError(f"no glyph metrics fit the EBDT format at {size}px")
        glyph_names = [name for name, _ in strike_glyphs]
        metrics_for_line = tuple(strike_metrics[name] for name in glyph_names)

        strike = Strike()
        strike.bitmapSizeTable.colorRef = 0
        strike.bitmapSizeTable.hori = _line_metrics(
            source, metrics_for_line, scale
        )
        strike.bitmapSizeTable.vert = _empty_line_metrics()
        strike.bitmapSizeTable.ppemX = size
        strike.bitmapSizeTable.ppemY = size
        strike.bitmapSizeTable.bitDepth = 1
        strike.bitmapSizeTable.flags = 0x01

        index_subtable = eblc_index_sub_table_1(None, None)
        index_subtable.indexFormat = 1
        index_subtable.imageFormat = 1
        index_subtable.names = list(glyph_names)
        strike.indexSubTables.append(index_subtable)
        eblc.strikes.append(strike)

        bitmap_glyphs = {}
        for glyph_name, glyph in strike_glyphs:
            bitmap = ebdt_bitmap_format_1(None, None)
            bitmap.metrics = strike_metrics[glyph_name]
            bitmap.imageData = _scale_bitmap(glyph, scale)
            bitmap_glyphs[glyph_name] = bitmap
        ebdt.strikeData.append(bitmap_glyphs)
        glyph_counts[size] = len(strike_glyphs)

    font["EBDT"] = ebdt
    font["EBLC"] = eblc
    return glyph_counts


def save_atomically(font: TTFont, output_path: Path) -> None:
    temporary_path = output_path.with_name(output_path.name + ".tmp")
    try:
        if temporary_path.exists():
            temporary_path.unlink()
        font.save(temporary_path, reorderTables=False)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def validate_font(
    path: Path,
    source: BDFFont,
    sizes: tuple[int, ...],
    glyph_counts: dict[int, int],
) -> None:
    with TTFont(path, lazy=False, recalcBBoxes=False, recalcTimestamp=False) as font:
        if "EBDT" not in font or "EBLC" not in font:
            raise RuntimeError("saved TTF does not contain EBDT and EBLC")
        strikes = font["EBLC"].strikes
        actual_sizes = tuple(strike.bitmapSizeTable.ppemY for strike in strikes)
        if actual_sizes != sizes:
            raise RuntimeError(
                f"saved TTF has bitmap sizes {actual_sizes}, expected {sizes}"
            )
        if len(font["EBDT"].strikeData) != len(sizes):
            raise RuntimeError("saved TTF has an unexpected EBDT strike count")
        mapped_glyphs = _map_glyphs(font, source)
        for size, strike, bitmap_glyphs in zip(
            sizes, strikes, font["EBDT"].strikeData
        ):
            expected_count = glyph_counts[size]
            if len(bitmap_glyphs) != expected_count:
                raise RuntimeError(
                    f"{size}px strike has {len(bitmap_glyphs)} glyphs, "
                    f"expected {expected_count}"
                )
            if (
                strike.bitmapSizeTable.ppemX != size
                or strike.bitmapSizeTable.bitDepth != 1
                or strike.bitmapSizeTable.flags != 0x01
            ):
                raise RuntimeError(f"{size}px strike has invalid size or format flags")

            scale = size // source.pixel_size
            expected_names = {glyph_name for glyph_name, _ in mapped_glyphs}
            if set(bitmap_glyphs) != expected_names:
                raise RuntimeError(f"{size}px strike has the wrong glyph set")
            for glyph_name, glyph in mapped_glyphs:
                bitmap = bitmap_glyphs[glyph_name]
                expected_metrics = _glyph_metrics(glyph, scale)
                for metric_name in (
                    "height",
                    "width",
                    "BearingX",
                    "BearingY",
                    "Advance",
                ):
                    if getattr(bitmap.metrics, metric_name) != getattr(
                        expected_metrics, metric_name
                    ):
                        raise RuntimeError(
                            f"{glyph.name} has invalid {metric_name} at {size}px"
                        )
                if bitmap.imageData != _scale_bitmap(glyph, scale):
                    raise RuntimeError(
                        f"{glyph.name} has invalid bitmap data at {size}px"
                    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add monochrome EBDT/EBLC bitmap strikes to a TTF."
    )
    parser.add_argument("--font", required=True, type=Path, help="TTF to update")
    parser.add_argument("--bdf", required=True, type=Path, help="source BDF")
    parser.add_argument(
        "--sizes",
        type=parse_sizes,
        default=DEFAULT_SIZES,
        help="comma-separated ppem sizes (default: 12,24,36,48,60)",
    )
    arguments = parser.parse_args()

    source = parse_bdf(arguments.bdf)
    with TTFont(
        arguments.font, lazy=False, recalcBBoxes=False, recalcTimestamp=False
    ) as font:
        glyph_counts = add_bitmap_strikes(font, source, arguments.sizes)
        save_atomically(font, arguments.font)
    validate_font(
        arguments.font,
        source,
        arguments.sizes,
        glyph_counts,
    )
    summary = ", ".join(
        f"{size}px ({glyph_counts[size]} glyphs)" for size in arguments.sizes
    )
    print(f"Embedded monochrome bitmap strikes: {summary}")
    print(f"Updated {arguments.font}")


if __name__ == "__main__":
    main()
