import openai

from fastapi import HTTPException, status
from openai import OpenAI

from apps.kyzo_backend.config import (fastapi_settings,
                                      InputPrompts,
                                      InstructionsPrompts,
                                      OpenAIMessages)
from apps.kyzo_backend.schemas import OCRResult, QuestionInputExtractedQuestionsUpdate


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

            # Debugging
            usage = response.usage
            parsed_data = response.output_parsed
            print("\n=== AI RESPONSE DEBUG ===")
            print(f"Tokens: {usage.total_tokens} (In: {usage.input_tokens} | Out: {usage.output_tokens})")
            print(parsed_data.model_dump_json(indent=4))
            print("=============================================\n")

            return response.output_parsed

        except openai.OpenAIError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{OpenAIMessages.LLM_CONNECTION_ERROR}: {str(error)}"
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{OpenAIMessages.UNEXPECTED_ERROR}: {str(error)}"
            ) from error

    def generate_raw_input_from_scan(
            self,
            base64_image: str,
            mime_type: str = "image/jpeg"
    ) -> OCRResult:
        """
        Performs AI-driven OCR to extract structured text from an image.

        This method leverages the OpenAI Vision API and Structured Outputs to transform
        visual document data (scans/photos) into a machine-readable format. It uses
        pedagogical instructions to ensure that educational content, such as tables
        and fill-in-the-blank texts, is correctly interpreted and formatted as Markdown.

        Args:
            base64_image (str): The optimized image data as a base64-encoded string.
            mime_type (str): The MIME type of the image. Defaults to "image/jpeg".

        Returns:
            OCRResult: An object containing the extracted text and a confidence score.

        Raises:
            HTTPException:
                - 502 (Bad Gateway): If the OpenAI API connection fails or a vision
                  processing error occurs.
                - 500 (Internal Server Error): For unexpected failures during parsing
                  or response handling.
        """
        vision_input = InputPrompts.get_ocr_input(mime_type, base64_image)

        try:
            response = self.client.responses.parse(
                model=self.model,
                temperature=self.temperature,
                instructions=InstructionsPrompts.OCR_INSTRUCTION,
                input=vision_input,
                text_format=OCRResult
            )

            # Debugging
            usage = response.usage
            parsed_data = response.output_parsed
            print("\n=== AI RESPONSE DEBUG ===")
            print(f"Tokens: {usage.total_tokens} (In: {usage.input_tokens} | Out: {usage.output_tokens})")
            print(parsed_data.model_dump_json(indent=4))
            print("=============================================\n")

            return parsed_data

        except openai.OpenAIError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{OpenAIMessages.LLM_CONNECTION_ERROR}: {str(error)}"
            ) from error

        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{OpenAIMessages.UNEXPECTED_ERROR}: {str(error)}"
            ) from error
