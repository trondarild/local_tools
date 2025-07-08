# Local LLM Tools

This repository contains a collection of Python scripts for interacting with local and remote Large Language Models (LLMs) to generate content for MediaWiki.

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

## Templates

This project uses template files to structure the generated MediaWiki content.

*   **`entrytemplate.txt`**: A template for general topics. Used by `create_gemini_entries.py`.
*   **`paper_entry_template.txt`**: A template for academic papers (both research articles and reviews). Used by `create_article_gemini_entries.py`.
*   **`book-template-wiki.txt`**: A template for book entries in MediaWiki.

