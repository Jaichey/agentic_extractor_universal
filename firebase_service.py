import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict, Any
import os
import json

class FirebaseService:
    def __init__(self):
        try:
            firebase_credentials_json = os.environ["FIREBASE_CREDENTIALS_JSON"]
            firebase_creds_dict = json.loads(firebase_credentials_json)
            cred = firebase_credentials_json
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            self.db = None
    
    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.db:
            return None

        try:
            # Standard field mapping with fallbacks
            FIELD_MAPPING = {
                'name': ['name', 'fullName'],
                'father_name': ['father_name', 'fatherName', 'father'],
                'mother_name': ['mother_name', 'motherName', 'mother'],
                'date_of_birth': ['date_of_birth', 'dob', 'birthDate'],
                'contact': ['contact', 'phone', 'mobile', 'phoneNumber'],
                'address': ['address', 'fullAddress', 'residentialAddress'],
                'category': ['category', 'casteCategory', 'caste'],
                'previous_school': ['previous_school', 'previousSchool','previousSchool_College'],
                'year_of_passing': ['year_of_passing', 'passingYear','YearOfPassing'],
                'marks': ['marks', 'grades', 'percentage','Marks_Grade']
            }

            users_ref = self.db.collection("applications")
            query = users_ref.where("userId", "==", user_id).limit(1).stream()
            
            for doc in query:
                user_data = doc.to_dict()
                print(f"Raw Firestore data: {user_data}")
                
                # Build standardized response
                standardized_data = {}
                for standard_field, possible_names in FIELD_MAPPING.items():
                    for name in possible_names:
                        if name in user_data:
                            standardized_data[standard_field] = user_data[name]
                            break
                    else:
                        standardized_data[standard_field] = ""  # Default empty string
                
                print(f"Standardized user data: {standardized_data}")
                return standardized_data
                
            return None
        except Exception as e:
            print(f"Error fetching user data: {e}")
            return None

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        return self.get_user_data(user_id)

    # def save_verification_result(self, user_id: str, result: Dict) -> bool:
    #     try:
    #         doc_ref = self.db.collection("verifications").document()
    #         doc_ref.set({
    #             "user_id": user_id,
    #             "timestamp": firestore.SERVER_TIMESTAMP,
    #             "status": result.get("verdict", "pending"),
    #             "similarity_score": float(result.get("similarity_score", 0)),
    #             "details": result.get("details", {}),
    #             "document_type": result.get("document_type"),
    #             "document_number": result.get("document_number")
    #         })
    #         return True
    #     except Exception as e:
    #         print(f"Error saving verification: {e}")
    #         return False