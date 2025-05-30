import os
import json
import shutil
from document_reader import DocumentProcessor
from local_llm import run_local_llm  # Your local LLM function to extract personal details from text
import cv2
import base64

class ExtractionAgent:
    output_base = os.path.join(os.getcwd(), 'extracted_data')
    os.makedirs(output_base, exist_ok=True)

    def __init__(self):
        self.processor = DocumentProcessor()
        self.supported_formats = ('.jpg', '.jpeg', '.png', '.pdf')

    def process_file(self, file_path, output_base=None):
        if output_base is None:
            output_base = self.output_base

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        doc_folder_name = file_name
        output_folder = os.path.join(output_base, doc_folder_name)
        os.makedirs(output_folder, exist_ok=True)

        photo_folder = os.path.join(output_folder, 'photos')
        data_folder = os.path.join(output_folder, 'data')
        os.makedirs(photo_folder, exist_ok=True)
        os.makedirs(data_folder, exist_ok=True)

        result = {
            "file_type": file_ext[1:].upper(),
            "faces": [],
            "signatures": [],
            "personal_details": {},
            "face_image_path": None  # Initialize this field
        }

        print(f"\n📄 Processing: {file_name}")

        # Extract text
        text = self.processor.extract_text(file_path)
        if text:
            print(f"📝 Extracted text preview:\n{text[:500]}...\n")
            result["personal_details"] = run_local_llm(text)
            print("✅ Data extracted successfully.")
        else:
            print("⚠️ No text found in the document.")

        # Handle visual elements
        if file_ext == ".pdf":
            images = self.processor.extract_pdf_images(file_path, photo_folder)
            for img_path in images:
                faces, sigs = self.processor.detect_face_signatures(img_path, photo_folder)
                # Store full paths
                result["faces"].extend(faces)
                result["signatures"].extend(sigs)
        else:
            dest_path = os.path.join(photo_folder, file_name)
            shutil.copy(file_path, dest_path)
            faces, sigs = self.processor.detect_face_signatures(dest_path, photo_folder)
            result["faces"] = faces
            result["signatures"] = sigs

        print("🖼️ Images extracted successfully.")
        print(f"👤 Faces detected: {len(result['faces'])} | ✍️ Signatures detected: {len(result['signatures'])}")

        # Handle face image path
        if result['faces']:
            result['face_image_path'] = result['faces'][0]  # Store full path
            print(f"📸 First face image saved at: {result['face_image_path']}")
            
            # Verify the image
            try:
                img = cv2.imread(result['face_image_path'])
                if img is not None:
                    print(f"Face image dimensions: {img.shape}")
                    # Convert to base64 for frontend
                    _, buffer = cv2.imencode('.jpg', img)
                    result['face_image_base64'] = base64.b64encode(buffer).decode('utf-8')
                else:
                    print("ERROR: Saved face image is invalid")
            except Exception as e:
                print(f"Face image verification failed: {str(e)}")

        # Save metadata
        with open(os.path.join(data_folder, 'personal_details.json'), 'w') as f:
            json.dump(result["personal_details"], f, indent=2)

        with open(os.path.join(data_folder, 'metadata.json'), 'w') as f:
            json.dump({
                "file_type": result["file_type"],
                "faces": [os.path.basename(f) for f in result["faces"]],
                "signatures": [os.path.basename(s) for s in result["signatures"]],
                "face_image_path": result.get("face_image_path")
            }, f, indent=2)

        print(f"✅ Process complete for: {file_name}")
        return result


    def batch_process(self, input_dir, output_dir=None):
        if output_dir is None:
            output_dir = self.output_base

        os.makedirs(output_dir, exist_ok=True)

        for file_name in os.listdir(input_dir):
            if file_name.lower().endswith(self.supported_formats):
                file_path = os.path.join(input_dir, file_name)
                print(f"Processing {file_name}...")
                self.process_file(file_path, output_dir)
        

if __name__ == "__main__":
    ExtractionAgent().batch_process("sample_docs", "extracted_data")
