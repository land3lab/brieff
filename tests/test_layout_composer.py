from illustrator.config import FINAL_SIZE
from illustrator.layout_composer import choose_layout, render_layout, wrap_text
from PIL import Image, ImageDraw, ImageFont

from pathlib import Path

FONT_PATH = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Pretendard-Regular.ttf"


def test_choose_layout_picks_comparison_for_two_items():
    assert choose_layout([{"term": "a", "description": ""}, {"term": "b", "description": ""}]) == "comparison"


def test_choose_layout_picks_numbered_cards_otherwise():
    assert choose_layout([{"term": "a", "description": ""}]) == "numbered_cards"
    assert choose_layout([{"term": str(i), "description": ""} for i in range(4)]) == "numbered_cards"


def test_render_layout_produces_final_size_image():
    items = [{"term": "국세", "description": "국가가 부과하는 조세"}]
    image = render_layout("numbered_cards", items, [None])
    assert image.size == FINAL_SIZE


def test_render_table_and_comparison_do_not_crash():
    items = [{"term": f"용어{i}", "description": f"설명{i}"} for i in range(3)]
    assert render_layout("table", items, [None] * 3).size == FINAL_SIZE
    two_items = items[:2]
    assert render_layout("comparison", two_items, [None, None]).size == FINAL_SIZE


def test_wrap_text_splits_long_korean_text_without_spaces():
    image = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT_PATH), 30)
    long_text = "가" * 50
    lines = wrap_text(draw, long_text, font, max_width=200)
    assert len(lines) > 1
    assert "".join(lines) == long_text
