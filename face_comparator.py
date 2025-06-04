# face_comparator.py
import cv2
import numpy as np
import logging

def compare_faces(extracted_face_path, uploaded_face_path):
    try:
        img1 = cv2.imread(extracted_face_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(uploaded_face_path, cv2.IMREAD_GRAYSCALE)

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

        if not top_matches:
            return {"photoMatch": "failed", "faceSimilarity": 0.0, "method": "ORB_feature_matching"}

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