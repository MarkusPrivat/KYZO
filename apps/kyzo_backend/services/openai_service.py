import openai

from fastapi import HTTPException, status
from openai import OpenAI

from apps.kyzo_backend.config import fastapi_settings, AIMessages
from apps.kyzo_backend.schemas import QuestionInputExtractedQuestionsUpdate


class OpenaiLLMService:
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

    @staticmethod
    def _ai_response_debug(usage, output) -> None:
        """
        Prints detailed technical metadata and the raw LLM output for debugging.

        Logs token consumption (input, output, and specialized tokens like 'thoughts')
        alongside the parsed or raw response body to the console. This is used
        to monitor API costs and verify structural integrity during development.

        Args:
            usage: The usage metadata object from the Gemini's UsageMetadata.
            output: The generated content, either as a raw string or
                    a serialized Pydantic model.
        """
        print("\n========= OPENAI RESPONSE DEBUG ===========")
        print(f"Tokens: Total: {usage.total_tokens} (In: {usage.input_tokens} |"
              f" Out: {usage.output_tokens})\n")
        print("=============================================")
        print(output.model_dump_json(indent=4))
        print("=============================================\n")

    def get_extracted_questions_from_raw_input(
            self,
            prompt_instructions: str,
            prompt_input: str
    ) -> QuestionInputExtractedQuestionsUpdate:
        """
        Processes raw text input and extracts structured questions using the LLM.

        This method communicates with the OpenAI API using Structured Outputs to
        transform unstructured source text into a structured schema. It separates
        pedagogical logic (instructions) from the content (input) for better
        reliability.

        Args:
            prompt_instructions (str): Guidelines and role definitions for the AI.
            prompt_input (str): The raw source material and specific request.

        Returns:
            QuestionInputExtractedQuestionsUpdate: The LLM-parsed question collection.

        Raises:
            HTTPException:
                - 502 (Bad Gateway): If the OpenAI API connection fails or triggers filters.
                - 500 (Internal Server Error): For unexpected parsing or server errors.
        """
        try:
            response = self.client.responses.parse(
                model=self.model,
                temperature=self.temperature,
                max_output_tokens=self.llm_max_tokens,
                instructions=prompt_instructions,
                input=prompt_input,
                text_format=QuestionInputExtractedQuestionsUpdate
            )

            if fastapi_settings.LLM_DEBUG:
                self._ai_response_debug(response.usage, response.output_parsed)

            return response.output_parsed

        except openai.OpenAIError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{AIMessages.LLM_CONNECTION_ERROR}: {str(error)}"
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{AIMessages.UNEXPECTED_ERROR}: {str(error)}"
            ) from error
