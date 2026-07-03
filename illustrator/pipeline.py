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
from illustrator.image_gen import generate_illustration
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
