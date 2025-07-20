#!/usr/bin/env python3.11

import sys
import argparse
import os
import requests
import json
from typing import List, Optional

max_length = 3000
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

def read_topics_from_stdin() -> List[str]:
    """Read topic titles from stdin."""
    topics = []
    for line in sys.stdin:
        topic = line.strip().strip('"').strip("'")
        if topic:
            topics.append(topic)
    return topics

def generate_entry_with_gemini(topic: str, sys_msg: str, api_key: str) -> Optional[str]:
    """Produce an answer for the given topic using Gemini API."""
    
    # Construct the prompt
    prompt = f"""

System message:
{sys_msg}

Request: 
{topic}

"""

    # Gemini API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # Request payload
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": max_length,
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        if 'candidates' in result and len(result['candidates']) > 0:
            if 'content' in result['candidates'][0]:
                if 'parts' in result['candidates'][0]['content']:
                    return result['candidates'][0]['content']['parts'][0]['text']
        
        print(f"Warning: Unexpected response format for topic '{topic}'", file=sys.stderr)
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Gemini API for topic '{topic}': {e}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Gemini API response for topic '{topic}': {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error for topic '{topic}': {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Generate answers using Gemini API')
    parser.add_argument('-s', '--system_message', required=False, help='The system message')
    parser.add_argument('-d', '--debug', required=False, help='Enable debug mode')

    args = parser.parse_args()
    
    # Get API key
    api_key = get_gemini_api_key()
    
    # Read template
    # template = read_template(args.template)
    default_sys_msg = """Use the supplied system message to create answers for the given requests.\ 
        Use neutral, tempered, and professional language, avoid any kind of terms indicating subjectivity like 'fascinating', 'intricate' and so on."""
    sys_msg = args.system_message if args.system_message else default_sys_msg
    # Read topics from stdin
    #topics = read_topics_from_stdin()
    topics = sys.stdin # read all lines as single topic so can process papers
    
    if not topics:
        print("Error: No topics provided via stdin", file=sys.stderr)
        sys.exit(1)
    
    # Generate entries for each topic
    for topic in topics:
        #print(f"<!-- Generating entry for: {topic} -->", file=sys.stderr)
        
        entry = generate_entry_with_gemini(topic, sys_msg, api_key)
        
        if entry:
            #print(f"== {topic} ==")
            print(entry)
            print()  # Add blank line between entries
        else:
            print(f"<!-- Failed to generate entry for: {topic} -->", file=sys.stderr)

if __name__ == "__main__":
    main()
