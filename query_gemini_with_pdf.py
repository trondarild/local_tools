#!/usr/bin/env python3.11
import os
import sys
import argparse
import base64
import requests
import json
from typing import Optional

# Set a reasonable timeout for API calls
API_TIMEOUT = 5*60  # 5 minutes

def get_gemini_api_key() -> str:
    """Get the Gemini API key from environment variable."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return api_key

def read_file_content(file_path: str) -> str:
    """Read the content of a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}", file=sys.stderr)
        sys.exit(1)

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

def query_gemini_with_pdf(pdf_path: str, prompt_content: str, api_key: str, template_content: Optional[str] = None) -> Optional[str]:
    """
    Queries Gemini with a PDF and a given prompt, optionally including a template.
    """
    pdf_base64 = pdf_to_base64(pdf_path)
    if not pdf_base64:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    full_prompt = prompt_content
    if template_content:
        full_prompt += f"\n\n**Template:**\n---\n{template_content}\n---"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": full_prompt},
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
            "maxOutputTokens": 8192,
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
        description='Query Gemini with a PDF file and a prompt file.',
        epilog='Example: python3 query_gemini_with_pdf.py --pdf-file paper.pdf --prompt-file my_prompt.md --template my_template.txt'
    )
    parser.add_argument(
        '-p', '--pdf-file',
        required=True,
        help='Path to the PDF file to analyze.'
    )
    parser.add_argument(
        '-P', '--prompt-file',
        required=True,
        help='Path to the file containing the prompt for Gemini.'
    )
    parser.add_argument(
        '-t', '--template',
        required=False,
        help='Optional: Path to a template file to be included in the prompt.'
    )
    args = parser.parse_args()
    
    api_key = get_gemini_api_key()
    prompt_content = read_file_content(args.prompt_file)
    template_content = read_file_content(args.template) if args.template else None
    
    if not os.path.exists(args.pdf_file):
        print(f"Error: PDF file '{args.pdf_file}' not found.", file=sys.stderr)
        sys.exit(1)
    
    result = query_gemini_with_pdf(args.pdf_file, prompt_content, api_key, template_content)
    
    if result:
        print(result)
    else:
        print(f"Error: Could not get a response from Gemini for '{args.pdf_file}'.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
