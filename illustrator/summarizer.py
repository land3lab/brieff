"""Condense a slide/section's text into one short, concrete visual concept
that an image model can draw -- this is what makes "본문내용을 그림에 함축"
(compress the body text into the picture) actually happen instead of the
model drawing a literal wall of text.
"""
from __future__ import annotations

from openai import OpenAI

from illustrator.config import CHAT_MODEL

SYSTEM_PROMPT = (
    "You turn a lecture slide's text into ONE short visual concept (max 20 English words) "
    "describing a single concrete scene, object, icon or metaphor that represents the core idea. "
    "Do not describe colors or art style, only the subject matter. "
    "Reply with only the concept sentence, no preamble."
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
