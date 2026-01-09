import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

def preprocess_image(image_input):
    # ---------------- INPUT HANDLING ----------------
    # Accept NumPy array or file path
    if isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input).convert("RGB")
    elif isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise ValueError(f"Image not found at path: {image_input}")
        img = Image.open(image_input).convert("RGB")
    else:
        raise ValueError("Unsupported image input")

    # ---------------- RESIZE FOR OCR ----------------
    # Mild upscale helps OCR detect small fonts
    new_width = int(img.width * 1.5)
    new_height = int(img.height * 1.5)
    img = img.resize((new_width, new_height), Image.BICUBIC)

    # ---------------- GRAYSCALE & DENOISE ----------------
    gray = img.convert("L")
    # Median filter to reduce noise
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # ---------------- CONTRAST & SHARPEN ----------------
    gray = ImageOps.autocontrast(gray)
    # Extra contrast boost for OCR stability
    gray = ImageEnhance.Contrast(gray).enhance(2.0)
    # Optional sharpening to enhance text edges
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))

    # ---------------- ADAPTIVE-LIKE BINARIZATION ----------------
    gray_np = np.array(gray)
    mean_val = gray_np.mean()
    binarized = np.where(gray_np > mean_val - 10, 255, 0).astype(np.uint8)

    # ---------------- CONVERT BACK TO RGB ----------------
    processed = Image.fromarray(binarized).convert("RGB")

    return np.array(processed)
