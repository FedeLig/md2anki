import json
from pydantic import ValidationError
from llama_cpp import Llama 

from schemas import ExtractionResult

def extract_cards_llamacpp(text: str, model_path: str) -> ExtractionResult:
    """
    Extract Anki cards using llama.cpp and a local GGUF model.
    """
    # Load your model (Gemma, Qwen, etc.)
    # Note: Adjust n_gpu_layers and n_ctx based on your hardware
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=-1, 
        n_ctx=2048,
        verbose=False
    )
    
    try:
        # llama-cpp-python supports the OpenAI API structure natively
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract cards from this text:\n\n{text}"}
            ],
            # Here is where the magic happens:
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ExtractionResult",
                    "schema": ExtractionResult.model_json_schema()
                }
            },
            temperature=0.0
        )
        
        # Extract the raw JSON string from the response
        response_text = response["choices"][0]["message"]["content"]
        
        # Parse and validate via Pydantic
        data = json.loads(response_text)
        result = ExtractionResult.model_validate(data)
        return result

    except (json.JSONDecodeError, ValidationError, KeyError) as e:
        print(f"Extraction failed: {e}")
        return ExtractionResult(cards=[])

# --- Example Usage ---
if __name__ == "__main__":
    sample_text = "The quick brown fox jumps over the lazy dog. A cloze deletion test is an exercise consisting of a portion of language with certain items removed."
    
    # Point this to your downloaded GGUF file
    model_file = "./models/qwen2.5-7b-instruct-q4_k_m.gguf" 
    
    result = extract_cards_llamacpp(sample_text, model_path=model_file)
    
    for card in result.cards:
        print(f"[{card.card_type.upper()}] {card.front} -> {card.back}")
