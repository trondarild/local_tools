# Local LLM Tools

This repository contains a collection of Python scripts and shell scripts for interacting with local and remote Large Language Models (LLMs) to generate content for MediaWiki and perform document analysis.

## Scripts

### `askllm.py`

A command-line tool to query a local LLM via the Ollama interface.

**Usage:**

```bash
cat prompt.txt | ./askllm.py --model <model_name> --system "You are a helpful assistant."
```

*   **`--model`**: The name of the Ollama model to use (e.g., `llama3`).
*   **`--system`**: The system message to prepend to the user's prompt.

### `create_gemini_entries.py`

This script generates MediaWiki entries for a list of topics using the Gemini API. It reads topics from standard input and uses a template file to structure the output.

**Usage:**

```bash
cat topics.txt | ./create_gemini_entries.py --template entrytemplate.txt
```

*   **`--template`**: Path to the template file for the MediaWiki entry.

### `create_article_gemini_entries.py`

This script generates MediaWiki entries for research papers in PDF format using the Gemini API. It reads a list of PDF file paths from standard input and uses a template file to structure the output.

**Usage:**

```bash
ls *.pdf | ./create_article_gemini_entries.py --template paper_entry_template.txt
```

*   **`--template`**: Path to the template file for the MediaWiki entry.

### `query_gemini_with_pdf.py`

A generalized Python script to query the Gemini API with an attached PDF file and a prompt from a file. It can optionally include a template file in the prompt.

**Usage:**

```bash
python3 query_gemini_with_pdf.py --pdf-file <path_to_pdf> --prompt-file <path_to_prompt_file> [--template <path_to_template_file>]
```

*   **`--pdf-file`**: Path to the PDF file to analyze.
*   **`--prompt-file`**: Path to the file containing the prompt for Gemini.
*   **`--template`**: Optional: Path to a template file to be included in the prompt.

### `pdf2cat.sh`

A shell script that uses `query_gemini_with_pdf.py` to perform a category theory analysis of a research paper in PDF format. It takes the PDF filename from stdin, uses `act_paper.md` as the prompt, and outputs the analysis to stdout.

**Usage:**

```bash
echo "path/to/your/paper.pdf" | ./pdf2cat.sh
```

## Templates

This project uses template files to structure the generated MediaWiki content or to provide specific instructions for LLM queries.

*   **`entrytemplate.txt`**: A template for general topics. Used by `create_gemini_entries.py`.
*   **`paper_entry_template.txt`**: A template for academic papers (both research articles and reviews). Used by `create_article_gemini_entries.py`.
*   **`book-template-wiki.txt`**: A template for book entries in MediaWiki.
*   **`act_paper.md`**: A prompt file used by `analyze_paper.sh` to guide the Gemini model in performing a category theory analysis of a research paper.