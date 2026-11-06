import re

class KnowledgeBaseCleaner:
    """Modul pembersihan teks (header/footer, hyphenation, spasi berlebih)."""

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        # 1. Menghilangkan karakter pembatas berulang (misal: ==== atau ----)
        text = re.sub(r"[-=]{3,}", "", text)

        # 2. Memperbaiki pemotongan kata di akhir baris (hyphenation: misal 'pen- \n jualan' -> 'penjualan')
        text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)

        # 3. Menghapus header / footer halaman yang umum (misal: "Halaman 1 dari 10" atau "Page 1")
        text = re.sub(r"(?i)halaman\s+\d+(\s+dari\s+\d+)?", "", text)
        text = re.sub(r"(?i)page\s+\d+(\s+of\s+\d+)?", "", text)

        # 4. Normalisasi newline berlebih (maksimal 2 newline berturut-turut)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. Normalisasi spasi horisontal ganda menjadi 1 spasi
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()