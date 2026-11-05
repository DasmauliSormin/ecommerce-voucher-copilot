import re

def clean_text(text: str) -> str:
    """Membersihkan teks SOP dari karakter ilegal dan spasi berlebih."""
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()