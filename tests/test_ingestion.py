from app.rag.chunker import create_chunks


def test_chunk_creation():

    text = """
    This is a sample document.
    """ * 100

    chunks = create_chunks(text)

    assert len(chunks) > 0
    assert isinstance(chunks, list)