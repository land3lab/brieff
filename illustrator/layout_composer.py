"""Compose a finished 4:3 infographic slide (numbered cards / table /
2-column comparison) from short (term, description) items plus one small
AI-generated icon per item -- the layout style is modeled on the reference
course slides (blue numbered badges, bordered cards, header table, vs-style
comparison).

Korean text is rendered here with a bundled font (Pretendard, OFL license)
rather than left to the image model, because image models render Korean
text unreliably.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from illustrator.config import FINAL_SIZE
from illustrator.style import PALETTE

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONT_REGULAR = FONT_DIR / "Pretendard-Regular.ttf"
FONT_BOLD = FONT_DIR / "Pretendard-Bold.ttf"
FONT_EXTRABOLD = FONT_DIR / "Pretendard-ExtraBold.ttf"

NAVY = PALETTE["navy"]
PRIMARY_BLUE = PALETTE["primary_blue"]
SKY_BLUE = PALETTE["sky_blue"]
PALE_BLUE = PALETTE["pale_blue"]
WHITE = PALETTE["white"]
TEXT_DARK = "#1F2937"

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    key = (str(path), size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(path), size)
    return _font_cache[key]


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    if not text:
        return (0, 0)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return (right - left, bottom - top)


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    path: Path,
    max_size: int,
    max_width: float,
    min_size: int = 14,
) -> ImageFont.FreeTypeFont:
    """Shrink font size until `text` fits on one line within `max_width`."""
    size = max_size
    while size > min_size:
        font = _font(path, size)
        width, _ = _text_size(draw, text, font)
        if width <= max_width:
            return font
        size -= 2
    return _font(path, min_size)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Greedy, character-by-character wrap (space-agnostic, safe for Korean)."""
    lines: list[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        width, _ = _text_size(draw, candidate, font)
        if width <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines or [""]


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    x0, y0, x1, y1 = box
    width, height = _text_size(draw, text, font)
    x = x0 + (x1 - x0 - width) / 2
    y = y0 + (y1 - y0 - height) / 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    lines: list[str],
    font: ImageFont.FreeTypeFont,
    fill: str,
    line_spacing: float = 1.4,
) -> float:
    """Draw left-aligned lines starting at xy, return total height used."""
    x, y = xy
    _, line_height = _text_size(draw, "가", font)
    cursor_y = y
    for line in lines:
        draw.text((x, cursor_y), line, font=font, fill=fill)
        cursor_y += line_height * line_spacing
    return cursor_y - y


def placeholder_icon(size: int = 640, label: str = "ICON") -> Image.Image:
    """Used in dry-run / preview mode when no AI icon has been generated."""
    image = Image.new("RGB", (size, size), PALE_BLUE)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([size * 0.1, size * 0.1, size * 0.9, size * 0.9], radius=size * 0.08, outline=PRIMARY_BLUE, width=6)
    font = _font(FONT_BOLD, int(size * 0.14))
    draw_centered_text(draw, (0, 0, size, size), label, font, PRIMARY_BLUE)
    return image


def paste_icon_fit(canvas: Image.Image, icon: Image.Image, box: tuple[float, float, float, float]) -> None:
    x0, y0, x1, y1 = (int(v) for v in box)
    box_w, box_h = x1 - x0, y1 - y0
    if box_w <= 0 or box_h <= 0:
        return
    icon_ratio = icon.width / icon.height
    box_ratio = box_w / box_h
    if icon_ratio > box_ratio:
        new_w = box_w
        new_h = int(box_w / icon_ratio)
    else:
        new_h = box_h
        new_w = int(box_h * icon_ratio)
    resized = icon.convert("RGBA").resize((max(new_w, 1), max(new_h, 1)), Image.LANCZOS)
    paste_x = x0 + (box_w - new_w) // 2
    paste_y = y0 + (box_h - new_h) // 2
    canvas.paste(resized, (paste_x, paste_y), resized)


def _new_canvas() -> Image.Image:
    return Image.new("RGB", FINAL_SIZE, WHITE)


def render_numbered_cards(items: list[dict], icons: list[Image.Image | None]) -> Image.Image:
    items = items[:5]
    icons = (icons + [None] * len(items))[: len(items)]
    canvas = _new_canvas()
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size

    margin = int(width * 0.03)
    gap = int(height * 0.02)
    n = max(len(items), 1)
    card_w = width - 2 * margin
    card_h = (height - 2 * margin - (n - 1) * gap) / n

    for i, (item, icon) in enumerate(zip(items, icons)):
        x0 = margin
        y0 = margin + i * (card_h + gap)
        x1 = x0 + card_w
        y1 = y0 + card_h
        draw.rounded_rectangle([x0, y0, x1, y1], radius=card_h * 0.12, outline=PRIMARY_BLUE, width=5, fill=WHITE)

        circle_d = card_h * 0.55
        cx0 = x0 + card_h * 0.12
        cy0 = y0 + (card_h - circle_d) / 2
        draw.ellipse([cx0, cy0, cx0 + circle_d, cy0 + circle_d], fill=NAVY)
        num_font = _font(FONT_EXTRABOLD, int(circle_d * 0.5))
        draw_centered_text(draw, (cx0, cy0, cx0 + circle_d, cy0 + circle_d), str(i + 1), num_font, WHITE)

        icon_box_size = card_h * 0.82
        icon_box = (x1 - icon_box_size - card_h * 0.1, y0 + (card_h - icon_box_size) / 2, x1 - card_h * 0.1, y0 + (card_h - icon_box_size) / 2 + icon_box_size)
        paste_icon_fit(canvas, icon or placeholder_icon(), icon_box)

        text_x = cx0 + circle_d + card_h * 0.15
        text_right = icon_box[0] - card_h * 0.1

        term_font = fit_font(draw, item["term"], FONT_EXTRABOLD, int(card_h * 0.26), text_right - text_x)
        draw.text((text_x, y0 + card_h * 0.14), item["term"], font=term_font, fill=NAVY)

        desc_font = _font(FONT_REGULAR, int(card_h * 0.14))
        desc_lines = wrap_text(draw, f"◆ {item.get('description', '')}", desc_font, int(text_right - text_x))
        draw_multiline(draw, (text_x, y0 + card_h * 0.52), desc_lines[:2], desc_font, TEXT_DARK)

    return canvas


def render_table(items: list[dict], icons: list[Image.Image | None]) -> Image.Image:
    items = items[:6]
    icons = (icons + [None] * len(items))[: len(items)]
    canvas = _new_canvas()
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size

    margin = int(width * 0.03)
    header_h = height * 0.09
    table_x0, table_x1 = margin, width - margin
    table_y0 = margin
    n = max(len(items), 1)
    row_h = (height - 2 * margin - header_h) / n
    col_split = table_x0 + (table_x1 - table_x0) * 0.38

    draw.rectangle([table_x0, table_y0, table_x1, table_y0 + header_h], fill=NAVY)
    header_font = _font(FONT_EXTRABOLD, int(header_h * 0.42))
    draw_centered_text(draw, (table_x0, table_y0, col_split, table_y0 + header_h), "용어", header_font, WHITE)
    draw_centered_text(draw, (col_split, table_y0, table_x1, table_y0 + header_h), "의미", header_font, WHITE)

    for i, (item, icon) in enumerate(zip(items, icons)):
        y0 = table_y0 + header_h + i * row_h
        y1 = y0 + row_h
        row_fill = WHITE if i % 2 == 0 else PALE_BLUE
        draw.rectangle([table_x0, y0, table_x1, y1], fill=row_fill)
        draw.line([table_x0, y1, table_x1, y1], fill="#D0D7E2", width=2)

        icon_size = row_h * 0.6
        icon_box = (table_x0 + row_h * 0.15, y0 + (row_h - icon_size) / 2, table_x0 + row_h * 0.15 + icon_size, y0 + (row_h - icon_size) / 2 + icon_size)
        paste_icon_fit(canvas, icon or placeholder_icon(), icon_box)

        term_x = icon_box[2] + row_h * 0.15
        term_max_width = col_split - term_x - row_h * 0.1
        term_font = fit_font(draw, item["term"], FONT_BOLD, int(row_h * 0.32), term_max_width)
        draw.text((term_x, y0 + (row_h - term_font.size) / 2), item["term"], font=term_font, fill=NAVY)

        desc_font = _font(FONT_REGULAR, int(row_h * 0.22))
        desc_max_width = table_x1 - col_split - row_h * 0.2
        desc_lines = wrap_text(draw, item.get("description", ""), desc_font, int(desc_max_width))[:2]
        line_block_h = len(desc_lines) * desc_font.size * 1.3
        draw_multiline(draw, (col_split + row_h * 0.1, y0 + (row_h - line_block_h) / 2), desc_lines, desc_font, TEXT_DARK)

        draw.line([col_split, y0, col_split, y1], fill="#D0D7E2", width=2)

    draw.rectangle([table_x0, table_y0, table_x1, table_y0 + header_h + n * row_h], outline=PRIMARY_BLUE, width=4)
    return canvas


def render_comparison(left_item: dict, right_item: dict, left_icon: Image.Image | None, right_icon: Image.Image | None) -> Image.Image:
    canvas = _new_canvas()
    draw = ImageDraw.Draw(canvas)
    width, height = canvas.size

    margin = int(width * 0.03)
    gap = int(width * 0.03)
    half_w = (width - 2 * margin - gap) / 2
    banner_h = height * 0.11

    for i, (item, icon) in enumerate([(left_item, left_icon), (right_item, right_icon)]):
        x0 = margin + i * (half_w + gap)
        x1 = x0 + half_w
        y0 = margin
        y1 = height - margin

        draw.rounded_rectangle([x0, y0, x1, y1], radius=half_w * 0.05, outline=PRIMARY_BLUE, width=5, fill=WHITE)
        draw.rounded_rectangle([x0, y0, x1, y0 + banner_h], radius=half_w * 0.05, fill=NAVY)
        draw.rectangle([x0, y0 + banner_h * 0.5, x1, y0 + banner_h], fill=NAVY)
        title_font = fit_font(draw, item["term"], FONT_EXTRABOLD, int(banner_h * 0.42), half_w * 0.9)
        draw_centered_text(draw, (x0, y0, x1, y0 + banner_h), item["term"], title_font, WHITE)

        icon_size = half_w * 0.42
        icon_box = (x0 + (half_w - icon_size) / 2, y0 + banner_h + half_w * 0.08, x0 + (half_w - icon_size) / 2 + icon_size, y0 + banner_h + half_w * 0.08 + icon_size)
        paste_icon_fit(canvas, icon or placeholder_icon(), icon_box)

        desc_font = _font(FONT_REGULAR, int(half_w * 0.075))
        desc_lines = wrap_text(draw, item.get("description", ""), desc_font, int(half_w * 0.82))[:4]
        draw_multiline(draw, (x0 + half_w * 0.09, icon_box[3] + half_w * 0.08), desc_lines, desc_font, TEXT_DARK)

    vs_d = height * 0.09
    vs_x0 = width / 2 - vs_d / 2
    vs_y0 = height * 0.42
    draw.ellipse([vs_x0, vs_y0, vs_x0 + vs_d, vs_y0 + vs_d], fill=SKY_BLUE, outline=WHITE, width=6)
    vs_font = _font(FONT_EXTRABOLD, int(vs_d * 0.4))
    draw_centered_text(draw, (vs_x0, vs_y0, vs_x0 + vs_d, vs_y0 + vs_d), "VS", vs_font, WHITE)

    return canvas


def choose_layout(items: list[dict]) -> str:
    if len(items) == 2:
        return "comparison"
    return "numbered_cards"


def render_layout(layout: str, items: list[dict], icons: list[Image.Image | None]) -> Image.Image:
    if layout == "auto":
        layout = choose_layout(items)
    if layout == "comparison":
        left = items[0] if items else {"term": "", "description": ""}
        right = items[1] if len(items) > 1 else {"term": "", "description": ""}
        left_icon = icons[0] if icons else None
        right_icon = icons[1] if len(icons) > 1 else None
        return render_comparison(left, right, left_icon, right_icon)
    if layout == "table":
        return render_table(items, icons)
    return render_numbered_cards(items, icons)
