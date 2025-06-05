import os
import cv2
import base64
import numpy as np
from io import BytesIO
from PIL import Image
import fitz  # PyMuPDF
from document_reader import DocumentProcessor
from local_llm import run_local_llm


class ExtractionAgent:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.pdf')

    def _image_to_bytes(self, img):
        """Encode OpenCV image to JPEG bytes."""
        success, buffer = cv2.imencode('.jpg', img)
        if not success:
            raise ValueError("Failed to encode image to JPEG")
        return buffer.tobytes()

    def process_bytes(self, file_data: bytes, filename: str):
        ext = os.path.splitext(filename)[1].lower()

        result = {
            "file_type": ext[1:].upper(),
            "faces": [],
            "signatures": [],
            "personal_details": {},
            "face_image_bytes": None,
            "face_image_base64": None
        }

        print(f"\n📄 Processing in-memory file: {filename}")

        try:
            # ------------------------------
            # PDF Processing (in-memory)
            # ------------------------------
            if ext == ".pdf":
                doc = fitz.open(stream=file_data, filetype="pdf")
                text = ""
                for page_num, page in enumerate(doc):
                    text += page.get_text()

                    # Use first page as image for face/signature detection
                    if page_num == 0:
                        pix = page.get_pixmap()
                        img_bytes = pix.tobytes("jpg")
                        img_np = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
                        if img_np is not None:
                            faces, sigs = self.processor.detect_face_signatures_from_image(img_np)
                            for face in faces:
                                result["faces"].append(self._image_to_bytes(face))
                            result["signatures"].extend(sigs)

            # ------------------------------
            # Image File Processing (in-memory)
            # ------------------------------
            elif ext in ['.jpg', '.jpeg', '.png']:
                img_np = cv2.imdecode(np.frombuffer(file_data, np.uint8), cv2.IMREAD_COLOR)
                if img_np is None:
                    raise ValueError("Could not decode image bytes.")
                # OCR text from image
                text = self.processor.ocr_image(img_np)
                faces, sigs = self.processor.detect_face_signatures_from_image(img_np)
                for face in faces:
                    result["faces"].append(self._image_to_bytes(face))
                result["signatures"].extend(sigs)

            else:
                raise ValueError("Unsupported file format")

            # ------------------------------
            # Run Local LLM for structured data
            # ------------------------------
            if text.strip():
                print(f"🧠 Extracting personal details via local LLM")
                result["personal_details"] = run_local_llm(text)
            else:
                print("⚠️ No text found for LLM processing.")

            # ------------------------------
            # First face encoding
            # ------------------------------
            if result['faces']:
                result['face_image_bytes'] = result['faces'][0]
                base64_str = base64.b64encode(result['face_image_bytes']).decode('utf-8')
                result['face_image_base64'] = f"data:image/jpeg;base64,{base64_str}"
                print("📸 First face encoded to base64.")

            print(f"✅ Finished in-memory processing for {filename}")
            return result

        except Exception as e:
            print(f"❌ Error in process_bytes: {e}")
            return None
