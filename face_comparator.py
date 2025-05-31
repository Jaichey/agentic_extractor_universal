import cv2
import numpy as np

def compare_faces(extracted_face_path, uploaded_face_path):
    try:
        # Load images in grayscale
        img1 = cv2.imread(extracted_face_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(uploaded_face_path, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return {"photoMatch": "error", "error": "Could not load images"}
            
        # Resize to same dimensions
        img1 = cv2.resize(img1, (128, 128))
        img2 = cv2.resize(img2, (128, 128))
        
        # ORB feature matching
        orb = cv2.ORB_create()
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return {"photoMatch": "error", "error": "No features detected"}
            
        # BFMatcher with default params
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        
        # Calculate similarity score
        similarity = sum(m.distance for m in matches) / len(matches) if matches else 100
        normalized_similarity = max(0, 100 - similarity) / 100
        
        return {
            "photoMatch": "success" if normalized_similarity > 0.5 else "failed",
            "faceSimilarity": float(normalized_similarity),
            "method": "ORB_feature_matching"
        }
    except Exception as e:
        return {"photoMatch": "error", "error": str(e)}