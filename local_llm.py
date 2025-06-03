import requests
import json
import re

def run_local_llm(doc_text):
    if not doc_text.strip():
        return {"error": "No text found in document"}
    
    prompt = f"""
You are a highly intelligent document understanding assistant.

Your task is to extract *every possible identifiable and relevant detail* from a given block of unstructured or semi-structured text. This text may be from official Indian documents such as Aadhaar cards, school certificates, income certificates, caste certificates, government forms, ID cards, etc.

Please analyze the content and extract *all useful information, returning it in a clean and structured **JSON format*. Do not make up values—only return what is found in the document.

Include fields such as (but not limited to):

- Personal Information:
  - Full Name
  - Father's Name
  - Mother's Name
  - Date of Birth
  - Gender
  - Nationality
  - Religion
  - Caste / Category (SC/ST/OBC/General/etc.)
  - Marital Status
  - Identification Marks (if any)

- Contact Information:
  - Phone Number(s) — *only extract numbers that begin with 6, 7, 8, or 9* and are 10 digits long
  - Email Address(es)
  - Full Address

- Educational Details:
  - Institution Name
  - Exam or Class Name
  - Roll Number / Registration Number
  - Marks / Grades
  - Year of Passing
  - Certificate/Marksheet Number

- Document Identifiers:
  - Aadhaar Number
  - PAN Number
  - Certificate Numbers
  - Application/Reference Numbers
  - Issuing Authority
  - Issue Date and Place

- Income / Employment / Caste Information:
  - Occupation
  - Income Details
  - Caste/Tribe Name
  - Certificate Type (e.g., Caste Certificate, Income Certificate)
  - Validity Period (if any)

- Any additional key-value data or tabular information found.
- Images and Digital Signatures:
  - Describe any images or digital signatures found in the document.
  - Provide their locations or metadata if available.

Represent all information as structured JSON. Group related information into nested objects where appropriate. If information is not available, omit that field. Do not fabricate values.

Here is the content to analyze:
{doc_text}

Return structured JSON with fields for:
- Personal Information
- Contact Information 
- Educational Details
- Document Identifiers
- Employment/Income Details
"""

    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "messages": [
            {"role": "system", "content": "Extract structured personal data from documents."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            return {"error": f"API Error {response.status_code}"}

        raw_content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")

        # Attempt to extract only the JSON part from the response
        match = re.search(r'\{[\s\S]*\}', raw_content)
        if not match:
            return {
                "error": "No JSON object found in response.",
                "raw_response": raw_content[:500]
            }

        json_str = match.group(0)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {
                "error": "Failed to parse response as JSON.",
                "raw_json": json_str[:500]
            }
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {str(e)}"}