"""Break one slide's content into short (term, description) items so it can
be laid out as a numbered-card / table / comparison infographic, the way the
reference course slides do it.
"""
from __future__ import annotations

import base64
import io
import json

from openai import OpenAI
from PIL import Image

from illustrator.config import CHAT_MODEL

SYSTEM_PROMPT = (
    "You extract infographic items from a Korean lecture slide. Find the key terms "
    "(용어) and, for each, one short one-line Korean description/definition (15-25자 정도). "
    "Return 1 to 6 items, ordered as they appear. "
    "Respond ONLY as JSON: {\"items\": [{\"term\": \"...\", \"description\": \"...\"}]}"
)


def _parse_items(raw_json: str) -> list[dict]:
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return []
    items = []
    for entry in data.get("items", []):
        term = str(entry.get("term", "")).strip()
        description = str(entry.get("description", "")).strip()
        if term:
            items.append({"term": term, "description": description})
    return items[:6]


def extract_items_from_text(client: OpenAI, title: str, body: str) -> list[dict]:
    combined = f"제목: {title}\n본문: {body}".strip()
    if not combined:
        return []
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": combined},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return _parse_items(response.choices[0].message.content)


def extract_items_from_image(client: OpenAI, image: Image.Image) -> list[dict]:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    b64_data = base64.b64encode(buffer.getvalue()).decode()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 슬라이드 캡처에서 항목을 추출해줘."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_data}"}},
                ],
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    return _parse_items(response.choices[0].message.content)


def fallback_items_from_text(title: str, body: str) -> list[dict]:
    """Heuristic, API-free split used for dry-run / preview mode."""
    lines = [l.strip("-•· \t") for l in body.splitlines() if l.strip()]
    items = []
    for line in lines[:6]:
        if ":" in line:
            term, _, description = line.partition(":")
        elif "-" in line:
            term, _, description = line.partition("-")
        else:
            term, description = line[:10], line
        items.append({"term": term.strip() or "항목", "description": description.strip()})
    if not items and title:
        items.append({"term": title[:10], "description": body[:40]})
    return items
