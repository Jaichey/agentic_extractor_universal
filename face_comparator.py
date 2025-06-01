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
        img1 = cv2.resize(img1, (250, 250))
        img2 = cv2.resize(img2, (250, 250))
        
        # Apply histogram equalization to improve contrast
        img1 = cv2.equalizeHist(img1)
        img2 = cv2.equalizeHist(img2)
        
        # Initialize ORB detector
        orb = cv2.ORB_create(nfeatures=1000)
        
        # Find keypoints and descriptors
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return {"photoMatch": "error", "error": "No features detected"}
            
        # Create BFMatcher object
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Match descriptors
        matches = bf.match(des1, des2)
        
        if not matches:
            return {"photoMatch": "failed", "faceSimilarity": 0.0, "method": "ORB_feature_matching"}
            
        # Sort matches by distance
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Calculate similarity score based on top matches
        top_matches = matches[:50]
        similarity = sum(m.distance for m in top_matches) / len(top_matches)
        
        # Normalize and invert the score (lower distance = more similar)
        normalized_similarity = max(0, 1 - (similarity / 100))
        
        # More lenient threshold
        return {
            "photoMatch": "success" if normalized_similarity > 0.35 else "failed",
            "faceSimilarity": float(normalized_similarity),
            "method": "ORB_feature_matching"
        }
    except Exception as e:
        return {"photoMatch": "error", "error": str(e)}