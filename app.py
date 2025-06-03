from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import tempfile, os, shutil, base64, cv2
from extract_agent import ExtractionAgent
from compare_agent import DocumentComparator
from firebase_service import FirebaseService
from face_comparator import compare_faces
from flask_cors import CORS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize services
firebase_service = FirebaseService()
extraction_agent = ExtractionAgent()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def image_to_base64(image_path):
    """Convert image file to base64 string with validation"""
    if not image_path or not os.path.exists(image_path):
        logger.error(f"Image path invalid or does not exist: {image_path}")
        return None
        
    try:
        # Read image with OpenCV to verify it's valid
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Invalid image file at {image_path}")
            return None
            
        # Convert to JPEG base64
        _, buffer = cv2.imencode('.jpg', img)
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
    except Exception as e:
        logger.error(f"Error converting image to base64: {str(e)}")
        return None

@app.route('/upload-and-verify', methods=['POST'])
def upload_and_verify():
    logger.info("Received upload request")

    # Validate request
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    extra_img_file = request.files.get('face')
    user_id = request.form.get('uid')
    doc_type = request.form.get('docType')
    doc_number = request.form.get('docNumber')
    
    if not user_id:
        return jsonify({'error': 'User ID (uid) is required'}), 400

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid or missing file'}), 400

    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(file_path)

        # Get user profile
        profile_data = firebase_service.get_user_profile(user_id)
        if not profile_data:
            return jsonify({'error': 'User profile not found'}), 404

        # Process document
        output_base = os.path.join(os.getcwd(), "extracted_data")
        extracted_data = extraction_agent.process_file(file_path, output_base)
        if not extracted_data:
            return jsonify({'error': 'Document processing failed'}), 400

        # Compare document data
        comparator = DocumentComparator(profile_data, extracted_data["personal_details"])
        result = comparator.compare_fields()

        # Initialize face comparison data
        face_result = {"photoMatch": "no face detected", "faceSimilarity": None}
        face_images = {"document_face": None, "uploaded_face": None}

        # Handle face comparison if required
        require_face_comparison = request.form.get('requireFaceComparison', 'false').lower() == 'true'
        if require_face_comparison and extra_img_file and extra_img_file.filename != '':
            uploaded_face_path = os.path.join(temp_dir, secure_filename(extra_img_file.filename))
            extra_img_file.save(uploaded_face_path)
            
            # Process uploaded face image
            face_images["uploaded_face"] = image_to_base64(uploaded_face_path)
            
            # Process extracted face image
            if extracted_data.get("face_image_path"):
                extracted_face_path = extracted_data["face_image_path"]
                face_images["document_face"] = image_to_base64(extracted_face_path)
                
                # Only compare if both images are valid
                if face_images["document_face"] and face_images["uploaded_face"]:
                    face_result = compare_faces(extracted_face_path, uploaded_face_path)
                    logger.info(f"Face comparison result: {face_result}")
                else:
                    face_result["photoMatch"] = "invalid face images"
            else:
                face_result["photoMatch"] = "no face detected in document"

        # Prepare response with personal details
        response_data = {
            'results': [{
                'extracted_data': extracted_data,  # This now includes personal_details
                'comparison_result': {
                    'verdict': result['verdict'],
                    'similarity_score': result.get('similarity_score', 0),
                    'details': result.get('details', {})
                },
                'face_comparison': face_result,
                'face_images': face_images,
                'file_name': file.filename,
                'document_type': doc_type,
                'document_number': doc_number,
                'personal_details': extracted_data.get("personal_details", {})  # Explicitly include
            }]
        }

        logger.info(f"Verification completed for user {user_id}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error during verification: {str(e)}", exc_info=True)
        return jsonify({'error': 'Verification failed', 'details': str(e)}), 500

    finally:
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
