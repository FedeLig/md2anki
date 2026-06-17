import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple

from markitdown import MarkItDown
from openai import OpenAI

# --- Configuration ---
CHARS_PER_TOKEN = 4  
DEFAULT_TOKEN_LIMIT = 512

@dataclass
class ExtractedDocument:
    source_path: str
    text: str
    chunks: Tuple[str, ...]
    file_type: str

# --- Text Processing Helpers ---
def preprocess_text(text: str) -> str:
    if not text:
        return ""
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line).strip()

def split_into_chunks(text: str, token_limit: int) -> List[str]:
    chunk_size = token_limit * CHARS_PER_TOKEN
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# --- Main Logic ---
def extract_text(
    file_path: str | Path,
    token_limit: int = DEFAULT_TOKEN_LIMIT,
) -> ExtractedDocument:
    
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    suffix = path.suffix.lower()
    raw_text = ""
    
    if suffix in [".txt", ".md"]:
        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        # --- The Qwen-VL Integration ---
        # Point the client to your local llama.cpp server
        client = OpenAI(
            base_url="http://localhost:8000/v1", 
            api_key="sk-local-qwen" # Required by the client, but ignored by your local server
        )
        
        # Initialize MarkItDown with the local Qwen client
        md = MarkItDown(
            llm_client=client, 
            llm_model="qwen2-vl-7b-instruct" # The name doesn't strictly matter for the local server, but good for logs
        )
        
        try:
            print(f"Processing {path.name} with MarkItDown + Qwen-VL...")
            result = md.convert(str(path))
            raw_text = result.text_content if result.text_content else ""
        except Exception as e:
            print(f"Extraction failed for {path.name}: {e}")

    text = preprocess_text(raw_text)
    chunks = split_into_chunks(text, token_limit=token_limit)

    return ExtractedDocument(
        source_path=str(file_path),
        text=text,
        chunks=tuple(chunks),
        file_type=suffix.lstrip(".")
    )

# Example Usage
if __name__ == "__main__":
    test_file = "sample.pdf" 
    
    if os.path.exists(test_file):
        document = extract_text(test_file)
        print("\n--- Extraction Complete ---")
        print(f"Total characters: {len(document.text)}")
    else:
        print(f"Please provide a valid file at {test_file} to test the pipeline.")