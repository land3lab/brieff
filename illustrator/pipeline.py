"""Wire content extraction -> concept summarization -> image generation ->
4:3 postprocessing into one call per chunk.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from openai import OpenAI
from PIL import Image

from illustrator.config import FINAL_SIZE
from illustrator.content_extractor import ContentChunk, ImageChunk
from illustrator.image_gen import generate_icon, generate_illustration
from illustrator.item_extractor import (
    extract_items_from_image,
    extract_items_from_text,
    fallback_items_from_text,
)
from illustrator.layout_composer import render_layout
from illustrator.postprocess import export_4_3
from illustrator.style import build_prompt
from illustrator.summarizer import concept_from_image, concept_from_text

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class GeneratedIllustration:
    index: int
    title: str
    concept: str
    prompt: str
    image: Image.Image | None


def _fallback_concept(chunk: ContentChunk | ImageChunk) -> str:
    if isinstance(chunk, ImageChunk):
        return "a lecture slide illustration (미리보기 모드에서는 이미지 내용을 읽을 수 없습니다)"
    text = chunk.title or chunk.body
    first_line = text.splitlines()[0] if text else "an abstract educational idea"
    return first_line[:120]


def generate_for_chunks(
    client: OpenAI | None,
    chunks: list[ContentChunk | ImageChunk],
    reference_image_path: str | None = None,
    dry_run: bool = False,
    include_mascot: bool = True,
    on_progress: ProgressCallback | None = None,
) -> list[GeneratedIllustration]:
    results: list[GeneratedIllustration] = []
    total = len(chunks)

    for chunk in chunks:
        if on_progress:
            on_progress(chunk.index, total, "요약 중...")

        if dry_run or client is None:
            concept = _fallback_concept(chunk)
        elif isinstance(chunk, ImageChunk):
            concept = concept_from_image(client, chunk.image)
        else:
            concept = concept_from_text(client, chunk.title, chunk.body)

        prompt = build_prompt(concept, include_mascot=include_mascot)

        image = None
        if not dry_run and client is not None:
            if on_progress:
                on_progress(chunk.index, total, "이미지 생성 중...")
            raw_image = generate_illustration(
                client, prompt, reference_image_path=reference_image_path
            )
            image = export_4_3(raw_image, FINAL_SIZE)

        results.append(
            GeneratedIllustration(
                index=chunk.index,
                title=chunk.title,
                concept=concept,
                prompt=prompt,
                image=image,
            )
        )
        if on_progress:
            on_progress(chunk.index, total, "완료")

    return results


def generate_infographic_for_chunks(
    client: OpenAI | None,
    chunks: list[ContentChunk | ImageChunk],
    layout: str = "auto",
    reference_image_path: str | None = None,
    dry_run: bool = False,
    on_progress: ProgressCallback | None = None,
) -> list[GeneratedIllustration]:
    """Build one finished infographic slide per chunk: extract (term,
    description) items, generate one small icon per item, and compose them
    into a numbered-card / table / comparison layout with real Korean text.
    """
    results: list[GeneratedIllustration] = []
    total = len(chunks)

    for chunk in chunks:
        if on_progress:
            on_progress(chunk.index, total, "항목 추출 중...")

        if dry_run or client is None:
            if isinstance(chunk, ImageChunk):
                items = [{"term": "(이미지)", "description": "미리보기 모드에서는 이미지 내용을 읽을 수 없습니다"}]
            else:
                items = fallback_items_from_text(chunk.title, chunk.body)
        elif isinstance(chunk, ImageChunk):
            items = extract_items_from_image(client, chunk.image)
        else:
            items = extract_items_from_text(client, chunk.title, chunk.body)

        if not items:
            items = [{"term": chunk.title or "내용 없음", "description": ""}]

        icons: list[Image.Image | None] = []
        if not dry_run and client is not None:
            needed = 2 if layout == "comparison" or (layout == "auto" and len(items) == 2) else len(items)
            for item_index, item in enumerate(items[:needed]):
                if on_progress:
                    on_progress(chunk.index, total, f"아이콘 생성 중... ({item_index + 1}/{needed})")
                concept = concept_from_text(client, item["term"], item.get("description", ""))
                icons.append(generate_icon(client, concept, reference_image_path=reference_image_path))

        image = None
        if not dry_run and client is not None:
            if on_progress:
                on_progress(chunk.index, total, "레이아웃 조립 중...")
            image = render_layout(layout, items, icons)

        concept_summary = " / ".join(item["term"] for item in items)
        results.append(
            GeneratedIllustration(
                index=chunk.index,
                title=chunk.title,
                concept=concept_summary,
                prompt=f"[인포그래픽 항목]\n" + "\n".join(f"- {i['term']}: {i.get('description', '')}" for i in items),
                image=image,
            )
        )
        if on_progress:
            on_progress(chunk.index, total, "완료")

    return results
