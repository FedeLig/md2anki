from enum import Enum
from pydantic import BaseModel, Field

class CardType(str, Enum):
    QA = "qa"
    TERM_DEFINITION = "term_definition"
    CLOZE = "cloze"

class QualityFlag(str, Enum):
    MULTI_CONCEPT_CARD = "multi_concept_card"
    VAGUE_QUESTION = "vague_question"
    BACK_TOO_LONG = "back_too_long"
    LIST_NOT_CLOZE = "list_not_cloze"
    BAD_MATHJAX = "bad_mathjax"
    TOO_SIMPLE = "too_simple"
    HALLUCINATION_RISK = "hallucination_risk"

class AnkiCard(BaseModel):
    front: str = Field(min_length=1)
    back: str = Field(default="")
    card_type: CardType
    tags: list[str] = Field(default_factory=list)

class ExtractionResult(BaseModel):
    cards: list[AnkiCard] = Field(default_factory=list)
    
"""
class CardConfidenceScore(BaseModel):
    # LLM's self-evaluation of the card's quality
    front_quality: float = Field(ge=0.0, le=1.0, description="Quality of the question/front (0.0 to 1.0)")
    back_quality: float = Field(ge=0.0, le=1.0, description="Quality of the answer/back (0.0 to 1.0)")
    atomicity: float = Field(ge=0.0, le=1.0, description="How atomic/singular the concept is (0.0 to 1.0)")
    flags: list[QualityFlag] = Field(default_factory=list, description="Any detected issues with the card")
"""
