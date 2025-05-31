# face_comparator.py
from deepface import DeepFace
import cv2
import base64
import numpy as np
import logging

def compare_faces(extracted_face_path, uploaded_face_path):
    try:
        logging.info(f"Comparing faces using DeepFace: {extracted_face_path} vs {uploaded_face_path}")

        # Validate image readability
        extracted_img = cv2.imread(extracted_face_path)
        uploaded_img = cv2.imread(uploaded_face_path)

        if extracted_img is None:
            return {
                "photoMatch": "no face detected in document",
                "faceSimilarity": None,
                "debug": "Could not read or decode face from document image"
            }

        if uploaded_img is None:
            return {
                "photoMatch": "no face detected in uploaded photo",
                "faceSimilarity": None,
                "debug": "Could not read or decode face from uploaded image"
            }

        # Analyze and compare using DeepFace (default model is 'VGG-Face')
        result = DeepFace.verify(
            img1_path=extracted_face_path,
            img2_path=uploaded_face_path,
            model_name="VGG-Face",         # Other options: "Facenet", "ArcFace", etc.
            detector_backend="opencv",     # Other options: "retinaface", "mediapipe"
            enforce_detection=False        # Prevents crash if face isn't detected
        )

        verified = result.get("verified", False)
        distance = result.get("distance", 1.0)
        similarity = 1 - distance if distance is not None else None

        return {
            "photoMatch": "success" if verified else "failed",
            "faceSimilarity": similarity,
            "faceDistance": distance,
            "debug": result
        }

    except Exception as e:
        logging.error(f"DeepFace error: {str(e)}")
        return {
            "photoMatch": "error",
            "faceSimilarity": None,
            "error": str(e)
        }
