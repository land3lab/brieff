#!/usr/bin/env python3
"""Batch CLI for generating course illustrations.

Examples:
  python cli.py --input lecture01.pptx --output-dir out/lecture01 --embed
  python cli.py --text "이번 시간에는 데이터베이스 정규화를 배웁니다" --output-dir out/quick
  python cli.py --input lecture01.pptx --dry-run   # preview prompts, no API calls/cost
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from illustrator.config import OPENAI_API_KEY
from illustrator.content_extractor import extract_from_file, extract_from_text
from illustrator.pipeline import generate_for_chunks, generate_infographic_for_chunks
from illustrator.pptx_writer import embed_images


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="한국열린사이버대학교 교안 삽화 생성기")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="입력 파일 경로 (.pptx, .pdf, .docx, .txt)")
    source.add_argument("--text", help="직접 입력할 텍스트")
    parser.add_argument("--output-dir", default="output", help="생성된 이미지를 저장할 폴더")
    parser.add_argument(
        "--reference", default=None, help="스타일 참고용 레퍼런스 이미지 경로 (선택)"
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="--input이 .pptx일 때, 생성된 이미지를 슬라이드에 삽입한 사본을 함께 저장",
    )
    parser.add_argument(
        "--mascot",
        action="store_true",
        help="주제별 아이콘 스타일에 브리피 마스코트를 추가로 등장시켜 생성 (기본은 미포함)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API를 호출하지 않고 생성될 프롬프트만 미리 확인",
    )
    parser.add_argument(
        "--infographic",
        action="store_true",
        help="아이콘 단일 이미지 대신, 용어+설명+아이콘이 조합된 완성된 인포그래픽 슬라이드로 생성",
    )
    parser.add_argument(
        "--layout",
        choices=["auto", "numbered_cards", "table", "comparison"],
        default="auto",
        help="--infographic일 때 사용할 레이아웃 (기본: auto)",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.input:
        chunks = extract_from_file(args.input)
    else:
        chunks = extract_from_text(args.text)

    if not chunks:
        print("추출된 내용이 없습니다. 입력을 확인해주세요.", file=sys.stderr)
        return 1

    client = None
    if not args.dry_run:
        if not OPENAI_API_KEY:
            print(
                "OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 만들거나 "
                "환경변수를 설정하세요. (--dry-run으로 API 호출 없이 미리보기 가능)",
                file=sys.stderr,
            )
            return 1
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

    def report(index: int, total: int, stage: str) -> None:
        print(f"[{index + 1}/{total}] {stage}")

    if args.infographic:
        results = generate_infographic_for_chunks(
            client,
            chunks,
            layout=args.layout,
            reference_image_path=args.reference,
            dry_run=args.dry_run,
            on_progress=report,
        )
    else:
        results = generate_for_chunks(
            client,
            chunks,
            reference_image_path=args.reference,
            dry_run=args.dry_run,
            include_mascot=args.mascot,
            on_progress=report,
        )

    images_by_index = {}
    for item in results:
        prefix = f"slide_{item.index + 1:02d}"
        prompt_path = output_dir / f"{prefix}_prompt.txt"
        prompt_path.write_text(item.prompt, encoding="utf-8")
        if item.image is not None:
            image_path = output_dir / f"{prefix}.png"
            item.image.save(image_path)
            images_by_index[item.index] = item.image
            print(f"저장됨: {image_path}")
        else:
            print(f"저장됨 (프롬프트만): {prompt_path}")

    if args.embed and args.input and Path(args.input).suffix.lower() == ".pptx" and images_by_index:
        embedded_path = output_dir / f"{Path(args.input).stem}_with_illustrations.pptx"
        embed_images(args.input, images_by_index, embedded_path)
        print(f"삽화가 삽입된 PPT 저장됨: {embedded_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
