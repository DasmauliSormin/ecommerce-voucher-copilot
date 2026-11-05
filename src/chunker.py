def word_aware_chunking(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Memotong teks secara terstruktur tanpa memotong kata di tengah-tengah."""
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 > chunk_size and current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            
            overlap_words = []
            overlap_len = 0
            for w in reversed(current_chunk):
                if overlap_len + len(w) + 1 <= overlap:
                    overlap_words.insert(0, w)
                    overlap_len += len(w) + 1
                else:
                    break
            
            current_chunk = overlap_words + [word]
            current_length = sum(len(w) + 1 for w in current_chunk)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks