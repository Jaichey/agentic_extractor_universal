from rapidfuzz import fuzz
from datetime import datetime
import re

class DocumentComparator:
    def __init__(self, profile_data: dict, extracted_data: dict, document_type: str = None, threshold: int = 60):
        self.profile_data = profile_data
        self.document_data = extracted_data
        self.profile = self.normalize_profile_data(profile_data)
        self.extracted = self.flatten_nested(extracted_data)
        self.threshold = threshold
        self.document_type = document_type.lower() if document_type else None
        print(f"[DocumentComparator] Initialized with document type: {self.document_type} and threshold: {self.threshold}")
        # Document-specific field mappings
        self.document_field_mappings = {
            "aadhaar": {
                "name": ["Name", "Full Name", "Holder's Name"],
                'father_name': ['father_name', 'fatherName', 'father', 'Father', "Father's Name", "F/O", "S/O"],
                "date_of_birth": ["DOB", "Date of Birth", "Year of Birth"],
                "contact": ["Mobile", "Phone", "Contact Number", "Mobile:", "Phone Number", "Phone Numbers", "Contact","contact"],
                "address": ["Address", "Residential Address"],
                "aadhar_number": ["Aadhar No", "UID", "Unique ID", "Aadhaar Number", "Aadhaar No", "Aadhaar","aadhaar"],
            },
            "passport": {
                "name": ["Name", "Full Name", "Holder's Name"],
                'father_name': ['father_name', 'fatherName', 'father', 'Father', "Father's Name", "F/O", "S/O"],
                "date_of_birth": ["DOB", "Date of Birth"],
                "passport_number": ["Passport No", "Document Number"],
                "nationality": ["Nationality"],
                "place_of_birth": ["Place of Birth"]
            },
            "bonafide": {
                "name": ["Name", "Student Name"],
                'father_name': ['father_name', 'fatherName', 'father', 'Father', "Father's Name", "F/O", "S/O"],
                "university": ["University", "University Name"],
                "college": ["College", "College Name", "Institution"],
                "course": ["Course", "Degree"],
                "year": ["Year", "Academic Year"]
            }
            #We can add more document types as needed
        }
        
        # Default field mapping (used when no specific document type is specified)
        self.default_field_map = {
            "name": ["Name", "Full Name", "Holder's Name", "Student Name"],
            'father_name': ['father_name', 'fatherName', 'father', 'Father', "Father's Name", "F/O", "S/O"],
            "motherName": ["Mother", "Mother Name", "Mother's Name", "D/O"],
            "date_of_birth": ["DOB", "Date of Birth", "Birth Date", "Date of Issue","dob"],
            "contact": ["Mobile", "Phone", "Contact Number", "Mobile:"],
            "address": ["Address", "Residential Address"],
            "category": ["Category", "Caste", "Caste Category"],
            "previousSchool_College": ["School", "College", "Institution"],
            "YearOfPassing": ["Year of Passing", "Passing Year"],
            "Marks_Grade": ["Grade", "Marks", "Percentage"]
        }

    def get_field_map(self):
        """Return the appropriate field mapping based on document type"""
        if self.document_type and self.document_type in self.document_field_mappings:
            return self.document_field_mappings[self.document_type]
        return self.default_field_map

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
        """Flatten nested dictionary but keep only the last segment of the key"""
        items = {}
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self.flatten_nested(v, new_key, sep=sep))
            else:
                simple_key = new_key.split(sep)[-1]  # Keep only last part of the key
                items[simple_key] = v
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
            formats = [
                "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d", "%d %b %Y",
                "%d %B %Y", "%d-%b-%Y", "%d-%B-%Y", "%Y.%m.%d", "%d.%m.%Y"
            ]
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
        """Extract only digits from phone numbers, keep last 10 digits"""
        digits = re.sub(r'\D', '', phone_str)
        return digits[-10:] if len(digits) >= 10 else digits

    def normalize_name(self, name_str: str) -> str:
        """Clean names by removing extra codes/titles"""
        name = re.sub(r'[^a-zA-Z\s]', '', name_str)  # Remove special chars
        words = [w for w in name.split() if not (w.isupper() and len(w) < 5)]
        return ' '.join(words).lower()

    def find_best_match(self, profile_field: str):
        """Find the best matching extracted field value for a given profile field using substring matching"""
        field_map = self.get_field_map()
        candidate_keys = []

        if profile_field in field_map:
            candidate_keys.extend(field_map[profile_field])

        print(f"[DEBUG] Searching for profile field: '{profile_field}'")
        print(f"[DEBUG] Candidate keys from field map: {candidate_keys}")
        print(f"[DEBUG] Extracted keys available: {list(self.extracted.keys())[:10]}")  # show sample keys

        # Check all extracted keys if they contain any candidate key substring
        for candidate in candidate_keys:
            for k in self.extracted.keys():
                if candidate.lower() in k.lower():
                    val = self.extracted.get(k, "")
                    if isinstance(val, str) and val.strip():
                        print(f"[DEBUG] Match found for '{profile_field}': key='{k}', value='{val}'")
                        return val.strip()

        # Fallback: try keys containing profile_field itself
        for k in self.extracted.keys():
            if profile_field.lower() in k.lower():
                val = self.extracted.get(k, "")
                if isinstance(val, str) and val.strip():
                    print(f"[DEBUG] Fallback match for '{profile_field}': key='{k}', value='{val}'")
                    return val.strip()

        print(f"[DEBUG] No match found for '{profile_field}'")
        return ""

    def compare_fields(self):
        results = {}
        matched_fields = 0
        field_map = self.get_field_map()
        
        # Determine fields to compare based on document type or profile keys
        if self.document_type and self.document_type in self.document_field_mappings:
            fields_to_compare = list(field_map.keys())
        else:
            fields_to_compare = list(self.profile.keys())
            
        total_fields = len(fields_to_compare)

        for profile_field in fields_to_compare:
            if profile_field not in self.profile:
                continue
                
            profile_value = self.profile[profile_field]
            extracted_value = self.find_best_match(profile_field)
            cleaned_profile = self.clean_text(profile_value, profile_field)
            cleaned_extracted = self.clean_text(extracted_value, profile_field)

            # Log actual comparison values
            print(f"Comparing field: {profile_field}")
            print(f"  Profile Value (cleaned): '{cleaned_profile}'")
            print(f"  Extracted Value (cleaned): '{cleaned_extracted}'")

            # Skip empty profile values
            if not cleaned_profile:
                results[profile_field] = {
                    "profile_value": profile_value,
                    "extracted_value": extracted_value,
                    "similarity": 0,
                    "match": False
                }
                continue

            # Special comparison for dates (exact match)
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
            "document_type": self.document_type,
            "details": results
        }
