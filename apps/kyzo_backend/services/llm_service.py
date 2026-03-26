import openai
from openai import OpenAI

from apps.kyzo_backend.config import fastapi_settings
from apps.kyzo_backend.schemas import QuestionInputExtractedQuestionsUpdate


system_prompt = '''
    Du bist ein erfahrener Lehrer und Experte für Didaktik. Antworte immer auf Deutsch.
'''


class LLMService:
    """
    Service layer for interacting with the OpenAI API.
    """

    def __init__(self):
        """
        Initializes the LLMService using centralized application settings.
        """
        self.client = OpenAI(api_key=fastapi_settings.OPENAI_API_KEY)
        self.model = fastapi_settings.OPENAI_MODEL
        self.temperature = fastapi_settings.LLM_TEMPERATURE
        self.llm_max_tokens = fastapi_settings.LLM_MAX_TOKENS

    def get_extracted_questions_from_raw_input(self, prompt: str):
        """
        Requests a completion from the LLM that strictly follows a given schema.
        """
        try:
            response = self.client.responses.parse(
                model=self.model,
                temperature=self.temperature,
                max_output_tokens=self.llm_max_tokens,
                instructions=system_prompt,
                input=prompt,
                text_format=QuestionInputExtractedQuestionsUpdate
            )

            return response.output_parsed

        except openai.OpenAIError as error:
            print(f"Server connection error: {error}")
        except Exception as error:  # pylint: disable=broad-exception-caught
            print(f"Unexpected error: {error}")

        return None



# --- TEST ---
if __name__ == "__main__":
    test_prompt = """
    Analysiere den folgenden Text und erstelle daraus genau 3 Multiple-Choice-Fragen.

    Regeln:
    1. Die Fragen müssen didaktisch wertvoll sein.
    2. Jede Frage braucht genau eine richtige Antwort.
    3. Erstelle für jede Frage eine hilfreiche Erklärung (Explanation).
    4. Schwierigkeitsgrad: 1 (leicht) bis 10 (sehr schwer).

    TEXT ZUR ANALYSE:
    Die Französische Revolution begann im Jahr 1789. Ein zentrales Ereignis war der 
    Sturm auf die Bastille am 14. Juli. Die Revolution führte zum Ende der absoluten 
    Monarchie in Frankreich und zur Erklärung der Menschen- und Bürgerrechte. 
    Wichtige Akteure waren unter anderem Maximilien de Robespierre und Napoleon Bonaparte.
    """
    service = LLMService()

    # Wir übergeben das Schema hier dynamisch
    result = service.get_extracted_questions_from_raw_input(
        test_prompt
    )

    if result:
        print(f"Erfolgreich generiert: {result}")
