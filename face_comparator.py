# face_comparator.py

import face_recognition
import logging

def compare_faces(extracted_face_path, uploaded_face_path):
    try:
        # Load images with enhanced detection
        extracted_image = face_recognition.load_image_file(extracted_face_path)
        uploaded_image = face_recognition.load_image_file(uploaded_face_path)
        print(f"Comparing faces in {extracted_face_path} and {uploaded_face_path}")
        logging.info(f"Comparing faces in {extracted_face_path} and {uploaded_face_path}")
        
        # Increase detection parameters
        extracted_locations = face_recognition.face_locations(
            extracted_image,
            number_of_times_to_upsample=2,
            model="cnn"  # Use CNN model for better accuracy
        )
        uploaded_locations = face_recognition.face_locations(
            uploaded_image,
            number_of_times_to_upsample=2,
            model="cnn"
        )
        
        if not extracted_locations:
            return {
                "photoMatch": "no face detected in document",
                "faceSimilarity": None,
                "debug": "Could not locate face in document image"
            }
            
        if not uploaded_locations:
            return {
                "photoMatch": "no face detected in uploaded photo", 
                "faceSimilarity": None,
                "debug": "Could not locate face in supporting image"
            }
            
        # Get encodings for the largest face found
        extracted_encoding = face_recognition.face_encodings(
            extracted_image, 
            extracted_locations
        )[0]
        
        uploaded_encoding = face_recognition.face_encodings(
            uploaded_image,
            uploaded_locations
        )[0]
        
        # Compare faces with tolerance=0.5 for better accuracy
        distance = face_recognition.face_distance(
            [extracted_encoding], 
            uploaded_encoding
        )[0]
        similarity = float(1 - distance)
        
        return {
            "photoMatch": "success" if distance <= 0.5 else "failed",
            "faceSimilarity": similarity,
            "faceDistance": distance
        }
        print(f"Face comparison result: {distance} (similarity: {similarity})")
        
    except Exception as e:
        return {
            "photoMatch": "error",
            "error": str(e)
        }