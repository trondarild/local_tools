#!/usr/bin/env python3.11
import sys
import argparse
import ollama

def main():
    """
    Main function to run the LLM query.
    """
    parser = argparse.ArgumentParser(
        description="Query a local LLM via Ollama. Reads the prompt from stdin."
    )
    parser.add_argument(
        "-s", "--system",
        help="The system message to prepend to the user's prompt.",
        default="You are a helpful assistant. Provide concise and accurate answers."
    )
    parser.add_argument(
        "-m", "--model",
        help="The name of the Ollama model to use.",
        default="llama3"
    )
    args = parser.parse_args()

    # Read the user's prompt from standard input
    if sys.stdin.isatty():
        print("Error: No input provided via stdin.", file=sys.stderr)
        sys.exit(1)
    
    user_prompt = sys.stdin.read().strip()

    if not user_prompt:
        print("Error: Empty prompt received from stdin.", file=sys.stderr)
        sys.exit(1)

    # Construct the messages payload
    messages = [
        {
            'role': 'system',
            'content': args.system,
        },
        {
            'role': 'user',
            'content': user_prompt,
        },
    ]

    try:
        # Stream the response from Ollama
        stream = ollama.chat(
            model=args.model,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            print(chunk['message']['content'], end='', flush=True)
        print() # for a final newline

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
