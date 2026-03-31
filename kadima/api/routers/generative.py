# kadima/api/routers/generative.py
"""REST API router for generative modules (M13-M25).

Provides endpoints for on-demand generative processing:
transliteration, morphological generation, diacritization, NER, translation.
"""

import logging
from typing import List, Optional

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
    forms: List[MorphFormResponse]
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
    entities: List[EntityResponse]
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
