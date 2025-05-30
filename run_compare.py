from compare_agent import DocumentComparator
import json

# Load profile and extracted data
profile = json.load(open("profile.json"))
extracted = json.load(open("outputs/Aadhar.jpg.json"))  # change filename if needed

# Compare
comp = DocumentComparator(profile, extracted)
report = comp.compare_fields()

# Print verdict
print("\n==============================")
print(f"🧾 DOCUMENT VERDICT: {report['verdict'].upper()}")
print("==============================\n")

# Print detailed comparison
for field, info in report["details"].items():
    print(f"📌 Field: {field}")
    print(f"    Profile Value  : {info['profile_value']}")
    print(f"    Extracted Value: {info['extracted_value']}")
    print(f"    ✅ Match        : {'Yes' if info['match'] else 'No'}")
    print(f"    🔍 Similarity   : {info['similarity']}%\n")

print("==============================")
print(f"📊 Overall Similarity Score: {report['similarity_score']:.2f}%")
print("==============================\n")
