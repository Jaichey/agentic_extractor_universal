from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import base64, cv2, io
from extract_agent import ExtractionAgent
from compare_agent import DocumentComparator
from firebase_service import FirebaseService
from face_comparator import compare_faces
from flask_cors import CORS
import logging
from doc_validator import DocumentValidator
from PIL import Image
import numpy as np


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


# Initialize services
firebase_service = FirebaseService()
extraction_agent = ExtractionAgent()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_bytes_to_base64(image_bytes):
    """Convert image bytes (JPEG/PNG) to base64 string"""
    try:
        img_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img_np is None:
            logger.error("Failed to decode image bytes for base64 conversion")
            return None
        _, buffer = cv2.imencode('.jpg', img_np)
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error converting image bytes to base64: {str(e)}")
        return None
def bytes_to_base64_in_dict(d):
    if isinstance(d, dict):
        return {k: bytes_to_base64_in_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [bytes_to_base64_in_dict(i) for i in d]
    elif isinstance(d, bytes):
        return base64.b64encode(d).decode('utf-8')
    else:
        return d
    
def convert_ndarray_to_list(obj):
    if isinstance(obj, dict):
        return {k: convert_ndarray_to_list(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_ndarray_to_list(i) for i in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj


@app.route('/upload-and-verify', methods=['POST'])
def upload_and_verify():
    logger.info("Received upload request")

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    extra_img_file = request.files.get('face')
    user_id = request.form.get('uid')
    doc_type = request.form.get('docType')
    doc_number = request.form.get('docNumber')
    logger.info(f"Received docType: {doc_type}")

    if not user_id:
        return jsonify({'error': 'User ID (uid) is required'}), 400

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid or missing file'}), 400

    try:
        file_data = file.read()
        filename = file.filename

        # Get user profile
        profile_data = firebase_service.get_user_profile(user_id)
        if not profile_data:
            return jsonify({'error': 'User profile not found'}), 404

        # Process the main document bytes directly (no disk save)
        extracted_data = extraction_agent.process_bytes(file_data, filename)
        if not extracted_data:
            return jsonify({'error': 'Document processing failed'}), 400
        
        safe_extracted_data = bytes_to_base64_in_dict(extracted_data)


        def flatten_dict(d, parent_key='', sep='_'):
            items = {}
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict) and v is not None:
                    items.update(flatten_dict(v, new_key, sep=sep))
                else:
                    items[new_key] = v
            return items

        KEY_MAPPING = {
            "Personal Information_Full Name": "name",
            "Personal Information_Father's Name": "father_name",
            "Personal Information_Mother's Name": "mother_name",
            "Personal Information_Date of Birth": "date_of_birth",
            "Contact Information_Phone Number(s)": "contact",
            "Contact Information_Email Address(es)": "email",
            "Contact Information_Full Address": "full_address",
            "Document Identifiers_Aadhaar Number": "aadhaar_number",
            "Document Identifiers_PAN Number": "pan_number",
            "personal information_gender": "gender",
            "personal information_nationality": "nationality",
            "personal information_religion": "religion",
            "personal information_caste / Category": "category",
            "personal information_marital Status": "marital_status",
            "personal information_full Name": "name",
            "personal information_identification Marks": "id_marks",
            "personal information_father's Name": "father_name",
            "personal information_mother's Name": "mother_name",
            "personal information_date of Birth": "date_of_birth",
            "contact information_phone Number(s)": "contact",
            "contact information_email Address(es)": "email",
            "contact information_full Address": "full_address",
            "document identifiers_aadhaar Number": "aadhaar_number",
            "document identifiers_pan Number": "pan_number",
            "personal information_gender": "gender"
        }

        from datetime import datetime

        def normalize_personal_details(flat_details, key_mapping):
            normalized = {}
            for original_key, value in flat_details.items():
                mapped_key = key_mapping.get(original_key)
                if mapped_key:
                    if isinstance(value, list):
                        normalized[mapped_key] = value[0] if len(value) > 0 else None
                    else:
                        normalized[mapped_key] = value
            dob = normalized.get("date_of_birth")
            if dob:
                try:
                    dt = datetime.strptime(dob, "%d/%m/%Y")
                    normalized["date_of_birth"] = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
            return normalized

        raw_details = extracted_data.get("personal_details", {})
        flat_details = flatten_dict(raw_details)
        normalized_details = normalize_personal_details(flat_details, KEY_MAPPING)

        logger.info("=== Profile Data ===")
        logger.info(profile_data)
        logger.info("=== Extracted Raw Details ===")
        logger.info(extracted_data.get("personal_details", {}))
        logger.info("=== Normalized Document Data ===")
        logger.info(normalized_details)
        logger.info(f"Profile keys: {list(profile_data.keys())}")
        logger.info(f"Document keys: {list(extracted_data.get('personal_details', {}).keys())}")

        comparator = DocumentComparator(profile_data, normalized_details, doc_type)
        result = comparator.compare_fields()

        face_result = {"photoMatch": "no face detected", "faceSimilarity": None}
        face_images = {"document_face": None, "uploaded_face": None}
        
        

        validation = None
        if doc_type == 'aadhaar':
            validation = DocumentValidator.validate_aadhaar(doc_number)
        elif doc_type == 'pan':
            validation = DocumentValidator.validate_pan(doc_number)
        elif doc_type == 'passport':
            validation = DocumentValidator.validate_passport(doc_number)
        elif doc_type == 'driving_license':
            validation = DocumentValidator.validate_driving_license(doc_number)
        elif doc_type == 'caste_certificate':
            validation = DocumentValidator.validate_caste_certificate(doc_number)
        elif doc_type == 'voter_id':
            validation = DocumentValidator.validate_voter_id(doc_number)
        elif doc_type == 'income_certificate':
            validation = DocumentValidator.validate_income_certificate(doc_number)

        # Face comparison using in-memory bytes
        require_face_comparison = request.form.get('requireFaceComparison', 'false').lower() == 'true'
        if require_face_comparison and extra_img_file and extra_img_file.filename != '':
            uploaded_face_bytes = extra_img_file.read()
            face_images["uploaded_face"] = image_bytes_to_base64(uploaded_face_bytes)

            # For extracted face image, your extraction_agent should return face image bytes or base64
            # We'll assume extracted_data contains face image bytes under key "face_image_bytes"
            extracted_face_bytes = extracted_data.get("face_image_bytes")
            if extracted_face_bytes:
                face_images["document_face"] = image_bytes_to_base64(extracted_face_bytes)

                # Compare faces using your compare_faces function that supports bytes or paths
                # We must save temporarily or modify compare_faces to accept bytes. 
                # Here let's save to memory files using cv2.imdecode and then compare with bytes:

                # Decode images to numpy arrays
                np_uploaded_face = cv2.imdecode(np.frombuffer(uploaded_face_bytes, np.uint8), cv2.IMREAD_COLOR)
                np_extracted_face = cv2.imdecode(np.frombuffer(extracted_face_bytes, np.uint8), cv2.IMREAD_COLOR)

                if np_uploaded_face is not None and np_extracted_face is not None:
                    face_result = compare_faces(np_extracted_face, np_uploaded_face)
                    face_result = convert_ndarray_to_list(face_result)  # Convert ndarrays to lists
                    logger.info(f"Face comparison result: {face_result}")
                    
                else:
                    face_result["photoMatch"] = "invalid face images"
            else:
                face_result["photoMatch"] = "no face detected in document"

        response_data = {
            'results': [{
                'extracted_data': safe_extracted_data,
                'comparison_result': {
                    'verdict': result['verdict'],
                    'similarity_score': result.get('similarity_score', 0),
                    'details': result.get('details', {})
                },
                'face_comparison': face_result,
                'face_images': face_images,
                'file_name': filename,
                'document_type': doc_type,
                'document_number': doc_number,
                'personal_details': extracted_data.get("personal_details", {}),
                'validation': {
                    'status': validation[0] if validation else None,
                    'message': validation[1] if validation else "No validation performed"
                }
            }]
        }

        logger.info(f"Verification completed for user {user_id}")
        return jsonify(convert_ndarray_to_list(response_data))

    except Exception as e:
        logger.error(f"Error during verification: {str(e)}", exc_info=True)
        return jsonify({'error': 'Verification failed', 'details': str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
