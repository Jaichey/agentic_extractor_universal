from rapidfuzz import fuzz
from datetime import datetime
import re

class DocumentComparator:
    def __init__(self, profile_data: dict, extracted_data: dict, threshold: int = 80):
        self.profile = self.normalize_profile_data(profile_data)
        self.extracted = self.flatten_nested(extracted_data)
        self.threshold = threshold

        # Field mapping between Firestore structure and document fields
        # Enhanced field mapping
        self.field_map = {
            "name": ["Name", "Full Name", "Holder's Name", "Student Name"],
            "fatherName": ["Father", "Father Name", "Father's Name", "S/O", "S/O:"],
            "motherName": ["Mother", "Mother Name", "Mother's Name", "D/O"],
            "date_of_birth": ["DOB", "Date of Birth", "Birth Date", "Date of Issue","dob"],
            "contact": ["Mobile", "Phone", "Contact Number", "Mobile:"],
            "address": ["Address", "Residential Address"],
            "category": ["Category", "Caste", "Caste Category"],
            "previousSchool_College": ["School", "College", "Institution",],
            "YearOfPassing": ["Year of Passing", "Passing Year"],
            "Marks_Grade": ["Grade", "Marks", "Percentage"]
        }

        # Enhanced clean_text method
    def clean_text(self, text: str, field_name: str) -> str:
        if not text or not isinstance(text, str):
            return ""
        
        text = text.strip()
    
        # Special handling for different field types
        if "date" in field_name.lower():
            return self.normalize_date(text)
        elif "phone" in field_name.lower() or "contact" in field_name.lower():
            return self.normalize_phone(text)
        elif "name" in field_name.lower():
        # Less aggressive cleaning for names
            return ' '.join([w for w in text.split() if w]).lower()
        
        return text.lower()

    def normalize_profile_data(self, profile_data: dict) -> dict:
        """Normalize Firebase profile data to consistent format"""
        normalized = {}
        for key, value in profile_data.items():
            if value is None:
                normalized[key] = ""
            elif isinstance(value, str):
                normalized[key] = value.strip()
            else:
                normalized[key] = str(value).strip()
        return normalized

    def flatten_nested(self, data, parent_key='', sep='/'):
        """Flatten nested dictionary from OCR extraction"""
        items = {}
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self.flatten_nested(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    def clean_text(self, text: str, field_name: str) -> str:
        """Clean and normalize text for comparison"""
        if not text or not isinstance(text, str):
            return ""
            
        text = text.strip()
        
        # Special handling for different field types
        if "date" in field_name.lower() or "dob" in field_name.lower():
            return self.normalize_date(text)
        elif "phone" in field_name.lower() or "contact" in field_name.lower():
            return self.normalize_phone(text)
        elif "name" in field_name.lower():
            return self.normalize_name(text)
            
        return text.lower()

    def normalize_date(self, date_str: str) -> str:
        """Normalize various date formats to YYYY-MM-DD"""
        try:
            formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d", "%d %b %Y"]
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            return date_str  # Return original if no format matched
        except:
            return date_str

    def normalize_phone(self, phone_str: str) -> str:
        """Extract only digits from phone numbers"""
        return re.sub(r'\D', '', phone_str)[-10:]  # Keep last 10 digits

    def normalize_name(self, name_str: str) -> str:
        """Clean names by removing extra codes/titles"""
        name = re.sub(r'[^a-zA-Z\s]', '', name_str)  # Remove special chars
        words = [w for w in name.split() if not (w.isupper() and len(w) < 5)]
        return ' '.join(words).lower()

    def find_best_match(self, profile_field: str):
        """More flexible field matching"""
        possible_keys = [profile_field]
    
        # Add mapped keys if available
        if profile_field in self.field_map:
            possible_keys.extend(self.field_map[profile_field])
    
        # Also try case-insensitive partial matches
        for key in self.extracted.keys():
            if profile_field.lower() in key.lower():
                possible_keys.append(key)
    
        # Find best match
        best_match = {"value": "", "score": 0}
        for key in possible_keys:
            if key in self.extracted:
                extracted_value = str(self.extracted[key])
                if extracted_value.strip():  # Only consider non-empty values
                    score = fuzz.ratio(profile_field.lower(), key.lower())
                    if score > best_match["score"]:
                        best_match = {"value": extracted_value, "score": score}
    
        return best_match["value"] if best_match["value"] else ""

    def compare_fields(self):
        results = {}
        matched_fields = 0
        total_fields = len(self.profile)

        for profile_field, profile_value in self.profile.items():
            extracted_value = self.find_best_match(profile_field)
            cleaned_profile = self.clean_text(profile_value, profile_field)
            cleaned_extracted = self.clean_text(extracted_value, profile_field)

            # Special comparison for dates
            if "date" in profile_field.lower() or "dob" in profile_field.lower():
                similarity = 100 if cleaned_profile == cleaned_extracted else 0
            else:
                similarity = fuzz.token_sort_ratio(cleaned_profile, cleaned_extracted)

            is_match = similarity >= self.threshold
            if is_match:
                matched_fields += 1

            results[profile_field] = {
                "profile_value": profile_value,
                "extracted_value": extracted_value,
                "similarity": similarity,
                "match": is_match
            }

        overall_score = (matched_fields / total_fields * 100) if total_fields else 0
        verdict = "correct" if overall_score >= self.threshold else "incorrect"

        return {
            "verdict": verdict,
            "similarity_score": round(overall_score, 2),
            "matched_fields": matched_fields,
            "total_fields": total_fields,
            "details": results
        }