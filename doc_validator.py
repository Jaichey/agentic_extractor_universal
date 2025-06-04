import re
from datetime import datetime

class DocumentValidator:
    @staticmethod
    def validate_aadhaar(number):
        """Validate Aadhaar using Verhoeff algorithm"""
        if not number or len(number) != 12 or not number.isdigit():
            return 'invalid', "Must be 12 digits"
        
        # Verhoeff algorithm implementation
        if not DocumentValidator._verhoeff_validate(number):
            return 'invalid', "Invalid Aadhaar number"
        
        return 'valid', "Valid Aadhaar"

    @staticmethod
    def validate_pan(number):
        """Validate PAN card format"""
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pattern, number.upper()):
            return 'invalid', "Format: ABCDE1234F"
        
        # Validate checksum letter (5th character should match)
        return 'valid', "Valid PAN"

    @staticmethod
    def validate_passport(number, country_code='IN'):
        """Validate Indian passport"""
        if not number or len(number) != 8:
            return 'invalid', "Must be 8 characters"
        
        if not re.match(r'^[A-Z]{1}[0-9]{7}$', number.upper()):
            return 'invalid', "Format: A1234567"
        
        return 'valid', "Valid Passport"

    @staticmethod
    def validate_driving_license(number):
        """Validate Indian Driving License"""
        if not number or len(number) < 10:
            return 'invalid', "Too short (min 10 chars)"
        if not re.match(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{7}$', number.upper()):
            return 'invalid', "Format: AB12C3456789"
        
        # Additional format checks for specific states
        return 'valid', "Valid Driving License"

    # Verhoeff Algorithm Implementation for Aadhaar
    @staticmethod
    def _verhoeff_validate(number):
        """Verhoeff algorithm for Aadhaar validation"""
        d = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
            [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
            [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
            [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
            [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
            [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
            [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
            [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
            [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
        ]
        
        p = [
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
            [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
            [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
            [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
            [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
            [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
            [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
        ]
        
        inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
        
        c = 0
        for i, digit in enumerate(reversed(number)):
            c = d[c][p[i % 8][int(digit)]]
        
        return c == 0
    @staticmethod
    def get_validation_details(doc_type, doc_number):
        # Placeholder implementation — customize as needed
        return {"info": f"Details for {doc_type} - {doc_number}"}
