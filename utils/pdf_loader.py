from pdf2image import convert_from_path
import os
import tempfile


def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)

    temp_dir = tempfile.mkdtemp()
    image_paths = []

    for i, img in enumerate(images):
        path = os.path.join(temp_dir, f"page_{i}.png")
        img.save(path, "PNG")
        image_paths.append(path)

    return image_paths
