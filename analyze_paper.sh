#!/bin/bash

# Check if a PDF file is provided via stdin
if [ -t 0 ]; then
  echo "Error: Please provide a PDF filename via stdin." >&2
  echo "Usage: echo <pdf_filename> | ./analyze_paper.sh" >&2
  exit 1
fi

PDF_FILE=$(cat)
PROMPT_FILE="/Users/trond/code/local_tools/act_paper.md"

# Check if the PDF file exists
if [ ! -f "$PDF_FILE" ]; then
  echo "Error: PDF file '$PDF_FILE' not found." >&2
  exit 1
fi

# Check if the prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
  echo "Error: Prompt file '$PROMPT_FILE' not found." >&2
  exit 1
fi

# Execute the Python script
/usr/bin/env python3.11 /Users/trond/code/local_tools/query_gemini_with_pdf.py \
  --pdf-file "$PDF_FILE" \
  --prompt-file "$PROMPT_FILE"

