import cv2
from skimage.metrics import structural_similarity as ssim

def verify_signature(sig1_path, sig2_path):
    img1 = cv2.imread(sig1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(sig2_path, cv2.IMREAD_GRAYSCALE)

    img1 = cv2.resize(img1, (300, 150))
    img2 = cv2.resize(img2, (300, 150))

    score, _ = ssim(img1, img2, full=True)

    return {
        "similarity_score": round(score * 100, 2),
        "match": score > 0.75
    }


def verify_signature(text):
    """
    Placeholder signature check
    """
    if "signature" in text.lower():
        return "Signature Found"
    return "No Signature Found"
