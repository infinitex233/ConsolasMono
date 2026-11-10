#!/usr/bin/env python3
"""Render comparison sheets for the built Consolas Mono fonts."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS = Path("C:/Windows/Fonts")
OUT = ROOT / "dist"

BG = "#101418"
TEXT = "#e8e8e8"
LABEL = "#4ea1ff"
DIM = "#6a737d"
RULE = "#2a3038"

LINES = [
    "The quick brown fox jumps over the lazy dog.",
    "Sphinx of black quartz, judge my vow.",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "abcdefghijklmnopqrstuvwxyz",
    "0123456789  !@#$%^&*()_+-=[]{};:'\",.<>/?\\|`~",
    "mmmmmmmmmm | iiiiiiiiii | WWWWWWWWWW",
    'fn main() { println!("Hello, world!"); }',
    "== != <= >= -> => :: ... && || ++",
    "ÀÉÎÕÜ àéîõü Çç Ññ Ąą Ęę ¼ ½ ¾ © ® €",
]

SMALL_LINES = [
    "The quick brown fox jumps over the lazy dog.",
    "0123456789 !@#$%^&*()_+-=[]{};:'\",.<>/?\\|`~",
    "fn main() { println!(\"Hello, world!\"); }",
    "mmmmmmmmmm | iiiiiiiiii | WWWWWWWWWW",
    "== != <= >= -> => :: ... && || ++",
]


def load(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def block_height(font: ImageFont.FreeTypeFont, lines: list[str], gap: float) -> int:
    ascent, descent = font.getmetrics()
    return int((ascent + descent) * gap) * len(lines)


def draw_block(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    title: str,
    font: ImageFont.FreeTypeFont,
    lines: list[str],
    label_font: ImageFont.FreeTypeFont,
    gap: float,
    width: int,
) -> int:
    ascent, descent = font.getmetrics()
    line_height = int((ascent + descent) * gap)
    draw.text((x, y), title, font=label_font, fill=LABEL)
    y += label_font.getbbox("Ag")[3] + 8
    draw.line((x, y, x + width, y), fill=RULE, width=1)
    y += 10
    for line in lines:
        draw.text((x, y), line, font=font, fill=TEXT)
        y += line_height
    return y + 18


def make_sheet(
    out_path: Path,
    size: int,
    fonts: list[tuple[str, Path]],
    lines: list[str],
    gap: float = 1.12,
) -> None:
    label_font = load(Path("C:/Windows/Fonts/segoeui.ttf"), max(14, size // 2))
    pad = 24
    loaded = [(title, load(path, size)) for title, path in fonts]
    content_width = int(max(font.getlength(line) for _, font in loaded for line in lines))
    width = max(640, content_width + pad * 2)
    height = pad * 2 + sum(
        block_height(font, lines, gap) + 40 for _, font in loaded
    ) + 60
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    y = pad
    for title, font in loaded:
        y = draw_block(
            draw, pad, y, title, font, lines, label_font, gap, content_width
        )
    image.save(out_path)
    print("wrote", out_path, image.size)


def main() -> None:
    make_sheet(
        OUT / "preview.png",
        32,
        [
            ("JetBrains Mono Nerd Font Mono - base", FONTS / "JetBrainsMonoNerdFontMono-Regular.ttf"),
            ("Consolas Mono - built", OUT / "ConsolasMono-Regular.ttf"),
            ("Consolas - reference", FONTS / "consola.ttf"),
        ],
        LINES,
    )
    make_sheet(
        OUT / "preview-small.png",
        16,
        [
            ("JetBrains Mono Nerd Font Mono - base", FONTS / "JetBrainsMonoNerdFontMono-Regular.ttf"),
            ("Consolas Mono - built", OUT / "ConsolasMono-Regular.ttf"),
            ("Consolas - reference", FONTS / "consola.ttf"),
        ],
        SMALL_LINES,
    )
    make_sheet(
        OUT / "preview-styles.png",
        24,
        [
            ("Consolas Mono Regular", OUT / "ConsolasMono-Regular.ttf"),
            ("Consolas Mono Bold", OUT / "ConsolasMono-Bold.ttf"),
            ("Consolas Mono Italic", OUT / "ConsolasMono-Italic.ttf"),
            ("Consolas Mono Bold Italic", OUT / "ConsolasMono-BoldItalic.ttf"),
        ],
        LINES[:7],
    )


if __name__ == "__main__":
    main()
