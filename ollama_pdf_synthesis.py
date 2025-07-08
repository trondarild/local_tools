#!/usr/bin/env python3.11
import os
import requests
import json
import fitz  # PyMuPDF
from pathlib import Path
import datetime
import sys
import argparse
import time

c_timeout = 5*60

def check_ollama_server():
    """Check if Ollama server is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def get_available_models():
    """Get list of available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        return []
    except requests.exceptions.RequestException:
        return []

def extract_pdf_text(pdf_path, max_pages=20):
    """Extract text from PDF for analysis"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        # Extract text from first few pages
        max_pages = min(max_pages, len(doc))
        for page_num in range(max_pages):
            page = doc[page_num]
            page_text = page.get_text()
            if page_text.strip():  # Only add non-empty pages
                text += f"--- PAGE {page_num + 1} ---\n{page_text}\n\n"
        
        doc.close()
        
        # Limit text size to avoid overwhelming the model
        if len(text) > 50000:  # Approximately 50k characters
            text = text[:50000] + "\n\n[TEXT TRUNCATED - DOCUMENT CONTINUES...]"
        
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def analyze_pdf_with_ollama(pdf_path, model_name, debug_print=print):
    """Send PDF text to Ollama for analysis"""
    debug_print(f"Analyzing {os.path.basename(pdf_path)} with Ollama ({model_name})...")
    
    try:
        # Extract text from PDF
        pdf_text = extract_pdf_text(pdf_path)
        if not pdf_text.strip():
            debug_print(f"❌ No text extracted from {pdf_path}")
            return None
        
        debug_print(f"   Extracted {len(pdf_text)} characters from PDF")
        
        # Create the prompt
        prompt = f"""
Please analyze this research paper and provide:

1. **Title and Authors**: Extract the EXACT full title and complete author list (including first and last names)
2. **Publication Year**: Extract the publication year from the paper
3. **Abstract Summary**: Summarize the main abstract in 2-3 sentences
4. **Key Findings**: List 3-5 main findings or contributions
5. **Methodology**: Briefly describe the research methods used
6. **Theoretical Framework**: What theories or models does this work build on?
7. **Implications**: What are the broader implications for the field?
8. **Keywords**: List 8-10 key terms/concepts from the paper

IMPORTANT: Be very careful to extract the exact title, complete author names, and publication year as these will be used for academic citations. Look for these in the header, first page, or reference sections.

Please format your response with clear headings and be concise but comprehensive.

PAPER TEXT:
{pdf_text}
"""
        
        # Prepare the request for Ollama
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more focused analysis
                "num_ctx": 8192,     # Context window size
                "num_predict": 2048  # Max tokens to generate
            }
        }
        
        # Make the request
        debug_print(f"   Sending request to Ollama...")
        response = requests.post(url, json=payload, timeout=c_timeout)  # Longer timeout for local models
        
        if response.status_code == 200:
            result = response.json()
            if 'response' in result:
                content = result['response'].strip()
                if content:
                    debug_print(f"   ✓ Analysis complete ({len(content)} characters)")
                    return content
                else:
                    debug_print(f"   ❌ Empty response from model")
                    return None
            else:
                debug_print(f"   ❌ Unexpected response format: {result}")
                return None
        else:
            debug_print(f"   ❌ API Error: {response.status_code}")
            debug_print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        debug_print(f"Error analyzing {pdf_path}: {e}")
        return None

def synthesize_with_ollama(analyses, pdf_files, model_name, debug_print=print):
    """Use Ollama to synthesize the individual analyses"""
    debug_print(f"Synthesizing analyses with Ollama ({model_name})...")
    
    try:
        # Combine all analyses with paper filenames
        combined_text = "\n\n---\n\n".join([
            f"PAPER {i+1} (FILE: {pdf_files[i]}):\n{analysis}" 
            for i, analysis in enumerate(analyses) if analysis
        ])
        
        # Limit combined text size
        if len(combined_text) > 40000:
            combined_text = combined_text[:40000] + "\n\n[ANALYSES TRUNCATED...]"
        
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
- Use proper academic inline citations throughout (e.g., Author, Year)
- Format as professional academic writing with clear sections
- Use scholarly language and terminology
- Extract the actual paper titles, authors, and years from each analysis above
- Use the actual author names and years in your citations, NOT placeholders like "Paper 1 Author"
- At the end, provide a "References" section with proper citations for each paper
- Make sure to reference papers by their actual authors and years throughout the synthesis
"""
        
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": synthesis_prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,  # Slightly higher temperature for creative synthesis
                "num_ctx": 8192,     # Context window size
                "num_predict": 4096  # More tokens for synthesis
            }
        }
        
        debug_print("   Generating synthesis...")
        response = requests.post(url, json=payload, timeout=c_timeout)  # Even longer timeout for synthesis
        
        if response.status_code == 200:
            result = response.json()
            if 'response' in result:
                content = result['response'].strip()
                if content:
                    debug_print(f"   ✓ Synthesis complete ({len(content)} characters)")
                    return content
                else:
                    debug_print("   ❌ Empty synthesis response")
                    return None
            else:
                debug_print(f"   ❌ Unexpected synthesis response format: {result}")
                return None
        else:
            debug_print(f"   ❌ Synthesis API Error: {response.status_code}")
            debug_print(f"   Response: {response.text}")
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
        description='Synthesize research papers using local Ollama models',
        epilog='Example: ls *.pdf | python3 ollama_pdf_synthesis.py --model llama3.2 > synthesis.md'
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
    parser.add_argument(
        '-m', '--model',
        help='Ollama model to use (default: auto-detect best available)',
        default=None
    )
    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available Ollama models and exit'
    )
    
    args = parser.parse_args()
    
    def debug_print(*msg):
        if args.debug:
            print(*msg, file=sys.stderr)
    
    # Check if we should just list models
    if args.list_models:
        if not check_ollama_server():
            print("❌ Ollama server is not running. Start it with: ollama serve", file=sys.stderr)
            return 1
        
        models = get_available_models()
        if models:
            print("Available Ollama models:")
            for model in models:
                print(f"  - {model}")
        else:
            print("No models available. Pull a model with: ollama pull <model_name>")
        return 0
    
    debug_print("🦙 Ollama PDF Synthesis Tool")
    debug_print("=" * 50)
    
    # Check if Ollama server is running
    if not check_ollama_server():
        print("❌ Ollama server is not running!", file=sys.stderr)
        print("   Start it with: ollama serve", file=sys.stderr)
        return 1
    
    debug_print("✓ Ollama server is running")
    
    # Get available models
    available_models = get_available_models()
    if not available_models:
        print("❌ No Ollama models available!", file=sys.stderr)
        print("   Pull a model with: ollama pull llama3.2", file=sys.stderr)
        return 1
    
    # Choose model
    if args.model:
        if args.model in available_models:
            model_name = args.model
            debug_print(f"✓ Using specified model: {model_name}")
        else:
            print(f"❌ Model '{args.model}' not found!", file=sys.stderr)
            print(f"   Available models: {', '.join(available_models)}", file=sys.stderr)
            return 1
    else:
        # Auto-select best model
        preferred_models = ['llama3.2:latest', 'llama3.1:latest', 'llama2:latest', 'mistral:latest']
        model_name = None
        
        for preferred in preferred_models:
            if preferred in available_models:
                model_name = preferred
                break
        
        if not model_name:
            # Use first available model
            model_name = available_models[0]
        
        debug_print(f"✓ Auto-selected model: {model_name}")
    
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
            
        analysis = analyze_pdf_with_ollama(pdf_file, model_name, debug_print)
        analyses.append(analysis)
        if analysis:
            debug_print(f"✓ Successfully analyzed {pdf_file}")
        else:
            debug_print(f"❌ Failed to analyze {pdf_file}")
        
        # Small delay between requests to be gentle on the local server
        time.sleep(1)
    
    # Count successful analyses
    successful_analyses = [a for a in analyses if a is not None]
    debug_print(f"\n📊 Successfully analyzed {len(successful_analyses)}/{len(selected_pdfs)} papers")
    
    if len(successful_analyses) < 2:
        print("❌ Need at least 2 successful analyses for synthesis", file=sys.stderr)
        return 1
    
    # Synthesize
    # Get the corresponding PDF filenames for successful analyses
    successful_pdf_files = [selected_pdfs[i] for i, analysis in enumerate(analyses) if analysis is not None]
    synthesis = synthesize_with_ollama(successful_analyses, successful_pdf_files, model_name, debug_print)
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
