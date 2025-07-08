#!/usr/bin/env python3.11
import os
import base64
import requests
import json
import fitz  # PyMuPDF
from pathlib import Path
import datetime
import sys
import argparse

c_timeout = 60*5

def get_gemini_api_key():
    """Get Gemini API key from environment variable"""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found!")
    return api_key

def pdf_to_base64(pdf_path):
    """Convert PDF to base64 for Gemini API"""
    with open(pdf_path, 'rb') as pdf_file:
        pdf_data = pdf_file.read()
        base64_data = base64.b64encode(pdf_data).decode('utf-8')
        return base64_data

def extract_pdf_text(pdf_path, max_pages=10):
    """Extract text from PDF as fallback"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        # Extract text from first few pages
        max_pages = min(max_pages, len(doc))
        for page_num in range(max_pages):
            page = doc[page_num]
            text += page.get_text() + "\n\n"
        
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def analyze_pdf_with_gemini(pdf_path, api_key, debug_print=print):
    """Send PDF to Gemini for analysis"""
    debug_print(f"Analyzing {os.path.basename(pdf_path)} with Gemini...")
    
    try:
        # Convert PDF to base64
        pdf_base64 = pdf_to_base64(pdf_path)
        
        # Prepare the request
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Create the prompt
        prompt = """
        Please analyze this research paper and provide:
        
        1. **Title and Authors**: Extract the full title and author list
        2. **Abstract Summary**: Summarize the main abstract in 2-3 sentences
        3. **Key Findings**: List 3-5 main findings or contributions
        4. **Methodology**: Briefly describe the research methods used
        5. **Theoretical Framework**: What theories or models does this work build on?
        6. **Implications**: What are the broader implications for the field?
        7. **Keywords**: List 8-10 key terms/concepts from the paper
        8. **publication Year**: Extract the year of publication

        IMPORTANT: Be very careful to extract the exact title, complete author names, and publication year as these will be used for academic citations. Look for these in the header, first page, or reference sections.


        Please format your response with clear headings and be concise but comprehensive.
        """
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": "application/pdf",
                                "data": pdf_base64
                            }
                        }
                    ]
                }
            ]
        }
        
        # Make the request
        response = requests.post(url, headers=headers, json=payload, timeout=c_timeout)
        
        if response.status_code == 200:
            result = response.json()
            debug_print(f"API Response structure: {list(result.keys())}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                debug_print(f"Candidate structure: {list(candidate.keys())}")
                
                if 'content' in candidate:
                    # New API format
                    if 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                        content = candidate['content']['parts'][0]['text']
                        return content
                elif 'parts' in candidate:
                    # Old API format
                    if len(candidate['parts']) > 0:
                        content = candidate['parts'][0]['text']
                        return content
                
                debug_print(f"Unexpected candidate structure: {candidate}")
                return None
            else:
                debug_print(f"No candidates in response: {result}")
                return None
        else:
            debug_print(f"API Error for {pdf_path}: {response.status_code}")
            debug_print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error analyzing {pdf_path}: {e}")
        return None

def synthesize_with_gemini(analyses, api_key, debug_print=print):
    """Use Gemini to synthesize the individual analyses"""
    debug_print("Synthesizing analyses with Gemini...")
    
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Combine all analyses
        combined_text = "\n\n---\n\n".join([
            f"PAPER {i+1} ANALYSIS:\n{analysis}" 
            for i, analysis in enumerate(analyses) if analysis
        ])
        
        synthesis_prompt = f"""
        Based on the following analyses of research papers, please create a comprehensive academic synthesis:

        {combined_text}

        Please provide:

        1. **Title**: Create an appropriate academic title that captures the main themes across all papers
        2. **Abstract**: Write a 150-200 word abstract summarizing the synthesis
        3. **Introduction**: Brief context and overview (1-2 paragraphs)
        4. **Common Themes**: What themes or concepts appear across multiple papers?
        5. **Methodological Approaches**: Compare and contrast the methods used
        6. **Theoretical Contributions**: How do these studies advance our understanding?
        7. **Convergent Findings**: What findings support or complement each other?
        8. **Divergent Perspectives**: Where do the studies differ or disagree?
        9. **Research Gaps**: What questions remain unanswered?
        10. **Future Directions**: What research directions do these studies suggest?
        11. **Conclusion**: What can we conclude when viewing these studies together?

        IMPORTANT FORMATTING REQUIREMENTS:
        - Use proper APA inline citations throughout (e.g., Author, Year)
        - Format as professional academic writing with clear sections
        - Use scholarly language and terminology; be neutral and objective - if anything be more critical, do not praise
        - At the end, provide a "References" section with full APA citations for each paper
        - Extract author names and publication years from the paper analyses to create proper citations
        """
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": synthesis_prompt
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=c_timeout)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                
                if 'content' in candidate:
                    # New API format
                    if 'parts' in candidate['content'] and len(candidate['content']['parts']) > 0:
                        content = candidate['content']['parts'][0]['text']
                        return content
                elif 'parts' in candidate:
                    # Old API format
                    if len(candidate['parts']) > 0:
                        content = candidate['parts'][0]['text']
                        return content
                
                debug_print(f"Unexpected synthesis candidate structure: {candidate}")
                return None
            else:
                debug_print("No synthesis content returned")
                return None
        else:
            debug_print(f"Synthesis API Error: {response.status_code}")
            debug_print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        debug_print(f"Error in synthesis: {e}")
        return None

def get_pdf_list_from_input():
    """Get PDF list from stdin (piped input) or return None"""
    if not sys.stdin.isatty():  # Check if input is piped
        pdf_files = []
        for line in sys.stdin:
            filename = line.strip()
            if filename and filename.endswith('.pdf'):
                pdf_files.append(filename)
        return pdf_files
    return None

def select_pdfs_for_analysis():
    """Select 3 representative PDFs from the directory"""
    pdf_files = [f for f in os.listdir('.') if f.lower().endswith('.pdf')]
    
    if len(pdf_files) < 3:
        print(f"Only {len(pdf_files)} PDFs found, need at least 3", file=sys.stderr)
        return pdf_files
    
    # Select 3 diverse papers for analysis
    # Try to get papers from different years and topics
    selected = []
    
    # Look for papers from different research areas
    keywords_to_find = ['attention', 'task switching', 'oscillations', 'decision', 'control']
    
    for keyword in keywords_to_find:
        if len(selected) >= 3:
            break
        for pdf in pdf_files:
            if keyword.lower() in pdf.lower() and pdf not in selected:
                selected.append(pdf)
                break
    
    # If we still need more, add any remaining PDFs
    while len(selected) < 3 and len(selected) < len(pdf_files):
        for pdf in pdf_files:
            if pdf not in selected:
                selected.append(pdf)
                break
    
    return selected[:3]


def main():
    parser = argparse.ArgumentParser(
        description='Synthesize research papers using Gemini AI',
        epilog='Example: ls *.pdf | gemini_pdf_synthesis.py > synthesis.md'
    )
    parser.add_argument(
        '-o', '--output', 
        help='Output file (if not specified, outputs to stdout)',
        default=None
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug output to stderr'
    )
    
    args = parser.parse_args()
    
    def debug_print(*msg):
        if args.debug:
            print(*msg, file=sys.stderr)
    
    debug_print("🧠 Gemini PDF Synthesis Tool")
    debug_print("=" * 50)
    
    # Check API key
    try:
        api_key = get_gemini_api_key()
        debug_print("✓ Gemini API key found")
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    
    # Get PDF list from piped input or directory
    pdf_list = get_pdf_list_from_input()
    if pdf_list:
        selected_pdfs = pdf_list
        debug_print(f"📄 Using {len(selected_pdfs)} PDFs from piped input")
    else:
        selected_pdfs = select_pdfs_for_analysis()
        debug_print(f"📄 Selected {len(selected_pdfs)} PDFs from directory")
    
    if len(selected_pdfs) < 2:
        print(f"❌ Need at least 2 PDFs, found {len(selected_pdfs)}", file=sys.stderr)
        return 1
    
    for pdf in selected_pdfs:
        debug_print(f"   - {pdf}")
    debug_print()
    
    # Analyze each PDF
    analyses = []
    for pdf_file in selected_pdfs:
        if not os.path.exists(pdf_file):
            debug_print(f"❌ File not found: {pdf_file}")
            analyses.append(None)
            continue
            
        analysis = analyze_pdf_with_gemini(pdf_file, api_key, debug_print)
        analyses.append(analysis)
        if analysis:
            debug_print(f"✓ Successfully analyzed {pdf_file}")
        else:
            debug_print(f"❌ Failed to analyze {pdf_file}")
    
    # Count successful analyses
    successful_analyses = [a for a in analyses if a is not None]
    debug_print(f"\n📊 Successfully analyzed {len(successful_analyses)}/{len(selected_pdfs)} papers")
    
    if len(successful_analyses) < 2:
        print("❌ Need at least 2 successful analyses for synthesis", file=sys.stderr)
        return 1
    
    # Synthesize
    synthesis = synthesize_with_gemini(successful_analyses, api_key, debug_print)
    if synthesis:
        debug_print("✓ Successfully generated synthesis")
    else:
        debug_print("❌ Failed to generate synthesis")
        return 1
    
    # Output synthesis
    if args.output:
        # Save to specified file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(synthesis)
        debug_print(f"\n📝 Synthesis saved to: {args.output}")
    else:
        # Output to stdout
        print(synthesis)
    
    debug_print("\n🎉 Analysis complete!")
    return 0

if __name__ == "__main__":
    main()
