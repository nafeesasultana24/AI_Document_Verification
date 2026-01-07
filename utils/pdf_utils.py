from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    image_paths = []

    os.makedirs("temp/pdf_images", exist_ok=True)

    for i, img in enumerate(images):
        path = f"temp/pdf_images/page_{i}.png"
        img.save(path, "PNG")
        image_paths.append(path)

    return image_paths
