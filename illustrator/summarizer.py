"""Condense a slide/section's text into one short, concrete visual concept
that an image model can draw -- this is what makes "본문내용을 그림에 함축"
(compress the body text into the picture) actually happen instead of the
model drawing a literal wall of text.
"""
from __future__ import annotations

import base64
import io

from openai import OpenAI
from PIL import Image

from illustrator.config import CHAT_MODEL

SYSTEM_PROMPT = (
    "You turn a lecture slide's text into ONE short icon concept (max 20 English words) for a "
    "professional flat-icon infographic illustration, in the style used in corporate/legal/tax "
    "training slides. Describe a single icon or a small cluster of 2-3 recognizable icons "
    "(e.g. a government/bank building, scales of justice, a law book, a businessperson at a "
    "laptop, a warning triangle, a document with a stamp, a stack of coins, a calculator, a "
    "checklist, a calendar, a shield with a checkmark) that best symbolizes the core idea. "
    "Do not describe colors, art style, or any text/labels -- only the icon subject matter. "
    "Reply with only the concept sentence, no preamble."
)

IMAGE_SYSTEM_PROMPT = (
    "The user attaches a photo or screenshot of a lecture slide. Read whatever text or "
    "diagrams are visible in it, then reply with ONE short icon concept (max 20 English words) "
    "for a professional flat-icon infographic illustration. Describe a single icon or a small "
    "cluster of 2-3 recognizable icons (e.g. a government/bank building, scales of justice, a "
    "law book, a businessperson at a laptop, a warning triangle, a document with a stamp, a "
    "stack of coins, a calculator, a checklist, a calendar, a shield with a checkmark) that best "
    "symbolizes its core idea. Do not describe colors, art style, or any text/labels -- only the "
    "icon subject matter. Reply with only the concept sentence, no preamble."
)


def concept_from_text(client: OpenAI, title: str, body: str) -> str:
    combined = f"제목: {title}\n본문: {body}".strip()
    if not combined:
        return "an abstract idea represented by simple geometric shapes"
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": combined},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


def concept_from_image(client: OpenAI, image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    b64_data = base64.b64encode(buffer.getvalue()).decode()
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": IMAGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "이 슬라이드 캡처의 핵심 내용을 요약해줘."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_data}"}},
                ],
            },
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()
