import cv2
from deepface import DeepFace

def compare_faces(extracted_face_path, uploaded_face_path):
    try:
        # Verify the images can be loaded first
        img1 = cv2.imread(extracted_face_path)
        img2 = cv2.imread(uploaded_face_path)
        if img1 is None or img2 is None:
            return {
                "photoMatch": "error",
                "error": "Could not load one or both images"
            }

        # Use OpenCV backend for better compatibility
        result = DeepFace.verify(
            img1_path=extracted_face_path,
            img2_path=uploaded_face_path,
            detector_backend='opencv',
            model_name='Facenet',
            distance_metric='cosine',
            enforce_detection=True
        )
        
        return {
            "photoMatch": "success" if result["verified"] else "failed",
            "faceSimilarity": float(1 - result["distance"]),
            "faceDistance": float(result["distance"]),
            "threshold": float(result["threshold"]),
            "model": "Facenet",
            "backend": "opencv"
        }
    except Exception as e:
        return {
            "photoMatch": "error",
            "error": str(e)
        }