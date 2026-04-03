"""Test TTS synthesis for all working backends and save artefacts."""
from kadima.engine.tts_synthesizer import TTSSynthesizer
import os
import shutil

HEBREW_TEXT = "תהליך ייצור הפלדה מתחיל בעפרת הברזל. העפרה מוכנסת לתנור היתוך בטמפרטורה גבוהה. הפחמן מוסף לברזל הנוזלי בשליטה מדויקת. התוצאה היא פלדה באיכות גבוהה. חוזק המתיחה של הפלדה תלוי באחוז הפחמן."

OUTPUT_DIR = os.path.expanduser("~/.kadima/tts_output")
ARTEFACTS_DIR = os.path.join(os.path.dirname(__file__), "artefacts")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ARTEFACTS_DIR, exist_ok=True)

print(f"Text length: {len(HEBREW_TEXT)} chars")
print(f"Output dir: {OUTPUT_DIR}")
print(f"Artefacts dir: {ARTEFACTS_DIR}")

# Test all 3 backends on GPU
for backend in ['xtts', 'mms', 'bark']:
    print(f"\n{'='*60}")
    print(f"Testing {backend} backend...")
    print(f"{'='*60}")
    try:
        proc = TTSSynthesizer()
        result = proc.process(HEBREW_TEXT, {'backend': backend, 'output_dir': OUTPUT_DIR})
        if result.data and result.data.audio_path:
            src_path = str(result.data.audio_path)
            filename = f"tts_{backend}_output.wav"
            dest_path = os.path.join(ARTEFACTS_DIR, filename)
            shutil.copy2(src_path, dest_path)
            size = os.path.getsize(dest_path)
            print(f"  Status: {result.status}")
            print(f"  Backend: {result.data.backend}")
            print(f"  Audio saved: {dest_path}")
            print(f"  Size: {size:,} bytes")
            print(f"  SUCCESS ✅")
        else:
            print(f"  Error: {result.errors}")
            print(f"  FAILED ❌")
    except Exception as e:
        print(f"  Exception: {e}")
        print(f"  FAILED ❌")

print(f"\n{'='*60}")
print("Artefacts saved to:")
for f in os.listdir(ARTEFACTS_DIR):
    if f.startswith("tts_") and f.endswith(".wav"):
        size = os.path.getsize(os.path.join(ARTEFACTS_DIR, f))
        print(f"  {f}: {size:,} bytes")