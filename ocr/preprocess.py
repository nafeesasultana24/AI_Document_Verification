import cv2
import os
import numpy as np

def preprocess_image(image_path):
    # -------- Path validation --------
    if not isinstance(image_path, str):
        raise ValueError("Expected image file path, got file object")

    if not os.path.exists(image_path):
        raise ValueError(f"Image not found at path: {image_path}")

    # -------- Read image --------
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("OpenCV failed to load the image")

    # -------- Resize for better OCR --------
    img = cv2.resize(
        img,
        None,
        fx=1.5,
        fy=1.5,
        interpolation=cv2.INTER_CUBIC
    )

    # -------- Convert to grayscale --------
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # -------- Noise removal --------
    gray = cv2.bilateralFilter(gray, 9, 75, 75)

    # -------- Improve contrast & binarization --------
    processed = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        10
    )

    return processed
