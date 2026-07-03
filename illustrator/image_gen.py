from __future__ import annotations

import base64
import io

from openai import OpenAI
from PIL import Image

from illustrator.config import IMAGE_GEN_SIZE, IMAGE_MODEL


def generate_illustration(
    client: OpenAI,
    prompt: str,
    reference_image_path: str | None = None,
    size: str = IMAGE_GEN_SIZE,
) -> Image.Image:
    if reference_image_path:
        with open(reference_image_path, "rb") as ref_file:
            result = client.images.edit(
                model=IMAGE_MODEL,
                image=ref_file,
                prompt=prompt,
                size=size,
            )
    else:
        result = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            size=size,
            quality="high",
        )
    b64_data = result.data[0].b64_json
    return Image.open(io.BytesIO(base64.b64decode(b64_data)))
