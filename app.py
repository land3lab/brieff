"""Personal-use Streamlit app: drop in a PPT / PDF / DOCX / text file, paste
text, or paste/upload a screenshot image, preview the generated illustration
for each slide, and download the images or a copy of the PPT with
illustrations embedded.

Run with: streamlit run app.py
"""
from __future__ import annotations

import io
import tempfile
from pathlib import Path

import streamlit as st
from openai import OpenAI
from PIL import Image
from streamlit_paste_button import paste_image_button

from illustrator.config import OPENAI_API_KEY
from illustrator.content_extractor import (
    ImageChunk,
    extract_from_docx,
    extract_from_pdf,
    extract_from_pptx,
    extract_from_text,
)
from illustrator.pipeline import generate_for_chunks
from illustrator.pptx_writer import embed_images

st.set_page_config(page_title="교안 삽화 생성기", page_icon="🩵", layout="wide")

EXTRACTORS = {
    ".pptx": extract_from_pptx,
    ".pdf": extract_from_pdf,
    ".docx": extract_from_docx,
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}

if "pasted_content_images" not in st.session_state:
    st.session_state.pasted_content_images = []
if "reference_image" not in st.session_state:
    st.session_state.reference_image = None
if "results" not in st.session_state:
    st.session_state.results = []
    st.session_state.source_pptx_path = None

st.title("🩵 한국열린사이버대학교 교안 삽화 생성기")
st.caption("PPT/PDF/DOCX/텍스트/캡처 이미지를 넣으면, 파란색 톤의 일관된 캐릭터 삽화를 4:3 비율로 자동 생성합니다.")

with st.sidebar:
    st.header("설정")
    api_key = st.text_input(
        "OpenAI API Key", value=OPENAI_API_KEY or "", type="password",
        help="환경변수 OPENAI_API_KEY 또는 .env로 미리 설정해두면 매번 입력하지 않아도 됩니다.",
    )
    include_mascot = st.checkbox("일관성 캐릭터(브리피) 포함", value=True)
    dry_run = st.checkbox(
        "미리보기 모드 (API 호출 없이 프롬프트만 확인, 비용 없음)", value=False
    )

    st.subheader("스타일 참고 이미지 (선택)")
    ref_upload_tab, ref_paste_tab = st.tabs(["파일 업로드", "클립보드 붙여넣기"])
    with ref_upload_tab:
        reference_file = st.file_uploader(
            "참고 이미지 파일", type=["png", "jpg", "jpeg"], key="reference_upload"
        )
        if reference_file is not None:
            st.session_state.reference_image = Image.open(reference_file)
    with ref_paste_tab:
        ref_paste_result = paste_image_button("📋 붙여넣기 (Ctrl+V로 복사한 이미지)", key="ref_paste")
        if ref_paste_result.image_data is not None:
            st.session_state.reference_image = ref_paste_result.image_data
    if st.session_state.reference_image is not None:
        st.image(st.session_state.reference_image, caption="적용될 참고 이미지", width=150)
        if st.button("참고 이미지 지우기"):
            st.session_state.reference_image = None
            st.rerun()

st.subheader("교안 내용 입력")
tab_file, tab_text, tab_paste = st.tabs(["파일/이미지 업로드", "텍스트 직접 입력", "캡처 이미지 붙여넣기"])

with tab_file:
    uploaded_file = st.file_uploader(
        "교안 파일 (.pptx, .pdf, .docx, .txt) 또는 슬라이드 이미지 (.png, .jpg)",
        type=["pptx", "pdf", "docx", "txt", "png", "jpg", "jpeg"],
    )

with tab_text:
    manual_text = st.text_area("빈 줄로 슬라이드를 구분해서 입력하세요", height=150)

with tab_paste:
    st.caption(
        "슬라이드를 캡처(Print Screen, Win+Shift+S 등)한 뒤 클립보드에 있는 상태에서 "
        "아래 버튼을 누르면 바로 추가됩니다. 여러 번 눌러 여러 장을 추가할 수 있습니다."
    )
    content_paste_result = paste_image_button("📋 캡처한 이미지 붙여넣기", key="content_paste")
    if content_paste_result.image_data is not None:
        st.session_state.pasted_content_images.append(content_paste_result.image_data)
    if st.session_state.pasted_content_images:
        st.write(f"추가된 캡처 이미지: {len(st.session_state.pasted_content_images)}장")
        preview_cols = st.columns(4)
        for i, img in enumerate(st.session_state.pasted_content_images):
            with preview_cols[i % 4]:
                st.image(img, use_container_width=True)
        if st.button("붙여넣은 이미지 모두 지우기"):
            st.session_state.pasted_content_images = []
            st.rerun()

generate_clicked = st.button("삽화 생성하기", type="primary")

if generate_clicked:
    has_input = uploaded_file or manual_text.strip() or st.session_state.pasted_content_images
    if not has_input:
        st.warning("파일을 업로드하거나 텍스트를 입력하거나 이미지를 붙여넣어주세요.")
        st.stop()
    if not dry_run and not api_key:
        st.warning("OpenAI API Key를 입력하거나 미리보기 모드를 사용하세요.")
        st.stop()

    reference_path = None
    if st.session_state.reference_image is not None:
        ref_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        st.session_state.reference_image.save(ref_tmp.name, format="PNG")
        reference_path = ref_tmp.name

    chunks = []
    source_pptx_path = None
    if uploaded_file is not None:
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix in IMAGE_SUFFIXES:
            chunks.append(ImageChunk(index=0, image=Image.open(uploaded_file)))
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(uploaded_file.getvalue())
            tmp.close()
            if suffix == ".txt":
                chunks = extract_from_text(Path(tmp.name).read_text(encoding="utf-8"))
            else:
                chunks = EXTRACTORS[suffix](tmp.name)
            if suffix == ".pptx":
                source_pptx_path = tmp.name
    elif manual_text.strip():
        chunks = extract_from_text(manual_text)

    for pasted_image in st.session_state.pasted_content_images:
        chunks.append(ImageChunk(index=len(chunks), image=pasted_image))

    if not chunks:
        st.error("추출된 내용이 없습니다. 입력 내용을 확인해주세요.")
        st.stop()

    client = None if dry_run else OpenAI(api_key=api_key)

    progress_bar = st.progress(0.0, text="시작 중...")

    def on_progress(index: int, total: int, stage: str) -> None:
        progress_bar.progress((index + 1) / total, text=f"{index + 1}/{total} - {stage}")

    with st.spinner("생성 중..."):
        results = generate_for_chunks(
            client,
            chunks,
            reference_image_path=reference_path,
            dry_run=dry_run,
            include_mascot=include_mascot,
            on_progress=on_progress,
        )
    progress_bar.empty()
    st.session_state.results = results
    st.session_state.source_pptx_path = source_pptx_path

results = st.session_state.results
if results:
    st.subheader("결과")
    columns = st.columns(2)
    images_by_index = {}
    for i, item in enumerate(results):
        with columns[i % 2]:
            st.markdown(f"**{item.index + 1}. {item.title or '(제목 없음)'}**")
            if item.image is not None:
                st.image(item.image, use_container_width=True)
                images_by_index[item.index] = item.image
                buf = io.BytesIO()
                item.image.save(buf, format="PNG")
                st.download_button(
                    "이미지 다운로드",
                    data=buf.getvalue(),
                    file_name=f"slide_{item.index + 1:02d}.png",
                    mime="image/png",
                    key=f"dl_{item.index}",
                )
            with st.expander("생성 프롬프트 보기"):
                st.text(item.prompt)

    if st.session_state.source_pptx_path and images_by_index:
        st.divider()
        if st.button("PPT에 삽화 삽입하여 다운로드용 파일 생성"):
            out_path = Path(tempfile.gettempdir()) / "with_illustrations.pptx"
            embed_images(st.session_state.source_pptx_path, images_by_index, out_path)
            with open(out_path, "rb") as f:
                st.download_button(
                    "삽화 삽입된 PPT 다운로드",
                    data=f.read(),
                    file_name="with_illustrations.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
