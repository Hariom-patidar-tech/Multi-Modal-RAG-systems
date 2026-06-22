import re


def clean_text(text: str) -> str:
    """
    Basic text cleaning
    """

    if not text:
        return ""

    # Multiple spaces remove
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def remove_special_characters(text: str) -> str:
    """
    Remove unwanted special characters
    """

    return re.sub(
        r"[^a-zA-Z0-9\s.,!?()-]",
        "",
        text
    )


def normalize_text(text: str) -> str:
    """
    Normalize text for embeddings
    """

    text = clean_text(text)

    text = text.lower()

    return text


def truncate_text(
    text: str,
    max_length: int = 1000
) -> str:
    """
    Truncate long text
    """

    if len(text) <= max_length:
        return text

    return text[:max_length]


def word_count(text: str) -> int:
    """
    Count words
    """

    return len(text.split())


def is_empty_text(text: str) -> bool:
    """
    Check if text is empty
    """

    return len(text.strip()) == 0