# Gate: Format Rendering Gate

Pass only if Markdown headings follow `STYLE.md`, LaTeX uses `$...$` and `$$...$$`, forbidden delimiters are absent, tables/diagrams are useful and not excessive, code blocks are readable, and final files are suitable for the requested environment.

For full study-pack exports, pass only if the delivery manifest lists the current lesson note, problem set, answer key, and package files, and no stale companion artifact is silently mixed into the final delivery.

When applying LaTeX/rendering cleanup, do not rewrite Mermaid, SQL, C/C++, Python, or other fenced code blocks unless that block itself is the target of the repair. Mermaid labels containing brackets, parentheses, formulas, punctuation, spaces, or bilingual text must be syntax-checked after edits.
