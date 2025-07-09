#!/bin/bash

#
# A script to extract text from a PDF, combine it with a system prompt,
# and send it to a hypothetical 'askllm' command-line tool.
#

# --- Configuration ---
# The file containing the system prompt (like the one in 'act_from_document').
PROMPT_FILE="/users/trond/code/local_tools/act_paper.md"

# --- Script Logic ---

# 1. Check that a PDF file was provided as an argument.
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path_to_your_pdf_file>"
    exit 1
fi

PDF_INPUT_FILE="$1"
# Create a descriptive output filename based on the input PDF name.
OUTPUT_FILE="${PDF_INPUT_FILE%.pdf}_category.md"

# 2. Verify that the required commands ('pdftotext' and 'askllm') exist.
if ! command -v pdftotext &> /dev/null; then
    echo "Error: The 'pdftotext' command was not found."
    echo "Please install the 'poppler-utils' package (e.g., 'sudo apt-get install poppler-utils' on Debian/Ubuntu)."
    exit 1
fi

if ! command -v askllm &> /dev/null; then
    echo "Error: The 'askllm' command is not available in your PATH."
    echo "This script assumes you have a working command-line LLM tool named 'askllm'."
    exit 1
fi

# 3. Check if the prompt file exists.
if [ ! -f "$PROMPT_FILE" ]; then
    echo "Error: Prompt file not found at '$PROMPT_FILE'"
    echo "Please save the system prompt to that file or update the PROMPT_FILE variable in this script."
    exit 1
fi


# 4. Read the entire system prompt from the file into a variable.
#    The '$(<...)' syntax is a clean way to read a file's content.
PROMPT_TEXT=$(<"$PROMPT_FILE")

# 5. Run the main command.
#    - 'pdftotext "$PDF_INPUT_FILE" -' extracts text from the PDF and prints it to standard output (-).
#    - The pipe '|' sends that text to the standard input of 'askllm'.
#    - 'askllm -s "$PROMPT_TEXT"' runs the LLM with the system prompt we loaded into the variable.
#    - '>' redirects the final output to our new markdown file.
echo "Processing '$PDF_INPUT_FILE'..."
pdftotext "$PDF_INPUT_FILE" - | askllm -s "$PROMPT_TEXT"  # > "$OUTPUT_FILE"

# 6. Check if the command was successful and print a final message.
if [ $? -eq 0 ]; then
    echo "Success! Category definition saved to '$OUTPUT_FILE'."
else
    echo "An error occurred during processing."
fi
