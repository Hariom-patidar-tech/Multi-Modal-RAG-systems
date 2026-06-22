from pathlib import Path
import shutil


def save_uploaded_file(file, destination: str):
    """
    Save uploaded file to destination path
    """

    Path(destination).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(destination, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    return destination