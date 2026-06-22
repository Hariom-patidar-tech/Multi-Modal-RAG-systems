import shutil
import os

CHROMA_PATH = "storage/chroma"

print("Resetting ChromaDB...")

if os.path.exists(CHROMA_PATH):
    shutil.rmtree(CHROMA_PATH)
    print("ChromaDB deleted successfully.")
else:
    print("ChromaDB directory not found.")

os.makedirs(CHROMA_PATH, exist_ok=True)

print("New ChromaDB directory created.")
print("Reset completed.")