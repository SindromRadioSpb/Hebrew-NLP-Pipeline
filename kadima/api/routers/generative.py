# kadima/api/routers/generative.py
"""REST API router for generative modules (M13-M25).

Provides endpoints for on-demand generative processing:
transliteration, morphological generation, diacritization, NER, translation.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from kadima.engine.base import ProcessorStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generative", tags=["generative"])


# ── Request/Response schemas ────────────────────────────────────────────────

class TransliterateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Source text")
    mode: str = Field(default="latin", pattern=r"^(latin|phonetic|hebrew)$")


class TransliterateResponse(BaseModel):
    result: str
    source: str
    mode: str
    char_count: int


class MorphGenRequest(BaseModel):
    lemma: str = Field(..., min_length=1, description="Hebrew lemma")
    pos: str = Field(default="NOUN", description="Part of speech")
    binyan: str = Field(default="paal", description="Verb binyan")
    gender: str = Field(default="masculine", pattern=r"^(masculine|feminine)$")


class MorphFormResponse(BaseModel):
    form: str
    features: dict


class MorphGenResponse(BaseModel):
    lemma: str
    pos: str
    forms: list[MorphFormResponse]
    count: int


class DiacritizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Unvocalized Hebrew text")
    backend: str = Field(default="phonikud", pattern=r"^(phonikud|dicta|rules)$")


class DiacritizeResponse(BaseModel):
    result: str
    source: str
    backend: str
    char_count: int
    word_count: int


class NERRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Hebrew text")
    backend: str = Field(default="heq_ner", pattern=r"^(heq_ner|rules)$")


class EntityResponse(BaseModel):
    text: str
    label: str
    start: int
    end: int
    score: float


class NERResponse(BaseModel):
    entities: list[EntityResponse]
    count: int
    backend: str


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Source text")
    src_lang: str = Field(default="he", description="Source language code")
    tgt_lang: str = Field(default="en", description="Target language code")
    backend: str = Field(default="mbart", pattern=r"^(mbart|opus|dict)$")


class TranslateResponse(BaseModel):
    result: str
    source: str
    src_lang: str
    tgt_lang: str
    backend: str
    word_count: int


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/transliterate", response_model=TransliterateResponse)
async def transliterate(req: TransliterateRequest) -> TransliterateResponse:
    """Transliterate Hebrew ↔ Latin text."""
    from kadima.engine.transliterator import Transliterator

    proc = Transliterator()
    result = proc.process(req.text, {"mode": req.mode})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return TransliterateResponse(
        result=result.data.result,
        source=result.data.source,
        mode=result.data.mode,
        char_count=result.data.char_count,
    )


@router.post("/morph-gen", response_model=MorphGenResponse)
async def morph_gen(req: MorphGenRequest) -> MorphGenResponse:
    """Generate morphological forms from lemma + POS."""
    from kadima.engine.morph_generator import MorphGenerator

    proc = MorphGenerator()
    input_data = {"lemma": req.lemma, "pos": req.pos}
    config = {"binyan": req.binyan, "gender": req.gender}
    result = proc.process(input_data, config)
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    forms = [
        MorphFormResponse(form=f.form, features=f.features)
        for f in result.data.forms
    ]
    return MorphGenResponse(
        lemma=result.data.lemma,
        pos=result.data.pos,
        forms=forms,
        count=result.data.count,
    )


@router.post("/diacritize", response_model=DiacritizeResponse)
async def diacritize(req: DiacritizeRequest) -> DiacritizeResponse:
    """Add niqqud (vowel marks) to Hebrew text."""
    from kadima.engine.diacritizer import Diacritizer

    proc = Diacritizer()
    result = proc.process(req.text, {"backend": req.backend})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return DiacritizeResponse(
        result=result.data.result,
        source=result.data.source,
        backend=result.data.backend,
        char_count=result.data.char_count,
        word_count=result.data.word_count,
    )


@router.post("/ner", response_model=NERResponse)
async def ner(req: NERRequest) -> NERResponse:
    """Extract named entities from Hebrew text."""
    from kadima.engine.ner_extractor import NERExtractor

    proc = NERExtractor()
    result = proc.process(req.text, {"backend": req.backend})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    entities = [
        EntityResponse(
            text=e.text, label=e.label,
            start=e.start, end=e.end, score=e.score,
        )
        for e in result.data.entities
    ]
    return NERResponse(
        entities=entities,
        count=result.data.count,
        backend=result.data.backend,
    )


@router.post("/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest) -> TranslateResponse:
    """Translate text between Hebrew and other languages."""
    from kadima.engine.translator import Translator

    proc = Translator()
    config = {
        "backend": req.backend,
        "src_lang": req.src_lang,
        "tgt_lang": req.tgt_lang,
    }
    result = proc.process(req.text, config)
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return TranslateResponse(
        result=result.data.result,
        source=result.data.source,
        src_lang=result.data.src_lang,
        tgt_lang=result.data.tgt_lang,
        backend=result.data.backend,
        word_count=result.data.word_count,
    )


# ── M24 Keyphrase ────────────────────────────────────────────────────────────


class KeyphraseRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Hebrew text")
    top_n: int = Field(default=10, ge=1, le=50, description="Number of keyphrases")
    backend: str = Field(default="yake", pattern=r"^(yake|tfidf)$")


class KeyphraseResponse(BaseModel):
    keyphrases: list[str]
    scores: list[float]
    count: int
    backend: str


@router.post("/keyphrase", response_model=KeyphraseResponse)
async def keyphrase(req: KeyphraseRequest) -> KeyphraseResponse:
    """Extract keyphrases from Hebrew text (M24)."""
    from kadima.engine.keyphrase_extractor import KeyphraseExtractor

    proc = KeyphraseExtractor()
    result = proc.process(req.text, {"backend": req.backend, "top_n": req.top_n})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return KeyphraseResponse(
        keyphrases=result.data.keyphrases,
        scores=result.data.scores,
        count=len(result.data.keyphrases),
        backend=result.data.backend,
    )


# ── M23 Grammar Corrector ────────────────────────────────────────────────────


class GrammarRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Hebrew text to correct")
    backend: str = Field(default="llm", pattern=r"^(llm|rules)$")
    llm_url: str = Field(default="http://localhost:8081")


class CorrectionDetail(BaseModel):
    original: str
    corrected: str
    rule: str


class GrammarResponse(BaseModel):
    original: str
    corrected: str
    correction_count: int
    corrections: list[CorrectionDetail]
    backend: str


@router.post("/grammar", response_model=GrammarResponse)
async def grammar(req: GrammarRequest) -> GrammarResponse:
    """Correct grammar in Hebrew text (M23)."""
    from kadima.engine.grammar_corrector import GrammarCorrector

    proc = GrammarCorrector()
    result = proc.process(req.text, {"backend": req.backend, "llm_url": req.llm_url})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    corrections = [
        CorrectionDetail(
            original=c.original, corrected=c.corrected, rule=c.rule
        )
        for c in result.data.corrections
    ]
    return GrammarResponse(
        original=result.data.original,
        corrected=result.data.corrected,
        correction_count=result.data.correction_count,
        corrections=corrections,
        backend=result.data.backend,
    )


# ── M19 Summarizer ───────────────────────────────────────────────────────────


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Hebrew text to summarize")
    backend: str = Field(default="extractive", pattern=r"^(llm|mt5|extractive)$")
    max_sentences: int = Field(default=3, ge=1, le=10)
    llm_url: str = Field(default="http://localhost:8081")


class SummarizeResponse(BaseModel):
    original_length: int
    summary: str
    compression_ratio: float
    sentence_count: int
    backend: str


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest) -> SummarizeResponse:
    """Summarize Hebrew text (M19)."""
    from kadima.engine.summarizer import Summarizer

    proc = Summarizer()
    result = proc.process(
        req.text,
        {
            "backend": req.backend,
            "max_sentences": req.max_sentences,
            "llm_url": req.llm_url,
        },
    )
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return SummarizeResponse(
        original_length=result.data.original_length,
        summary=result.data.summary,
        compression_ratio=result.data.compression_ratio,
        sentence_count=result.data.sentence_count,
        backend=result.data.backend,
    )
