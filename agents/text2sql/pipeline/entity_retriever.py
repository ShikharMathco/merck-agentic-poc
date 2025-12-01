from pathlib import Path
from typing import List

def get_context_documents(folder_path: str) -> List[str]:
    """
    Reads all files in the given folder and returns their contents as a list of strings.
    """
    folder = Path(folder_path)
    context_docs = []
    for file_path in folder.glob("*"):  # all files in folder
        if file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8")
                context_docs.append(content)
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")
    return context_docs

# Example usage
context_folder = "context_input"
documents = get_context_documents(context_folder)
full_context = "\n\n".join(documents)  # merge into one string for your SQL prompt
print(full_context)
