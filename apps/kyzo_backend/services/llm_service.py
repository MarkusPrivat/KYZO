import openai
from openai import OpenAI

from apps.kyzo_backend.config import fastapi_settings,  InstructionsPrompts, OpenAIMessages
from apps.kyzo_backend.schemas import QuestionInputExtractedQuestionsUpdate



class LLMService:
    """
    Service layer for interacting with the OpenAI Responses API.

    This service encapsulates the OpenAI client and provides a high-level
    interface for generating structured educational content. It leverages
    the modern 'Responses' API to ensure that AI-generated data strictly
    conforms to internal Pydantic schemas.

    Attributes:
        client (OpenAI): The initialized OpenAI client.
        model (str): The specific model ID (e.g., 'gpt-4o-mini').
        temperature (float): Controls the creativity/determinism of the output.
        llm_max_tokens (int): The maximum allowed token count for the response.
    """

    def __init__(self):
        """
        Initializes the LLMService using centralized application settings.

        Sets up the OpenAI client with API keys and model parameters
        defined in the global 'fastapi_settings'.
        """
        self.client = OpenAI(api_key=fastapi_settings.OPENAI_API_KEY)
        self.model = fastapi_settings.OPENAI_MODEL
        self.temperature = fastapi_settings.LLM_TEMPERATURE
        self.llm_max_tokens = fastapi_settings.LLM_MAX_TOKENS

    def get_extracted_questions_from_raw_input(
            self,
            prompt: str
    ) -> tuple[bool, QuestionInputExtractedQuestionsUpdate | str | None]:
        """
        Processes raw text input and extracts structured questions using the LLM.

        This method sends the raw input to the OpenAI Responses API, utilizing
        predefined pedagogical instructions. The response is automatically
        parsed and validated against the QuestionInputExtractedQuestionsUpdate
        schema.

        Args:
            prompt (str): The raw source text (e.g., from a PDF or manual input)
                from which questions should be generated.

        Returns:
            tuple[bool, QuestionInputExtractedQuestionsUpdate | str | None]:
                A tuple where the first element indicates success (True/False).
                If True, the second element is the parsed
                QuestionInputExtractedQuestionsUpdate object.
                If False, the second element is a string containing the error
                message for the user/logs.

        Note:
            Specific OpenAI errors (Connection, Rate Limit, etc.) are caught
            internally and returned as a failure state with a descriptive
            message from OpenAIMessages.
        """
        try:
            response = self.client.responses.parse(
                model=self.model,
                temperature=self.temperature,
                max_output_tokens=self.llm_max_tokens,
                instructions=InstructionsPrompts.TEACHER_PROMPT,
                input=prompt,
                text_format=QuestionInputExtractedQuestionsUpdate
            )

            return True, response.output_parsed

        except openai.OpenAIError as error:
            return False, f"{OpenAIMessages.LLM_CONNECTION_ERROR} {str(error)}"
