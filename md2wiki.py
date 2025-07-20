#!/usr/bin/env python3.11
import sys
import re

def convert_md_to_mediawiki_headings():
    """
    Reads lines from standard input, converts Markdown headings to MediaWiki
    headings, and prints the result to standard output.
    """
    for line in sys.stdin:
        # Regular expression to match Markdown headings:
        # ^(#+)\s*(.*)
        # ^      - start of the line
        # (#+)   - captures one or more '#' characters (group 1)
        # \s* - matches any whitespace (zero or more)
        # (.*)   - captures the rest of the line (the heading text) (group 2)
        match = re.match(r"^(#+)\s*(.*)", line)

        if match:
            num_hashes = len(match.group(1))  # Get the count of '#'
            heading_text = match.group(2).strip() # Get the heading text, remove leading/trailing whitespace

            # Construct the MediaWiki heading
            mediawiki_heading = "=" * num_hashes + " " + heading_text + " " + "=" * num_hashes
            print(mediawiki_heading)
        else:
            # If it's not a heading, print the line as is
            print(line, end='') # print() adds a newline by default, end='' prevents double newlines

if __name__ == "__main__":
    convert_md_to_mediawiki_headings()
