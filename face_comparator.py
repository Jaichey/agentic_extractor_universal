import cv2
import numpy as np
import logging

def load_image(img_input):
    """
    Helper: load image from:
    - file path (str),
    - bytes (bytes),
    - numpy array (return as is)
    Returns grayscale numpy array or None.
    """
    if isinstance(img_input, str):
        img = cv2.imread(img_input, cv2.IMREAD_GRAYSCALE)
    elif isinstance(img_input, bytes):
        nparr = np.frombuffer(img_input, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    elif isinstance(img_input, np.ndarray):
        if len(img_input.shape) == 3:
            img = cv2.cvtColor(img_input, cv2.COLOR_BGR2GRAY)
        else:
            img = img_input
    else:
        logging.error(f"Unsupported input type for image: {type(img_input)}")
        return None
    return img


def compare_faces(extracted_face_input, uploaded_face_input):
    try:
        img1 = load_image(extracted_face_input)
        img2 = load_image(uploaded_face_input)

        if img1 is None or img2 is None:
            logging.error("One or both images could not be loaded.")
            return {"photoMatch": "error", "error": "Could not load images"}

        img1 = cv2.resize(img1, (250, 250))
        img2 = cv2.resize(img2, (250, 250))

        img1 = cv2.equalizeHist(img1)
        img2 = cv2.equalizeHist(img2)

        orb = cv2.ORB_create(nfeatures=1500)
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)

        if des1 is None or des2 is None:
            logging.warning("No features detected in one of the images.")
            return {"photoMatch": "error", "error": "No features detected"}

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        if not matches:
            return {"photoMatch": "failed", "faceSimilarity": 0.0, "method": "ORB_feature_matching"}

        matches = sorted(matches, key=lambda x: x.distance)
        top_matches = matches[:50]

        similarity = sum(m.distance for m in top_matches) / len(top_matches)
        normalized_similarity = max(0, 1 - (similarity / 100))

        result = {
            "photoMatch": "success" if normalized_similarity > 0.35 else "failed",
            "faceSimilarity": float(round(normalized_similarity * 100, 2)),  # percentage
            "method": "ORB_feature_matching"
        }

        logging.info(f"[compare_faces] result: {result}")
        return result

    except Exception as e:
        logging.exception("Error during face comparison")
        return {"photoMatch": "error", "error": str(e)}
