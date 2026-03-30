# kadima/kb/models.py
"""M19: KB data models."""

from typing import Optional, Dict
from dataclasses import dataclass, field


@dataclass
class KBTerm:
    """Термин Knowledge Base: поверхность, лемма, определение, embedding."""

    id: Optional[int]
    surface: str
    canonical: str
    lemma: str
    pos: str
    features: Dict[str, str] = field(default_factory=dict)
    definition: Optional[str] = None
    embedding: Optional[bytes] = None
    source_corpus_id: Optional[int] = None
    freq: int = 0
    related_count: int = 0


@dataclass
class KBRelation:
    """Связь между терминами: синоним, гипероним, тематическая, embedding."""

    id: Optional[int]
    term_id: int
    related_term_id: int
    relation_type: str  # synonym | hypernym | thematic | embedding_similar
    similarity_score: float = 0.0
    related_surface: str = ""


@dataclass
class KBDefinition:
    """Определение термина: источник, верификация."""

    id: Optional[int]
    term_id: int
    definition_text: str
    source: str  # manual | llm_generated | imported
    llm_model: Optional[str] = None
    verified: bool = False
