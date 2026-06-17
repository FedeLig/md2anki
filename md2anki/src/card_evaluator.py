import logging
import re
from pydantic import BaseModel
import ollama # or llama_cpp

# Assuming you have the schemas from our previous steps
from schemas import AnkiCard, CardType, QualityFlag, ExtractionResult

logger = logging.getLogger(__name__)

# --- Regex Patterns (English & Italian) ---
_QUESTION_MARK_RE = re.compile(r"\?")
# Common question words to check if a QA front actually asks a question
_QUESTION_WORDS_RE = re.compile(
    r"\b(what|who|where|when|why|how|is|are|do|does|can|"
    r"che|chi|dove|quando|perché|come|quale|quanto|è|sono)\b", 
    re.IGNORECASE
)
# Matches bullet points or numbered lists (1., -, *)
_LIST_PATTERN_RE = re.compile(r"(?:\d+\.|[•\-\*])\s*\S")
# Words that often indicate multiple concepts are crammed into one card
_MULTI_CONCEPT_RE = re.compile(
    r"\b(and|furthermore|additionally|also|inoltre|nonché)\b", 
    re.IGNORECASE
)

class QualityReport(BaseModel):
    total_cards: int
    passed_cards: int
    critiqued_cards: int
    final_card_count: int

# --- 1. Programmatic Scoring ---

def get_card_flags(card: AnkiCard) -> list[QualityFlag]:
    """Check for bad patterns using English/Italian heuristics."""
    flags = []
    front_len = len(card.front)
    back_len = len(card.back)

    # Vague Question Check (Short front, no question mark, no question word)
    if card.card_type == CardType.QA:
        has_q_mark = bool(_QUESTION_MARK_RE.search(card.front))
        has_q_word = bool(_QUESTION_WORDS_RE.search(card.front))
        if front_len < 15 and not (has_q_mark or has_q_word):
            flags.append(QualityFlag.VAGUE_QUESTION)

    # Length Checks
    if back_len > 250:
        flags.append(QualityFlag.TOO_LONG_ANSWER)
    elif back_len < 5 and card.card_type != CardType.CLOZE:
        flags.append(QualityFlag.TOO_SIMPLE)

    # Format Checks: Did it generate a list instead of a cloze/atomic card?
    if card.card_type in (CardType.QA, CardType.TERM_DEFINITION):
        if _LIST_PATTERN_RE.search(card.back):
            flags.append(QualityFlag.LIST_NOT_CLOZE)

    return flags

def score_card(card: AnkiCard) -> float:
    """Returns a simple 0.0 to 1.0 confidence score."""
    score = 1.0
    flags = get_card_flags(card)
    
    # Deduct points for every issue found
    score -= (len(flags) * 0.25)
    
    # Severe penalty if Cloze card lacks Anki cloze syntax {{c1::...}}
    if card.card_type == CardType.CLOZE and "{{c" not in card.front:
        score -= 0.5 
        
    # Penalty if the back contains too many concepts joined by "and/inoltre"
    if card.back and _MULTI_CONCEPT_RE.search(card.back):
        score -= 0.15
        
    return max(0.0, score)

# --- 2. Local LLM Critique ---

def critique_bad_cards(bad_cards: list[AnkiCard], source_text: str, model_name: str = "llama3") -> list[AnkiCard]:
    """Ask the local LLM to rewrite only the low-quality cards."""
    if not bad_cards:
        return []

    bad_cards_text = "\n".join([f"- Q: {c.front} | A: {c.back}" for c in bad_cards])
    
    prompt = f"""You are an Anki expert. The following flashcards were generated from the text but are low quality (vague, too long, or poorly formatted):
{bad_cards_text}

Source text: {source_text}

Rewrite these into high-quality, concise cards. Keep the original language (English or Italian). Output strictly in the requested JSON format."""

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            format=ExtractionResult.model_json_schema(),
            options={"temperature": 0.2} # Low temp for fixing things
        )
        
        import json
        data = json.loads(response['message']['content'])
        result = ExtractionResult.model_validate(data)
        return result.cards
    except Exception as e:
        logger.error(f"Critique failed: {e}")
        return [] 

# --- 3. The Main Pipeline ---

def run_quality_pipeline(cards: list[AnkiCard], source_text: str, threshold: float = 0.75) -> tuple[list[AnkiCard], QualityReport]:
    """Filters bad cards and attempts to fix them."""
    passed_cards = []
    bad_cards = []

    for card in cards:
        if score_card(card) >= threshold:
            passed_cards.append(card)
        else:
            bad_cards.append(card)

    # Attempt to fix the bad ones via LLM
    fixed_cards = critique_bad_cards(bad_cards, source_text)

    # Note: You could run the fixed cards through `score_card` again to ensure 
    # the LLM actually fixed them, dropping them entirely if they fail twice.
    
    final_cards = passed_cards + fixed_cards
    
    report = QualityReport(
        total_cards=len(cards),
        passed_cards=len(passed_cards),
        critiqued_cards=len(bad_cards),
        final_card_count=len(final_cards)
    )

    return final_cards, report
