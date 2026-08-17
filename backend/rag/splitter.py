# Step 2 of RAG: cut the long document text into smaller overlapping chunks.
# Small chunks give the AI focused context instead of a whole textbook.

CHUNK_SIZE = 1000      # characters per chunk
CHUNK_OVERLAP = 150    # characters repeated between chunks so sentences are not cut


def split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Return a list of text chunks."""
    clean_text = " ".join(text.split())  # remove extra spaces and newlines
    if not clean_text:
        return []

    chunks = []
    start = 0
    while start < len(clean_text):
        end = start + chunk_size
        chunks.append(clean_text[start:end])
        if end >= len(clean_text):
            break
        start = end - overlap  # step back a little to create the overlap

    return chunks
