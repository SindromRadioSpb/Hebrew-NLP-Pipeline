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
    backend: str = Field(default="heq_ner", pattern=r"^(neodictabert|heq_ner|rules)$")
    device: str = Field(default="cpu", pattern=r"^(cpu|cuda)$")


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
    note: str = ""


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Source text")
    src_lang: str = Field(default="he", description="Source language code")
    tgt_lang: str = Field(default="en", description="Target language code")
    backend: str = Field(default="mbart", pattern=r"^(mbart|nllb|opus|dict)$")


class TranslateResponse(BaseModel):
    result: str
    source: str
    src_lang: str
    tgt_lang: str
    backend: str
    word_count: int


# ── Canonicalization schemas ────────────────────────────────────────────────


class CanonicalizeRequest(BaseModel):
    words: list[str] = Field(
        ..., min_length=1, max_length=1000,
        description="List of Hebrew words/surfaces to canonicalize",
    )
    use_hebpipe: bool = Field(default=True, description="Use HebPipe backend if available")


class CanonicalizeMappingResponse(BaseModel):
    surface: str
    canonical: str
    rules_applied: list[str]


class CanonicalizeResponse(BaseModel):
    mappings: list[CanonicalizeMappingResponse]
    count: int
    backend: str  # "hebpipe" or "rules"


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/canonicalize", response_model=CanonicalizeResponse)
async def canonicalize(req: CanonicalizeRequest) -> CanonicalizeResponse:
    """Canonicalize Hebrew surface forms: det removal, niqqud stripping, clitic decomposition.

    M6: Canonicalizer — приведение поверхностных форм к каноническим.
    Supports hebpipe (full lemma) and rule-based (det/final/niqqud/clitic) backends.
    """
    from kadima.engine.canonicalizer import Canonicalizer

    proc = Canonicalizer()
    input_words = list(set(req.words))  # deduplicate
    result = proc.process(input_words, {"use_hebpipe": req.use_hebpipe})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    backend = "hebpipe" if result.data.mappings and any(
        "hebpipe" in r for m in result.data.mappings for r in m.rules_applied
    ) else "rules"

    return CanonicalizeResponse(
        mappings=[
            CanonicalizeMappingResponse(
                surface=m.surface, canonical=m.canonical, rules_applied=m.rules_applied,
            )
            for m in result.data.mappings
        ],
        count=len(result.data.mappings),
        backend=backend,
    )


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
    result = proc.process(req.text, {"backend": req.backend, "device": req.device})
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
        note=result.data.note,
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


# ── M18 Sentiment Analyzer ───────────────────────────────────────────────────


class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Hebrew text")
    backend: str = Field(default="hebert", pattern=r"^(hebert|rules)$")


class SentimentResponse(BaseModel):
    label: str        # "positive" | "negative" | "neutral"
    score: float
    backend: str
    text_length: int


@router.post("/sentiment", response_model=SentimentResponse)
async def sentiment(req: SentimentRequest) -> SentimentResponse:
    """Analyse sentiment of Hebrew text (M18).

    Returns label (positive/negative/neutral), confidence score, and backend used.
    Falls back to rules if heBERT is not installed.
    """
    from kadima.engine.sentiment_analyzer import SentimentAnalyzer

    proc = SentimentAnalyzer()
    result = proc.process(req.text, {"backend": req.backend})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return SentimentResponse(
        label=result.data.label,
        score=result.data.score,
        backend=result.data.backend,
        text_length=result.data.text_length,
    )


# ── M20 QA Extractor ─────────────────────────────────────────────────────────


class QARequest(BaseModel):
    question: str = Field(..., min_length=1, description="Hebrew question")
    context: str = Field(..., min_length=1, description="Hebrew passage to search")
    backend: str = Field(default="alephbert", pattern=r"^(alephbert)$")


class QAResponse(BaseModel):
    answer: str
    score: float
    start: int
    end: int
    backend: str
    uncertainty: float


@router.post("/qa", response_model=QAResponse)
async def qa(req: QARequest) -> QAResponse:
    """Extract answer span from Hebrew context (M20 QA Extractor).

    Returns the extracted answer, confidence score, character offsets,
    and uncertainty (1-score) for active learning prioritisation.
    """
    from kadima.engine.qa_extractor import QAExtractor, QAInput

    proc = QAExtractor()
    input_data = QAInput(question=req.question, context=req.context)
    result = proc.process(input_data, {"backend": req.backend})
    if result.status != ProcessorStatus.READY:
        raise HTTPException(status_code=500, detail=result.errors)

    return QAResponse(
        answer=result.data.answer,
        score=result.data.score,
        start=result.data.start,
        end=result.data.end,
        backend=result.data.backend,
        uncertainty=result.data.uncertainty,
    )


# ── M15 TTS Synthesizer ──────────────────────────────────────────────────────


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Hebrew text to synthesize")
    backend: str = Field(default="auto", pattern=r"^(auto|f5tts|lightblue|phonikud|mms)$")
    device: str = Field(default="cpu", pattern=r"^(cpu|cuda)$")
    speaker_ref_path: str | None = Field(default=None, description="Path to speaker reference WAV for voice cloning")
    voice: str | None = Field(default=None, description="Voice name for LightBlue/Phonikud backends")
    use_g2p: bool = Field(default=True, description="Apply Hebrew G2P/niqqud preprocessing before synthesis")


class TTSResponse(BaseModel):
    audio_path: str | None
    backend: str
    backend_used: str
    text_length: int
    duration_seconds: float
    sample_rate: int
    note: str | None = None


@router.post("/tts", response_model=TTSResponse)
async def tts(req: TTSRequest) -> TTSResponse:
    """Synthesize Hebrew text to speech (M15 TTS Synthesizer).

    Returns audio file path on server and metadata.
    Backend auto-selects: F5-TTS → LightBlue → Phonikud/Piper ONNX → MMS.
    Returns audio_path=null if no TTS backend is installed.
    """
    from kadima.engine.tts_synthesizer import TTSSynthesizer

    proc = TTSSynthesizer()
    result = proc.process(
        req.text,
        {
            "backend": req.backend,
            "device": req.device,
            "speaker_ref_path": req.speaker_ref_path,
            "voice": req.voice,
            "use_g2p": req.use_g2p,
        },
    )
    # TTS returns FAILED if no backend available but still fills data for text_length
    data = result.data
    if data is None:
        raise HTTPException(status_code=500, detail=result.errors)

    audio_path_str = str(data.audio_path) if data.audio_path else None
    return TTSResponse(
        audio_path=audio_path_str,
        backend=data.backend,
        backend_used=data.backend,
        text_length=data.text_length,
        duration_seconds=data.duration_seconds,
        sample_rate=data.sample_rate,
        note=data.note,
    )


@router.get("/tts/download/{filename}")
async def tts_download(filename: str):
    """Download synthesized audio file by filename.

    Files are stored in ~/.kadima/tts_output/ (content-addressed by SHA-256).
    """
    import os
    from pathlib import Path
    from fastapi.responses import FileResponse

    output_dir = Path(os.path.expanduser("~/.kadima/tts_output"))
    file_path = output_dir / filename

    # Security: prevent path traversal
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"Audio file not found: {filename}")
    if not str(file_path.resolve()).startswith(str(output_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        str(file_path),
        media_type="audio/wav",
        filename=filename,
    )


# ── M16 STT Transcriber ──────────────────────────────────────────────────────


class STTRequest(BaseModel):
    audio_path: str = Field(..., description="Absolute path to audio file on server (WAV/MP3/OGG/FLAC)")
    backend: str = Field(default="auto", pattern=r"^(auto|whisper|faster-whisper)$")
    device: str = Field(default="cpu", pattern=r"^(cpu|cuda)$")
    language: str = Field(default="he", description="Language code (he, en, ...)")


class STTResponse(BaseModel):
    transcript: str
    language: str
    confidence: float
    duration_seconds: float
    backend: str
    segments: list[dict] = Field(default_factory=list)
    word_segments: list[dict] = Field(default_factory=list)
    note: str = ""


@router.post("/stt", response_model=STTResponse)
async def stt(req: STTRequest) -> STTResponse:
    """Transcribe audio file to Hebrew text (M16 STT Transcriber).

    Accepts a server-side audio file path.
    Backend auto-selects: openai-whisper → faster-whisper fallback.
    """
    import os
    if not os.path.isfile(req.audio_path):
        raise HTTPException(
            status_code=422,
            detail=f"Audio file not found: {req.audio_path!r}",
        )

    from kadima.engine.stt_transcriber import STTTranscriber

    proc = STTTranscriber()
    result = proc.process(
        req.audio_path,
        {"backend": req.backend, "device": req.device, "language": req.language},
    )
    if result.status != ProcessorStatus.READY or result.data is None:
        raise HTTPException(status_code=500, detail=result.errors)

    return STTResponse(
        transcript=result.data.transcript,
        language=result.data.language,
        confidence=result.data.confidence,
        duration_seconds=result.data.duration_seconds,
        backend=result.data.backend,
        segments=result.data.segments,
        word_segments=result.data.word_segments,
        note=result.data.note,
    )
