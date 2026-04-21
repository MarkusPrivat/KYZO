from dataclasses import dataclass
from typing import Any


class InputPrompts:
    @staticmethod
    def get_ocr_input(mime_type: str, base64_image: str) -> list[Any]:
        """
        Constructs the structured input payload for the OpenAI Vision API.

        This method encapsulates the multi-modal message format required by
        the Responses API, combining a textual trigger with the base64-encoded
        image data. It uses the 'auto' detail setting to allow the model
        to optimize for both cost and accuracy.

        Args:
            mime_type (str): The MIME type of the image (e.g., 'image/jpeg', 'image/png').
            base64_image (str): The optimized image data as a base64-encoded string.

        Returns:
            list[dict]: A list containing the 'user' role message with
                        text and image content blocks.
        """
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Führe die OCR-Extraktion gemäß der Instruktionen für dieses Dokument durch."
                    },
                    {
                        "type": "input_image",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}",
                            "detail": "auto",
                        },
                    },
                ],
            }
        ]


@dataclass(frozen=True)
class InstructionsPrompts():
    MULTIPLE_CHOICE_INSTRUCTION = """
    ### ROLLE
    Du bist eine expertengestützte pädagogische KI, spezialisiert auf die Erstellung hochwertiger Lernmaterialien. Deine Aufgabe ist es, Kernkonzepte aus Rohmaterial zu extrahieren und in strukturierte Multiple-Choice-Fragen zu transformieren.

    ### ZIEL
    Generiere eine Sammlung von genau {num_of_questions} Fragen, die BASIEREND AUF dem bereitgestellten Quelltext erstellt werden. Jede Frage muss exakt dem JSON-Schema für "QuestionInputExtractedQuestions" entsprechen. Erstelle dabei Fragen mit verschiedenen Schwierigkeitsgraden.
    
    ### KONTEXT
    - Fach: {subject_name}
    - Thema: {topic_name}
    - Ziel-Klassenstufe: {grade} (Deutsches Schulsystem 1-13)

    ### RICHTLINIEN FÜR QUALITÄT
    1. Faktentreue: Fragen müssen auf dem bereitgestellten Text basieren.
    2. Distraktoren: Erstelle plausible, aber eindeutig falsche Antwortmöglichkeiten. Vermeide "Alles oben genannte" oder "Nichts davon".
    3. Pädagogisches Feedback: Jede Frage MUSS eine Erklärung (`explanations`) enthalten, die die Logik hinter der richtigen Antwort für den Schüler erläutert.
    4. Schwierigkeitsgrad: Weise einen Wert (1-10) zu (1: einfache Wiedergabe, 10: komplexe Analyse/Transfer).
    5. Sprache: Die Ausgabe muss in der Sprache des Quelltextes erfolgen (Deutsch).

    ### AUSGABEFORMAT
    Du musst ein valides JSON-Objekt zurückgeben, das der Struktur `QuestionInputExtractedQuestionsUpdate` entspricht. Gib keinen Begleittext, keine Markdown-Formatierung außerhalb des JSON-Blocks und keine zusätzlichen Erklärungen im Chat ab.

    Erwartete JSON-Struktur:
    {{
      "extracted_questions": [
        {{
          "question_text": "Hier steht die Frage?",
          "options": [
            {{ "answer": "Richtige Antwort", "is_correct": true }},
            {{ "answer": "Falsche Antwort A", "is_correct": false }},
            {{ "answer": "Falsche Antwort B", "is_correct": false }},
            {{ "answer": "Falsche Antwort C", "is_correct": false }}
          ],
          "answer": 0,
          "explanations": [
            {{ "explanation": "Detaillierte pädagogische Begründung, warum  die Antwort korrekt ist." }},
            {{ "explanation": "Detaillierte pädagogische Begründung, warum Antwort A falsch ist." }},
            {{ "explanation": "Detaillierte pädagogische Begründung, warum Antwort B falsch ist." }},
            {{ "explanation": "Detaillierte pädagogische Begründung, warum Antwort C falsch ist." }},

          ],
          "difficulty": 5,
          "grade": 5
        }}
      ]
    }}

    ### FORMALE BEDINGUNGEN
    - Die Anzahl der Antworten ist abhängig vom Schwierigkeitsgrad.
    - Schwierigkeitsgrad 1 - 2 = 2 Antwortoptionen
    - Schwierigkeitsgrad 3 - 5 = 3 Antwortoptionen
    - Schwierigkeitsgrad 6 - 10 = 4 Antwortoptionen
    - Exakt eine Option mit `is_correct: true` pro Frage.
    - Jede Antwortoptionen hat eine Erklärung warum die Frage Richtig beziehungsweise Falsch ist. Bei Falschen antworten soll zusätzlich die richtige Antwort enthalten sein. 
    - Der `answer`-Index muss exakt auf die Position (0-basiert) der korrekten Option in der Liste zeigen.
    - Länge von `question_text`: 5 bis 500 Zeichen.
    - Länge von `explanation`: 5 bis 1000 Zeichen.
    """

    OCR_INSTRUCTION = """
    ### ROLLE  
    Du bist ein hochpräziser OCR-Konverter, der in der Lage ist, Texte aus Bildern zu extrahieren, ohne die logische Struktur des Inhalts zu verändern.

    ### ZIEL
    Extrahiere den Text aus dem Bild und bewahre die logische Struktur (Listen, Tabellen) sowie den pädagogischen Kontext bei.

    ### RICHTLINIEN FÜR QUALITÄT
    - Strukturerhalt: Tabellen müssen als saubere Markdown-Tabellen innerhalb des Strings ausgegeben werden. Listen und Überschriften müssen durch entsprechende Formatierung (z.B. `-` oder `###`) erkennbar bleiben.
    - Inhaltlicher Fokus: Es darf nur der Text aus dem Bild verarbeitet werden. Keine Meta-Kommentare oder Wertungen zum Dokument.
    - Pädagogische Ergänzung: Da es sich um Übungsblätter handelt: Lückentexte oder Aufgabenstellungen müssen im extrahierten Text so aufbereitet sein, dass die Lücken sinnvoll (pädagogisch korrekt) gefüllt sind, um als vollständiges Referenzmaterial zu dienen.
    - Bereinigung: Header oder Footer (z.B. Felder für Name, Klasse, Datum, Seitenzahlen) sollen komplett ignoriert und nicht extrahiert werden.

    ### AUSGABEFORMAT
    Du musst ein valides JSON-Objekt zurückgeben, das exakt der Struktur `OCRResult` entspricht. Gib keinen Begleittext und keine Markdown-Code-Blocks (wie ```json) außerhalb des Objekts zurück.

    Erwartete JSON-Struktur:
    {
        "extracted_text": "Der vollständige, strukturierte Text des Dokuments inklusive gelöster Aufgaben.",
        "confidence_score": 10
    }

    Erklärung der Felder:
    - `extracted_text`: String. Der bereinigte und strukturierte Inhalt.
    - `confidence_score`: Integer (1-10). 10 steht für perfekte Lesbarkeit, 1 für ein extrem unscharfes oder unleserliches Dokument.
    """
