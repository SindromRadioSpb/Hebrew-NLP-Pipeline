# Offline TTS Bootstrap

This folder is the offline staging area for the M15 TTS and M16 STT backends.

Repository runtime convention:

- use `E:\projects\Project_Vibe\Kadima\.venv` as the only supported virtual environment;
- do not stage or reuse legacy sibling environments such as `.venv-311`.

## Wheelhouse

Place Python wheels into [wheels](E:/projects/Project_Vibe/Kadima/offline/wheels):

- `f5-tts`
- `lightblue-onnx` (official LightBlue package from source)
- `piper-tts`
- `phonikud`
- `phonikud-onnx`
- `openai-whisper`
- `faster-whisper`
- `silero-vad` (optional STT preprocessing)
- `whisperx` (optional STT alignment, staged separately from the main `.venv`)

Recommended install command:

```powershell
cd E:\projects\Project_Vibe\Kadima
.\.venv\Scripts\Activate.ps1
python -m pip install --no-index --find-links=offline\wheels --no-deps `
  f5-tts lightblue-onnx piper-tts phonikud phonikud-onnx soundfile
```

Recommended STT install command:

```powershell
cd E:\projects\Project_Vibe\Kadima
.\.venv\Scripts\Activate.ps1
python -m pip install --no-index --find-links=offline\wheels `
  openai-whisper faster-whisper silero-vad
```

Optional alignment evaluation command:

```powershell
cd E:\projects\Project_Vibe\Kadima
.\.venv\Scripts\Activate.ps1
# Install only in an isolated experimental env if needed.
python -m pip install --no-index --find-links=offline\wheels whisperx
```

## Models

Expected local model paths:

- `F:\datasets_models\tts\f5tts-hebrew-v2\model.safetensors`
- `F:\datasets_models\tts\f5tts-hebrew-v2\vocab.txt`
- `F:\datasets_models\tts\f5tts-hebrew-v2\vocoder`
- `F:\datasets_models\tts\lightblue`
- `F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx`
- `F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx.json`
- `F:\datasets_models\stt\whisper-large-v3-turbo\large-v3-turbo.pt`
- `F:\datasets_models\stt\whisper-large-v3-turbo-he\models--ivrit-ai--whisper-large-v3-turbo-ct2\`

Optional environment overrides:

```powershell
$env:F5TTS_HEB_MODEL_PATH='F:\datasets_models\tts\f5tts-hebrew-v2\model.safetensors'
$env:F5TTS_VOCAB_PATH='F:\datasets_models\tts\f5tts-hebrew-v2\vocab.txt'
$env:F5TTS_VOCODER_PATH='F:\datasets_models\tts\f5tts-hebrew-v2\vocoder'
$env:LIGHTBLUE_MODEL_PATH='F:\datasets_models\tts\lightblue'
$env:PHONIKUD_TTS_MODEL_PATH='F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx'
$env:PHONIKUD_TTS_CONFIG_PATH='F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx.json'
$env:WHISPER_MODEL_PATH='F:\datasets_models\stt\whisper-large-v3-turbo\large-v3-turbo.pt'
$env:FASTER_WHISPER_MODEL_PATH='F:\datasets_models\stt\whisper-large-v3-turbo-he\models--ivrit-ai--whisper-large-v3-turbo-ct2\snapshots\72ad623a37947395efcc3933132353790e5a12f5'
```

## F5 Hebrew v2 Notes

- Runtime now targets the official `Yzamari/f5tts-hebrew-v2` checkpoint layout: `model.safetensors` + `vocab.txt`.
- `vocab.txt` is mandatory for readiness and inference.
- Hebrew fine-tunes must use direct `model.sample()` with the custom vocab path; the generic F5 CLI/batch path is not used here.
- `speaker_ref_path` no longer requires `F5TTS_REF_TEXT`. If no transcript is supplied, upstream ASR is used for the reference WAV.
- Optional voice presets can be staged under `F:\datasets_models\tts\f5tts-hebrew-v2\voices\` as `<voice>.wav` plus optional `<voice>.txt`.
- A local open-source preset pack can live in that directory. Current staged pack uses `google/fleurs` `he_il` references under `cc-by-4.0`; see `voices\README.txt` and `voices\manifest.csv` for attribution and exact source rows.
- Current local preset names are: `fleurs-he-m1511`, `fleurs-he-m1512`, `fleurs-he-m1513`, `fleurs-he-m1515`, `fleurs-he-m1516`, `fleurs-he-m1517`, `fleurs-he-m1660`, `fleurs-he-m1661`, `fleurs-he-m1664`, `fleurs-he-m1666`.
- The Hugging Face model repo currently publishes only `model.safetensors` and `vocab.txt`; it does not publish the 58 preset reference WAV/TXT files, so preset voice selection is supported by runtime but not bundled by default.
- Current `google/fleurs` preset references are treated as experimental. If one produces a non-finite F5 waveform, runtime logs a warning and falls back to the bundled default voice so synthesis still completes.
- Without `voices\*.wav` or an explicit `speaker_ref_path`, `f5tts` falls back to the packaged demo reference voice from the upstream `f5-tts` wheel.

## Removed Backends

`zonos` and `bark` are intentionally excluded from the prototype release contract.

- `zonos` was dropped because the Windows runtime never had a production-ready implementation and the earlier WSL2/premium idea would have been a false backend promise in UI/API.
- `bark` was dropped because it is not bundled offline, is slow/heavy for the prototype, and overlaps with the now-working `f5tts` cloning flow while worsening UX clarity.
- Release-supported Hebrew path is `lightblue (Noa by default) -> f5tts -> phonikud -> mms`.

## M16 STT Notes

- Release-supported STT backends: `auto`, `whisper`, `faster-whisper`.
- `auto` means `whisper -> faster-whisper -> FAILED`.
- `GenerativeView` STT tab now surfaces:
  - supported formats;
  - ready/changed state after selecting or changing audio/backend/device;
  - final summary with backend used, duration, confidence and segment count;
  - embedded audio playback for direct audition against the transcript;
  - optional `Use VAD` and `Word alignment` toggles.
- `TTS -> STT` round-trip quality gate is implemented in `tests/engine/test_tts_stt_roundtrip.py` and enforces `WER < 0.15` when local models are available.
- `silero-vad` is installed in the main `.venv` and used as an optional enhancement path. If it finds no speech or preprocessing fails, runtime keeps the transcript path alive and returns a note instead of failing.
- `whisperx` remains opt-in and is not bundled into the standard `.venv` because the current upstream package pulls a `torch~=2.8` stack that conflicts with the accepted project runtime (`torch 2.10.0+cu128`).
- Live smoke artifact from the current workspace:
  - transcript: [stt_m16_smoke.txt](E:/projects/Project_Vibe/Kadima/artefacts/stt_m16_smoke.txt)
  - metadata: [stt_m16_smoke.json](E:/projects/Project_Vibe/Kadima/artefacts/stt_m16_smoke.json)

## Readiness Check

```powershell
@'
from kadima.engine.tts_bootstrap import get_offline_bootstrap_report
report = get_offline_bootstrap_report()
print(report)
'@ | python -
```

## Smoke Synthesis

```powershell
@'
from pathlib import Path
from kadima.engine.tts_synthesizer import TTSSynthesizer

text = "שלום, זה מבחן סינתזה."
out = Path("artefacts")
out.mkdir(exist_ok=True)

for backend in ("f5tts", "lightblue", "phonikud"):
    result = TTSSynthesizer().process(
        text,
        {"backend": backend, "device": "cpu", "output_dir": str(out)},
    )
    print(backend, result.status, result.errors, getattr(result.data, "audio_path", None))
'@ | python -
```
