import cv2
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import fitz  # PyMuPDF

class DocumentProcessor:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        # Set your local tesseract path if needed
        #pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def extract_text(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        if ext == ".pdf":
            images = convert_from_path(file_path)
            for img in images:
                text += pytesseract.image_to_string(img, lang='eng')
        else:
            img = Image.open(file_path).convert('RGB')
            text = pytesseract.image_to_string(img, lang='eng')

        return text.strip()

    def is_valid_photo(self, base_img):
        # base_img is a dict with keys: width, height, colorspace, image
        width, height = base_img.get('width', 0), base_img.get('height', 0)
        if width < 100 or height < 100:
            return False
        aspect = max(width, height) / min(width, height)
        # colorspace: 1 = grayscale, 3 = RGB
        return aspect <= 2.0 and base_img.get('colorspace') in [1, 3]

    def extract_pdf_images(self, pdf_path, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        doc = fitz.open(pdf_path)
        extracted = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                base_img = doc.extract_image(xref)
                if self.is_valid_photo(base_img):
                    ext = base_img["ext"]
                    img_path = os.path.join(output_folder, f"photo_{page_num+1}_{img_index+1}.{ext}")
                    with open(img_path, "wb") as f:
                        f.write(base_img["image"])
                    extracted.append(img_path)
        doc.close()
        return extracted

    def detect_face_signatures(self, image_path, output_folder):
        img = cv2.imread(image_path)
        if img is None:
            return [], []

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5,
            minSize=(100, 100), flags=cv2.CASCADE_SCALE_IMAGE
        )

        signatures = self._find_signatures(gray)
        face_paths = []
        for i, (x, y, w, h) in enumerate(faces):
            face_path = os.path.join(output_folder, f"face_{i+1}.jpg")
            cv2.imwrite(face_path, img[y:y + h, x:x + w])
            face_paths.append(face_path)

        sig_paths = []
        for i, sig in enumerate(signatures):
            sig_path = os.path.join(output_folder, f"signature_{i+1}.jpg")
            cv2.imwrite(sig_path, sig)
            sig_paths.append(sig_path)

        return face_paths, sig_paths

    def _find_signatures(self, gray_img):
        blurred = cv2.GaussianBlur(gray_img, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        signatures = []

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if 500 < area < 2000 and 0.7 < (w / h) < 4.0 and y > gray_img.shape[0] * 0.6:
                signatures.append(gray_img[y:y + h, x:x + w])
        return signatures
