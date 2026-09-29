"""Stable, conservative identity for comparing imported problem stems."""

import html
import re
import unicodedata


_EXPORT_NOISE = re.compile(
    r"^\s*(?:得分\s*\d+(?:\.\d+)?\s*分?|\(?\s*\d+(?:\.\d+)?\s*分\s*\)?|"
    r"(?:作者|单位|创建提问|评测结果)\s*[:：]?.*|"
    r"答案(?:正确|错误)|https?://[^\s]*(?:pintia|pta)[^\s]*)\s*$",
    re.IGNORECASE,
)
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
_HTML_TAG = re.compile(r"</?([a-z][a-z0-9]*)(?:\s+[^<>]*)?\s*/?>", re.IGNORECASE)
_HTML_ENTITY = re.compile(r"&(?:#\d+|#x[\da-f]+|[a-z][a-z0-9]+);", re.IGNORECASE)
_TEX_DELIMITERS = re.compile(r"\\\[|\\\]|\\\(|\\\)|\${1,2}")
_TEX_COMMANDS = {
    r"\leq": "<=", r"\le": "<=", r"\geq": ">=", r"\ge": ">=",
    r"\neq": "!=", r"\ne": "!=", r"\times": "*", r"\cdot": "*",
    r"\div": "/", r"\pm": "+-", r"\mp": "-+", r"\approx": "~",
    r"\to": "->", r"\rightarrow": "->",
    r"\infty": "infinity", r"\in": "in", r"\notin": "notin",
}
_TEX_SPACING = re.compile(r"\\(?:[,;:!]|quad|qquad|enspace|thinspace|space)\s*")
_TEX_STYLE = re.compile(
    r"\\(?:text|mathrm|mathbf|mathit|operatorname|textrm)\s*\{([^{}]*)\}"
)
_CJK_SPACE = re.compile(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])")
_SPACE_AROUND_OPERATOR = re.compile(r"\s*([+\-*/=<>≤≥≠≈~^_|:%]+)\s*")


def normalize_problem_text(text):
    """Return a whole-stem comparison key, or ``None`` for non-text input.

    The key removes known display/export differences but does not shorten the
    stem or use a similarity threshold. Arithmetic, comparisons and grouping
    remain part of the identity.
    """
    if not isinstance(text, str):
        return None
    text = unicodedata.normalize("NFKC", html.unescape(text)).casefold()
    lines = [line for line in text.splitlines() if not _EXPORT_NOISE.match(line)]
    text = "\n".join(lines)
    text = re.sub(r"https?://[^\s)]*(?:pintia|pta)[^\s)]*", " ", text)

    # Keep the visible image label, while treating the Markdown destination as
    # presentation metadata; content identity is based on the problem wording.
    text = _IMAGE.sub(lambda match: f" image {match.group(1)} ", text)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"<\s*sup\s*>", "^", text)
    text = re.sub(r"<\s*sub\s*>", "_", text)
    text = re.sub(r"</\s*(?:sup|sub)\s*>", "", text)
    text = _HTML_TAG.sub(" ", text)
    text = _TEX_DELIMITERS.sub(" ", text)
    text = text.replace(r"\left", "").replace(r"\right", "")
    text = _TEX_SPACING.sub("", text)
    for source, target in _TEX_COMMANDS.items():
        text = text.replace(source, target)
    text = _TEX_STYLE.sub(r"\1", text)
    text = re.sub(r"\\(?:displaystyle|textstyle|scriptstyle|limits|nolimits)\b", "", text)
    text = re.sub(r"\\(?:,|;|:|!|quad|qquad|enspace|thinspace|space)\b", "", text)
    text = re.sub(r"\^\s*\{\s*([^{}]*)\s*\}", r"^\1", text)
    text = re.sub(r"_\s*\{\s*([^{}]*)\s*\}", r"_\1", text)
    # TeX grouping around a one-token superscript/subscript is not semantic.
    text = re.sub(r"([_^])\(([^()]*)\)", r"\1\2", text)
    text = _HTML_ENTITY.sub(lambda match: html.unescape(match.group(0)), text)
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = text.replace("×", "*").replace("·", "*").replace("÷", "/")
    text = text.replace("≤", "<=").replace("≥", ">=").replace("≠", "!=")

    # Preserve decimal points; other punctuation is editorial variation.
    output = []
    for index, char in enumerate(text):
        if char == "." and index and index + 1 < len(text) \
                and text[index - 1].isdigit() and text[index + 1].isdigit():
            output.append(char)
        elif char in "()[]{}+-*/=<>≤≥≠≈~^_|%":
            output.append(char)
        elif unicodedata.category(char)[0] not in {"P", "Z", "C"}:
            output.append(char)
        elif char.isspace():
            output.append(" ")
    text = "".join(output)
    text = _CJK_SPACE.sub("", text)
    text = _SPACE_AROUND_OPERATOR.sub(lambda match: match.group(1), text)
    return " ".join(text.split())


def problem_identity(text):
    """Named alias used at comparison call sites."""
    return normalize_problem_text(text)
