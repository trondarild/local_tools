#!/usr/bin/env python3.11
import os
import sys
import argparse
import base64
import requests
import json
from typing import List, Optional

# Set a reasonable timeout for API calls
API_TIMEOUT = 5*60  # 5 minutes

def get_gemini_api_key() -> str:
    """Get the Gemini API key from environment variable."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return api_key

def read_template(template_file: str) -> str:
    """Read the template file content."""
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: Template file '{template_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading template file: {e}", file=sys.stderr)
        sys.exit(1)

def get_pdf_list_from_stdin() -> List[str]:
    """Get a list of PDF filenames from stdin."""
    if sys.stdin.isatty():
        return []
    pdf_files = [line.strip() for line in sys.stdin if line.strip().lower().endswith('.pdf')]
    return pdf_files

def pdf_to_base64(pdf_path: str) -> Optional[str]:
    """Convert a PDF file to a base64 encoded string."""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: PDF file not found at '{pdf_path}'", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading or encoding PDF '{pdf_path}': {e}", file=sys.stderr)
        return None

def generate_mediawiki_for_pdf(pdf_path: str, template: str, api_key: str) -> Optional[str]:
    """
    Analyzes a PDF with Gemini and generates a MediaWiki entry from a template.
    """
    print(f"", file=sys.stderr)
    
    pdf_base64 = pdf_to_base64(pdf_path)
    if not pdf_base64:
        return None

    # Gemini API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt = f"""
Analyze the provided research paper PDF and generate a MediaWiki entry.

**Instructions:**

1.  **Determine Paper Type:** First, identify if the paper is an 'Original Research Study' (presents new experimental data) or a 'Review Article' (synthesizes existing research).

2.  **Extract Core Information:**
    * **Title:** The full title of the paper.
    * **Authors:** A comma-separated list of all authors.
    * **Year:** The year of publication.
    * **Journal:** The name of the journal where the paper was published.

3.  **Generate Key Takeaways:** This is the most critical step. Create a MediaWiki-formatted list based on the paper type.
    * **For an Original Research Study:** List the primary findings. Each finding must be on a new line formatted as:
        `* [[reports::{{A clear and concise summary of one specific finding}}]]`
    * **For a Review Article:** List the main subjects synthesized in the review and a key fact about each. Use this two-line format for each subject:
        `* [[has subject::{{Subject Name}}]]`
        `* [[{{Subject Name}}::{{A key fact, insight, or summary about this subject from the review}}]]`

4.  **Populate the Template:** Fill the extracted information into the placeholders (`{{TITLE}}`, `{{AUTHORS}}`, `{{YEAR}}`, `{{KEY_TAKEAWAYS}}`) in the provided template.

Note: the template block contains two placeholders: the first for a study, the second for a review paper; only use the appropriate one
Note: Text used for filling the [[reports::..]] and [[<subject name>::..]] fields should be concise and informative, max 180 characters.
**Template:**
---
{template}
---

Now, analyze the attached PDF and generate the complete MediaWiki page content.
"""

    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": pdf_base64
                    }
                }
            ]
        }],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 4096,
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            content = result['candidates'][0].get('content', {})
            if 'parts' in content and len(content['parts']) > 0:
                return content['parts'][0].get('text', '').strip()

        print(f"Warning: Unexpected API response format for '{pdf_path}'. Full response: {result}", file=sys.stderr)
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API for '{pdf_path}': {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred for '{pdf_path}': {e}", file=sys.stderr)
        return None

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Generate MediaWiki entries for research papers using the Gemini API.',
        epilog='Example: ls *.pdf | python3 create_pdf_entries.py --template my_template.txt'
    )
    parser.add_argument(
        '-t', '--template',
        required=True,
        help='Path to the MediaWiki entry template file.'
    )
    args = parser.parse_args()
    
    api_key = get_gemini_api_key()
    template = read_template(args.template)
    pdf_files = get_pdf_list_from_stdin()
    
    if not pdf_files:
        print("Error: No PDF files provided via stdin.", file=sys.stderr)
        print("Usage: ls *.pdf | python3 create_pdf_entries.py --template <template_file>", file=sys.stderr)
        sys.exit(1)
    
    print(f"\n", file=sys.stderr)
    
    for pdf_path in pdf_files:
        if not os.path.exists(pdf_path):
            print(f"\n", file=sys.stderr)
            continue

        # Each PDF gets its own MediaWiki page title
        page_title = os.path.basename(pdf_path).replace('_', ' ').replace('.pdf', '')
        
        entry = generate_mediawiki_for_pdf(pdf_path, template, api_key)
        
        if entry:
            print(f"== {page_title} ==")
            print(entry)
            print("\n" + "=" * 20 + "\n") # Separator for clarity in output
        else:
            print(f"\n", file=sys.stderr)

if __name__ == "__main__":
    main()
