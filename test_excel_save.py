import sys
sys.path.insert(0, 'src')

from cvstack.services.extractor import CVExtractor
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

# Simple test CV
test_cv = """
John Doe
Email: john.doe@example.com
Phone: +1-234-567-8900

EXPERIENCE
Software Engineer | Tech Corp | 2020 - 2023
- Developed Python applications
- Worked with SQL databases
- Used Docker for containerization

EDUCATION
Bachelor of Science in Computer Science
University of Technology, 2020

SKILLS
Python, SQL, Docker, Git
"""

print("=" * 60)
print("Testing CV Extraction and Excel Save")
print("=" * 60)

try:
    extractor = CVExtractor()
    print("\n✓ Extractor initialized")
    
    result = extractor.extract(test_cv)
    print("✓ Extraction completed")
    print(f"✓ Found {len(result.get('user_skills', []))} skills")
    
    print("\n" + "=" * 60)
    print("Check the output folder for the generated Excel file!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
