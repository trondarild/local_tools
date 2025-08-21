#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A Python script to process markdown files with LaTeX-style citations.

This script reads markdown text from standard input, finds citations in the
format \cite{key1,key2,...}, and replaces them with numbered references.
It then appends a formatted bibliography to the end of the document.

The script requires a BibTeX file and a citation style as command-line arguments.

Usage:
cat my_document.md | python3 cite_md.py my_references.bib numbered > output.md
"""

import sys
import re
import argparse
from collections import OrderedDict

def parse_bib_file(filepath):
    """
    Parses a .bib file and returns a dictionary of entries.

    This is a simple parser and may not handle all BibTeX complexities,
    but it is robust enough for common entry types. It handles entries
    spanning multiple lines.

    Args:
        filepath (str): The path to the .bib file.

    Returns:
        dict: A dictionary where keys are citation keys and values are
              dictionaries of the BibTeX fields for that entry.
        Returns None if the file cannot be read.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Bib file not found at '{filepath}'", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: Could not read bib file '{filepath}': {e}", file=sys.stderr)
        return None

    entries = {}
    # Regex to find each BibTeX entry
    bib_entry_pattern = re.compile(r'@(\w+)\s*\{\s*([^,]+),', re.DOTALL)
    
    for match in bib_entry_pattern.finditer(content):
        entry_type = match.group(1).lower()
        cite_key = match.group(2).strip()
        
        # Find the content of this specific entry
        entry_start = match.end()
        brace_level = 1
        entry_content_str = ""
        for char in content[entry_start:]:
            if char == '{':
                brace_level += 1
            elif char == '}':
                brace_level -= 1
            if brace_level == 0:
                break
            entry_content_str += char
        
        # We only want the content within the braces
        entry_content_str = entry_content_str.rsplit('}', 1)[0]

        fields = {}
        # Regex to find key-value pairs within an entry
        field_pattern = re.compile(r'(\w+)\s*=\s*[\{"\'](.*?)[\}"\']\s*,?\s*$', re.MULTILINE)
        
        # Clean up lines and parse fields
        lines = entry_content_str.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            field_match = re.match(r'(\w+)\s*=\s*\{(.*)\},?', line)
            if field_match:
                key = field_match.group(1).strip().lower()
                # Remove extra braces and clean up value
                value = field_match.group(2).strip().replace('{', '').replace('}', '')
                fields[key] = value

        if fields:
            entries[cite_key] = fields
        else:
            print(f"Warning: Could not parse fields for entry '{cite_key}'", file=sys.stderr)

    return entries

def format_apa_authors(authors_string):
    """
    Formats an author string into APA-like style (Lastname, F. M.).
    
    Args:
        authors_string (str): The raw author string from the bib file,
                              e.g., "Albert Einstein and Isaac Newton".
    
    Returns:
        str: Formatted author string, e.g., "Einstein, A., Newton, I.".
    """
    if not authors_string:
        return "N/A"

    authors = [a.strip() for a in authors_string.split(' and ')]
    formatted_authors = []
    
    for author in authors:
        name_parts = author.split()
        if not name_parts:
            continue
        
        last_name = name_parts[-1]
        initials = [part[0] + '.' for part in name_parts[:-1]]
        
        formatted_authors.append(f"{last_name}, {' '.join(initials)}")
        
    return ', '.join(formatted_authors)


def format_numbered_reference(entry_data, number):
    """
    Formats a single bibliography entry into the 'numbered' style string.
    Author list is formatted in APA style.

    Args:
        entry_data (dict): The dictionary of fields for one citation.
        number (int): The citation number.

    Returns:
        str: A formatted reference string.
    """
    # Use .get() to avoid KeyErrors for missing fields
    authors_raw = entry_data.get('author', 'N/A')
    authors = format_apa_authors(authors_raw)
    
    year = entry_data.get('year', 'N/A')
    title = entry_data.get('title', 'N/A')
    journal = entry_data.get('journal', '')
    volume = entry_data.get('volume', '')
    number_field = entry_data.get('number', '')
    pages = entry_data.get('pages', '')

    # Build the reference string piece by piece
    ref_parts = [f"**[{number}]**", authors, f"({year}).", f"{title}."]
    
    if journal:
        ref_parts.append( '*' + journal + '*.')
    
    issue_info = ""
    if volume:
        issue_info += volume
    if number_field:
        issue_info += f"({number_field})"
    if issue_info:
        ref_parts.append(issue_info + ',')

    if pages:
        # Use en-dash for page ranges if possible
        pages = pages.replace('--', '–')
        ref_parts.append(f"pp. {pages}")

    return " ".join(filter(None, ref_parts))

# --- Style Formatter Dictionary ---
# To add a new style, create a new formatting function and add it here.
STYLE_FORMATTERS = {
    'numbered': format_numbered_reference,
}
# ------------------------------------

def main():
    """
    Main function to execute the script's logic.
    """
    parser = argparse.ArgumentParser(
        description="Process markdown files with LaTeX-style citations.",
        epilog="Example: cat doc.md | python3 cite_md.py refs.bib numbered > new_doc.md"
    )
    parser.add_argument("bib_file", help="Path to the .bib bibliography file.")
    parser.add_argument("style", help="The citation style to use.", choices=STYLE_FORMATTERS.keys())
    
    args = parser.parse_args()

    # 1. Parse the BibTeX file
    bib_data = parse_bib_file(args.bib_file)
    if bib_data is None:
        sys.exit(1) # Exit if bib file could not be parsed

    # 2. Read markdown from stdin
    try:
        markdown_text = sys.stdin.read()
    except Exception as e:
        print(f"Error: Could not read from standard input: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Find all citation keys in order of appearance
    cited_keys = OrderedDict()
    citation_pattern = re.compile(r'\\cite\{([^}]+)\}')
    for match in citation_pattern.finditer(markdown_text):
        keys_str = match.group(1)
        keys = [k.strip() for k in keys_str.split(',')]
        for key in keys:
            if key not in cited_keys:
                cited_keys[key] = None
    
    cited_keys_list = list(cited_keys.keys())

    # 4. Create a mapping from citation key to its number
    citation_map = {key: i + 1 for i, key in enumerate(cited_keys_list)}

    # 5. Replace inline citations
    def citation_replacer(match):
        keys_str = match.group(1)
        keys = [k.strip() for k in keys_str.split(',')]
        numbers = []
        for key in keys:
            if key in citation_map:
                numbers.append(str(citation_map[key]))
            else:
                print(f"Warning: Citation key '{key}' not found in bib file.", file=sys.stderr)
                numbers.append('?')
        return f"[{', '.join(numbers)}]"

    modified_text = citation_pattern.sub(citation_replacer, markdown_text)

    # 6. Generate the reference list using the selected style formatter
    references = []
    formatter = STYLE_FORMATTERS[args.style]
    for i, key in enumerate(cited_keys_list):
        number = i + 1
        if key in bib_data:
            formatted_ref = formatter(bib_data[key], number)
            references.append(formatted_ref)
        else:
            pass # Warning was already issued during replacement

    # 7. Print the final output
    print(modified_text)
    if references:
        print("\n\n## References")
        print("; ".join(references))


if __name__ == "__main__":
    main()
