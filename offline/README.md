# Offline TTS Bootstrap

This folder is the offline staging area for the M15 TTS backends.

## Wheelhouse

Place Python wheels into [wheels](E:/projects/Project_Vibe/Kadima/offline/wheels):

- `f5-tts`
- `lightblue-onnx` (official LightBlue package from source)
- `piper-tts`
- `phonikud`
- `phonikud-onnx`

Recommended install command:

```powershell
cd E:\projects\Project_Vibe\Kadima
.\.venv\Scripts\Activate.ps1
python -m pip install --no-index --find-links=offline\wheels --no-deps `
  f5-tts lightblue-onnx piper-tts phonikud phonikud-onnx soundfile
```

## Models

Expected local model paths:

- `F:\datasets_models\tts\f5tts-hebrew-v2\model_1250000.safetensors`
- `F:\datasets_models\tts\f5tts-hebrew-v2\vocoder`
- `F:\datasets_models\tts\lightblue`
- `F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx`
- `F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx.json`

Optional environment overrides:

```powershell
$env:F5TTS_HEB_MODEL_PATH='F:\datasets_models\tts\f5tts-hebrew-v2\model_1250000.safetensors'
$env:F5TTS_VOCODER_PATH='F:\datasets_models\tts\f5tts-hebrew-v2\vocoder'
$env:LIGHTBLUE_MODEL_PATH='F:\datasets_models\tts\lightblue'
$env:PHONIKUD_TTS_MODEL_PATH='F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx'
$env:PHONIKUD_TTS_CONFIG_PATH='F:\datasets_models\tts\phonikud-tts\he_IL-heb-high.onnx.json'
```

## Bark

`bark` is optional and is not bundled into the offline bootstrap for the prototype release.

- Readiness should show `bark` as optional unless `bark`/`suno-bark` is installed separately.
- Primary product path for Hebrew remains `f5tts -> lightblue -> phonikud -> mms`.

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
