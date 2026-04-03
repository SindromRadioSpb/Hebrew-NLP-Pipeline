"""Test NLLB backend HE->RU translation."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kadima.engine.translator import Translator

t = Translator()
text = 'תהליך ייצור הפלדה מתחיל בעפרת הברזל.'
config = {'backend': 'nllb', 'src_lang': 'he', 'tgt_lang': 'ru', 'device': 'cpu'}

print("Translating HE->RU with NLLB...")
result = t.process(text, config)

print(f"Backend: {result.data.backend}")
print(f"Source:  {result.data.source}")
print(f"Result:  {result.data.result}")
print(f"Time:    {result.processing_time_ms:.0f}ms")