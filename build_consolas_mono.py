#!/usr/bin/env python3
"""Build "Consolas Mono": Consolas Latin glyphs on JetBrains Mono metrics.

The donor glyphs are uniformly scaled so Consolas's 1126-unit (2048 UPM)
monospace cell maps exactly onto JetBrains Mono's 600-unit (1000 UPM) cell.
Baselines coincide, so vertical placement and line spacing stay JetBrains
Mono's; all non-replaced glyphs (box drawing, Nerd Font icons, arrows, Greek,
Cyrillic, ligature glyphs, OpenType layout) remain untouched.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

WINDOWS_FONTS = Path("C:/Windows/Fonts")

STYLES = {
    # style: (base file, donor file, subfamily, PostScript name)
    "Regular": (
        "JetBrainsMonoNerdFontMono-Regular.ttf",
        "consola.ttf",
        "Regular",
        "ConsolasMono-Regular",
    ),
    "Bold": (
        "JetBrainsMonoNerdFontMono-Bold.ttf",
        "consolab.ttf",
        "Bold",
        "ConsolasMono-Bold",
    ),
    "Italic": (
        "JetBrainsMonoNerdFontMono-Italic.ttf",
        "consolai.ttf",
        "Italic",
        "ConsolasMono-Italic",
    ),
    "BoldItalic": (
        "JetBrainsMonoNerdFontMono-BoldItalic.ttf",
        "consolaz.ttf",
        "Bold Italic",
        "ConsolasMono-BoldItalic",
    ),
}

# Basic Latin, Latin-1 Supplement, Latin Extended-A, plus English typographic
# punctuation / symbols that Consolas also has at its normal 1126 advance.
CODEPOINTS = (
    list(range(0x0020, 0x007F))
    + list(range(0x00A0, 0x0100))
    + list(range(0x0100, 0x0180))
    + [
        0x2010, 0x2011, 0x2012, 0x2013, 0x2014, 0x2018, 0x2019, 0x201A,
        0x201C, 0x201D, 0x201E, 0x2020, 0x2021, 0x2022, 0x2026, 0x2030,
        0x2039, 0x203A, 0x20AC,
    ]
)

COPYRIGHT = (
    "Consolas glyph outlines Copyright (c) 2025 Microsoft Corporation. "
    "All rights reserved. Base font JetBrains Mono Copyright (c) 2020 "
    "The JetBrains Mono Project Authors. Local personal-use build; "
    "do not redistribute."
)
TRADEMARK = (
    "Consolas is a trademark of the Microsoft group of companies. "
    "JetBrains Mono is a trademark of JetBrains s.r.o."
)
DESIGNER = (
    "Consolas by Luc(as) de Groot / Microsoft Corporation; "
    "JetBrains Mono by Philipp Nurullin, Konstantin Bulenkov / JetBrains."
)
DESCRIPTION = (
    "Consolas letterforms scaled onto JetBrains Mono metrics and cell width, "
    "with Nerd Font symbols and OpenType features retained from the base."
)
LICENSE = (
    "Personal use only. This font contains proprietary Consolas glyph "
    "outlines owned by Microsoft Corporation and must not be redistributed. "
    "The base JetBrains Mono font is licensed under the SIL Open Font "
    "License, Version 1.1 (https://scripts.sil.org/OFL)."
)


def set_names(font: TTFont, subfamily: str, ps_name: str) -> None:
    full_name = "Consolas Mono" if subfamily == "Regular" else f"Consolas Mono {subfamily}"
    typo_family = "Consolas Mono"
    version = "Version 1.000"
    unique_id = f"1.000;NONE;{ps_name}"

    records = {
        0: COPYRIGHT,
        1: typo_family,
        2: subfamily,
        3: unique_id,
        4: full_name,
        5: version,
        6: ps_name,
        7: TRADEMARK,
        8: "Local build",
        9: DESIGNER,
        10: DESCRIPTION,
        13: LICENSE,
        16: typo_family,
        17: subfamily,
    }

    name = font["name"]
    # Keep the font-specific names referenced by OpenType stylistic sets.
    name.names = [record for record in name.names if record.nameID >= 256]
    for name_id, value in records.items():
        name.setName(value, name_id, 3, 1, 0x409)  # Windows, Unicode BMP, en-US
        name.setName(value, name_id, 1, 0, 0)     # Macintosh, Roman, English

    font["head"].fontRevision = 1.0


def replacement_names(font: TTFont, donor: TTFont) -> set[str]:
    font_cmap = font.getBestCmap()
    donor_cmap = donor.getBestCmap()
    return {
        font_cmap[cp]
        for cp in CODEPOINTS
        if cp in font_cmap and cp in donor_cmap
    }


def bake_affected_composites(font: TTFont, replaced: set[str]) -> int:
    """Freeze untouched composites that reference a replaced glyph.

    JetBrains Mono builds e.g. Greek capitals as composites of Latin letters.
    Baking those composites first keeps the non-Latin scripts visually
    identical to the base font after the Latin glyphs are swapped.
    """
    glyf = font["glyf"]
    hmtx = font["hmtx"]
    glyph_set = font.getGlyphSet()
    memo: dict[str, bool] = {}

    def references_replaced(glyph_name: str) -> bool:
        if glyph_name in memo:
            return memo[glyph_name]
        glyph = glyf[glyph_name]
        result = False
        if glyph.isComposite():
            for component in glyph.components:
                if component.glyphName in replaced or references_replaced(
                    component.glyphName
                ):
                    result = True
                    break
        memo[glyph_name] = result
        return result

    affected = [
        glyph_name
        for glyph_name in font.getGlyphOrder()
        if glyph_name not in replaced
        and glyf[glyph_name].isComposite()
        and references_replaced(glyph_name)
    ]

    for glyph_name in affected:
        recording = DecomposingRecordingPen(glyph_set)
        glyph_set[glyph_name].draw(recording)
        pen = TTGlyphPen(None)
        recording.replay(pen)
        glyph = pen.glyph()
        glyph.recalcBounds(glyf)
        glyf[glyph_name] = glyph
        hmtx[glyph_name] = (hmtx[glyph_name][0], glyph.xMin if glyph.numberOfContours else 0)

    return len(affected)


def replace_latin(font: TTFont, donor: TTFont) -> tuple[int, list[str]]:
    font_cmap = font.getBestCmap()
    donor_cmap = donor.getBestCmap()
    donor_set = donor.getGlyphSet()
    donor_hmtx = donor["hmtx"]

    glyf = font["glyf"]
    hmtx = font["hmtx"]
    replaced = 0
    skipped: list[str] = []

    for cp in CODEPOINTS:
        target_name = font_cmap.get(cp)
        donor_name = donor_cmap.get(cp)
        char = chr(cp)
        if target_name is None or donor_name is None:
            skipped.append(f"U+{cp:04X} ({char!r}): missing in "
                           f"{'base' if target_name is None else 'donor'}")
            continue

        target_advance = hmtx[target_name][0]
        donor_advance = donor_hmtx[donor_name][0]
        if donor_advance <= 0:
            skipped.append(f"U+{cp:04X} ({char!r}): zero donor advance")
            continue

        scale = target_advance / donor_advance
        # Record with components decomposed, then replay at the new scale.
        recording = DecomposingRecordingPen(donor_set)
        donor_set[donor_name].draw(recording)
        pen = TTGlyphPen(None)
        recording.replay(
            TransformPen(pen, Transform(scale, 0, 0, scale, 0, 0))
        )
        glyph = pen.glyph()

        if glyph.numberOfContours == 0:
            glyf[target_name] = glyph
            hmtx[target_name] = (target_advance, 0)
        else:
            glyph.recalcBounds(glyf)
            glyf[target_name] = glyph
            hmtx[target_name] = (target_advance, glyph.xMin)
        replaced += 1

    return replaced, skipped


def build_style(
    style: str,
    base_path: Path,
    donor_path: Path,
    subfamily: str,
    ps_name: str,
    output_dir: Path,
) -> Path:
    font = TTFont(base_path, lazy=False, recalcBBoxes=False)
    donor = TTFont(donor_path, lazy=False)

    swapped_names = replacement_names(font, donor)
    baked = bake_affected_composites(font, swapped_names)
    replaced, skipped = replace_latin(font, donor)

    # Recalculate table summaries from the stored bounds without changing
    # untouched glyphs or the base font's line metrics.
    font["maxp"].recalc(font)
    font["hhea"].recalc(font)

    set_names(font, subfamily, ps_name)
    font["OS/2"].achVendID = "NONE"
    if "PfEd" in font:
        del font["PfEd"]

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{ps_name}.ttf"
    # Keep the base font's stored bounds for untouched glyphs; fontTools'
    # default bbox recalculation would otherwise shift them by a unit.
    font.save(out_path)
    font.close()
    donor.close()

    print(
        f"{style:10s} -> {out_path.name}: replaced {replaced} glyphs, "
        f"baked {baked} untouched composites"
    )
    if skipped:
        for item in skipped:
            print("   skipped", item)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts-dir", type=Path, default=WINDOWS_FONTS)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "dist",
    )
    args = parser.parse_args()

    for style, (base_file, donor_file, subfamily, ps_name) in STYLES.items():
        base_path = args.fonts_dir / base_file
        donor_path = args.fonts_dir / donor_file
        missing = [str(p) for p in (base_path, donor_path) if not p.exists()]
        if missing:
            raise SystemExit(f"{style}: missing font file(s): {', '.join(missing)}")
        build_style(style, base_path, donor_path, subfamily, ps_name, args.output_dir)


if __name__ == "__main__":
    main()
