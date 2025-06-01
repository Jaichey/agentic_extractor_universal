# import firebase_admin
# from firebase_admin import credentials, firestore
# from typing import Optional, Dict, Any
# import os
# import json
# from dotenv import load_dotenv
# load_dotenv()

# class FirebaseService:
#     def __init__(self):
#         try:
#             # cred = credentials.Certificate({
#             #     "type": "service_account",
#             #     "project_id": os.getenv("FIREBASE_PROJECT_ID"),
#             #     "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
#             #     "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
#             #     "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
#             #     "client_id": os.getenv("FIREBASE_CLIENT_ID"),
#             #     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#             #     "token_uri": "https://oauth2.googleapis.com/token",
#             #     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#             #     "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
#             # })
#             cred  = credentials.Certificate("/etc/secrets/firebase-config.json")
#             if not firebase_admin._apps:
#                 firebase_admin.initialize_app(cred)
#                 print("Firebase initialized successfully.")
#             self.db = firestore.client()
#         except Exception as e:
#             print(f"Firebase initialization error: {e}")
#             self.db = None
    
#     def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
#         if not self.db:
#             return None

#         try:
#             # Standard field mapping with fallbacks
#             FIELD_MAPPING = {
#                 'name': ['name', 'fullName'],
#                 'father_name': ['father_name', 'fatherName', 'father'],
#                 'mother_name': ['mother_name', 'motherName', 'mother'],
#                 'date_of_birth': ['date_of_birth', 'dob', 'birthDate'],
#                 'contact': ['contact', 'phone', 'mobile', 'phoneNumber'],
#                 'address': ['address', 'fullAddress', 'residentialAddress'],
#                 'category': ['category', 'casteCategory', 'caste'],
#                 'previous_school': ['previous_school', 'previousSchool','previousSchool_College'],
#                 'year_of_passing': ['year_of_passing', 'passingYear','YearOfPassing'],
#                 'marks': ['marks', 'grades', 'percentage','Marks_Grade']
#             }

#             users_ref = self.db.collection("applications")
#             query = users_ref.where("userId", "==", user_id).limit(1).stream()
            
#             for doc in query:
#                 user_data = doc.to_dict()
#                 print(f"Raw Firestore data: {user_data}")
                
#                 # Build standardized response
#                 standardized_data = {}
#                 for standard_field, possible_names in FIELD_MAPPING.items():
#                     for name in possible_names:
#                         if name in user_data:
#                             standardized_data[standard_field] = user_data[name]
#                             break
#                     else:
#                         standardized_data[standard_field] = ""  # Default empty string
                
#                 print(f"Standardized user data: {standardized_data}")
#                 return standardized_data
                
#             return None
#         except Exception as e:
#             print(f"Error fetching user data: {e}")
#             return None

#     def get_user_profile(self, user_id: str) -> Optional[Dict]:
#         return self.get_user_data(user_id)

#     # def save_verification_result(self, user_id: str, result: Dict) -> bool:
#     #     try:
#     #         doc_ref = self.db.collection("verifications").document()
#     #         doc_ref.set({
#     #             "user_id": user_id,
#     #             "timestamp": firestore.SERVER_TIMESTAMP,
#     #             "status": result.get("verdict", "pending"),
#     #             "similarity_score": float(result.get("similarity_score", 0)),
#     #             "details": result.get("details", {}),
#     #             "document_type": result.get("document_type"),
#     #             "document_number": result.get("document_number")
#     #         })
#     #         return True
#     #     except Exception as e:
#     #         print(f"Error saving verification: {e}")
#     #         return False

import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict, Any
import os
import json
from dotenv import load_dotenv

load_dotenv()

class FirebaseService:
    def __init__(self):
        try:
            # Try multiple credential sources
            cred = self._get_firebase_credentials()
            
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully.")
            self.db = firestore.client()
        except Exception as e:
            print(f"Firebase initialization error: {e}")
            self.db = None
    
    def _get_firebase_credentials(self):
        """Try multiple ways to load Firebase credentials"""
        # 1. Try Render's secret file location
        render_secret_path = '/etc/secrets/firebase-config.json'
        if os.path.exists(render_secret_path):
            return credentials.Certificate(render_secret_path)
            
        # 2. Try local secret file (for development)
        local_secret_path = 'firebase-config.json'
        if os.path.exists(local_secret_path):
            return credentials.Certificate(local_secret_path)
            
        # 3. Try environment variables
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        if private_key:
            return credentials.Certificate({
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": private_key.replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
            })
            
        raise ValueError("No Firebase credentials found in secrets file, local file, or environment variables")

    def get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.db:
            return None

        try:
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
                
                standardized_data = {}
                for standard_field, possible_names in FIELD_MAPPING.items():
                    for name in possible_names:
                        if name in user_data:
                            standardized_data[standard_field] = user_data[name]
                            break
                    else:
                        standardized_data[standard_field] = ""
                
                print(f"Standardized user data: {standardized_data}")
                return standardized_data
                
            return None
        except Exception as e:
            print(f"Error fetching user data: {e}")
            return None

    def get_user_profile(self, user_id: str) -> Optional[Dict]:
        return self.get_user_data(user_id)

    def save_verification_result(self, user_id: str, result: Dict) -> bool:
        if not self.db:
            return False
            
        try:
            doc_ref = self.db.collection("verifications").document()
            doc_ref.set({
                "user_id": user_id,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "status": result.get("verdict", "pending"),
                "similarity_score": float(result.get("similarity_score", 0)),
                "details": result.get("details", {}),
                "document_type": result.get("document_type"),
                "document_number": result.get("document_number")
            })
            return True
        except Exception as e:
            print(f"Error saving verification: {e}")
            return False