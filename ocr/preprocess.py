import os
import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

def preprocess_image(image_input):
    # ✅ Accept NumPy or file path
    if isinstance(image_input, np.ndarray):
        img = Image.fromarray(image_input).convert("RGB")
    elif isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise ValueError(f"Image not found at path: {image_input}")
        img = Image.open(image_input).convert("RGB")
    else:
        raise ValueError("Unsupported image input")

    # ✅ Mild upscale (helps OCR)
    img = img.resize(
        (int(img.width * 1.3), int(img.height * 1.3)),
        Image.BICUBIC
    )

    # ✅ Convert to grayscale (SAFE)
    gray = img.convert("L")

    # ✅ Very mild denoise
    gray = gray.filter(ImageFilter.MedianFilter(size=3))

    # ✅ Gentle contrast boost (SAFE)
    gray = ImageEnhance.Contrast(gray).enhance(1.6)

    # ✅ Convert BACK to RGB (CRITICAL FOR PADDLEOCR)
    processed = gray.convert("RGB")

    return np.array(processed)
