# kadima/llm/prompts.py
"""Prompt templates for Hebrew NLP LLM interactions.

All prompts are designed for DictaLM (Hebrew-specialized LLM).
Templates use .format() with named placeholders.
"""


# Term definition prompt
TERM_DEFINITION = """הגדר את המונח "{term}" בתחום {domain}.
ההגדרה צריכה להיות מדויקת, מקצועית, בעברית.
{context_section}
הגדרה:"""

# Grammar explanation prompt
GRAMMAR_EXPLAIN = """הסבר את התחביר של המשפט הבא:
"{sentence}"

כלול:
1. ניתוח תחבירי (נושא, נשוא, משלימים)
2. זיהוי זמן הפועל
3. שיוך מילות קישור
"""

# Exercise generation prompt
EXERCISE_GENERATE = """צור {count} תרגילים בנושא "{pattern}" ברמת {level}.
פורמט: משפט עם מקום ריק + 4 אפשרויות.
"""

# QA prompt
QA = """ענה על השאלה הבאה בנושא {domain}:

{question}

תשובה:"""

# Translation prompt (辅助)
TRANSLATE = """תרגם את הטקסט הבא מ-{src} ל-{tgt}:
"{text}"

תרגום:"""
