import re

def clean_text(text: str) -> str:
    """Sanitize extracted text, fix broken newlines, and remove duplicate whitespace."""
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("\x00", "")
    return text.strip()

def extract_sections(text: str) -> list:
    """
    Split text into coherent sections based on major markdown headings (## Section ... or ## ...).
    Keeps entire multi-clause sections together.
    """
    # Regex to capture major section headings
    section_pattern = re.compile(r"(?:^|\n)(#{1,3}\s+[^\n]+)", re.IGNORECASE)
    parts = section_pattern.split(text)

    sections = []
    current_title = "Overview / General"

    if len(parts) <= 1:
        return [{"section_title": current_title, "content": clean_text(text)}]

    # Leading content before first header
    if parts[0].strip():
        sections.append({"section_title": current_title, "content": clean_text(parts[0])})

    for i in range(1, len(parts), 2):
        raw_title = parts[i].strip()
        title = clean_text(raw_title).lstrip("#").strip()
        content = clean_text(parts[i+1]) if i + 1 < len(parts) else ""
        if content:
            sections.append({"section_title": title, "content": content})

    if not sections:
        sections.append({"section_title": current_title, "content": clean_text(text)})

    return sections
