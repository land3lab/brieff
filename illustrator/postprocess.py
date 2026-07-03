"""gpt-image-1 does not offer a native 4:3 size, so we generate at the
closest supported wide size and center-crop + resize to an exact 4:3 frame.
"""
from __future__ import annotations

from PIL import Image


def crop_to_ratio(image: Image.Image, ratio: tuple[int, int] = (4, 3)) -> Image.Image:
    target_ratio = ratio[0] / ratio[1]
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = round(height * target_ratio)
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height))
    if current_ratio < target_ratio:
        new_height = round(width / target_ratio)
        top = (height - new_height) // 2
        return image.crop((0, top, width, top + new_height))
    return image.copy()


def export_4_3(image: Image.Image, target_size: tuple[int, int] = (1600, 1200)) -> Image.Image:
    cropped = crop_to_ratio(image, (4, 3))
    return cropped.resize(target_size, Image.LANCZOS)
