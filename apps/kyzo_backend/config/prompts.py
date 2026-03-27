from dataclasses import dataclass


@dataclass(frozen=True)
class InputPrompts():
    MULTIPLE_CHOICE_INSTRUCTION = """
    Analysiere den folgenden Text und erstelle daraus genau {question_count} Multiple-Choice-Fragen.

    Regeln:
    1. Die Fragen müssen didaktisch wertvoll sein.
    2. Jede Frage braucht genau eine richtige Antwort.
    3. Erstelle für jede Frage eine hilfreiche Erklärung (Explanation).
    4. Schwierigkeitsgrad: 1 (leicht) bis 10 (sehr schwer).

    TEXT ZUR ANALYSE:
    """


@dataclass(frozen=True)
class InstructionsPrompts():
    TEACHER_PROMPT = """
    Du bist ein erfahrener Lehrer und Experte für Didaktik. Antworte immer auf Deutsch.
    """