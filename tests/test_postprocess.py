from PIL import Image

from illustrator.postprocess import crop_to_ratio, export_4_3


def test_crop_wide_image_to_4_3():
    image = Image.new("RGB", (1536, 1024))
    cropped = crop_to_ratio(image, (4, 3))
    assert cropped.size == (1365, 1024)
    assert abs(cropped.width / cropped.height - 4 / 3) < 0.01


def test_crop_tall_image_to_4_3():
    image = Image.new("RGB", (1000, 2000))
    cropped = crop_to_ratio(image, (4, 3))
    assert cropped.size == (1000, 750)


def test_crop_already_4_3_is_noop():
    image = Image.new("RGB", (800, 600))
    cropped = crop_to_ratio(image, (4, 3))
    assert cropped.size == (800, 600)


def test_export_4_3_resizes_to_target():
    image = Image.new("RGB", (1536, 1024))
    exported = export_4_3(image, (1600, 1200))
    assert exported.size == (1600, 1200)
