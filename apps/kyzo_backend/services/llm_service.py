import openai

from fastapi import HTTPException, status
from google import genai
from google.genai import errors, types
from openai import OpenAI

from apps.kyzo_backend.config import (fastapi_settings,
                                      InputPrompts,
                                      InstructionsPrompts,
                                      AIMessages)
from apps.kyzo_backend.schemas import OCRResult, QuestionInputExtractedQuestionsUpdate


class GoogleLLMService:
    """
    Service layer for interacting with the Google GenAI (Gemini/Gemma) API.

    This service encapsulates the Google GenAI client and provides a high-level
    interface for generating structured content and performing vision-based tasks.
    It is designed to handle modern Google models like Gemini 3.x and Gemma-4,
    leveraging native Pydantic support for structured JSON outputs.

    Attributes:
        client (genai.Client): The initialized Google GenAI client.
        gemini_model (str): The specific gemini model ID.
        temperature (float): Controls the creativity/determinism of the output.
        max_output_tokens (int): The maximum allowed token count for the response.
    """

    def __init__(self):
        """
        Initializes the GoogleLLMService using the Google GenAI SDK.

        Sets up the generative AI client with credentials and model parameters
        sourced from the centralized application settings. This service is
        optimized for Google-specific models like Gemini and Gemma-4.
        """
        self.client = genai.Client(api_key=fastapi_settings.GEMINI_API_KEY)
        self.gemini_model = fastapi_settings.GEMINI_MODEL
        self.temperature = fastapi_settings.LLM_TEMPERATURE
        self.max_output_tokens = fastapi_settings.LLM_MAX_TOKENS

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
        print("\n========= GOOGLE RESPONSE DEBUG ===========")
        print(f"Tokens: Total: {usage.total_token_count} (In: {usage.prompt_token_count} |"
              f" Out: {usage.candidates_token_count}\n")
        print("=============================================")
        print(output)
        print("=============================================\n")

    def get_extracted_questions_from_raw_input(
            self,
            prompt_instructions: str,
            prompt_input: str
    ) -> QuestionInputExtractedQuestionsUpdate:
        """
        Processes raw text input and extracts structured questions using Google GenAI.

        This method utilizes the Google GenAI SDK's native structured output capabilities
        to transform unstructured text into a validated Pydantic schema. It leverages
        system instructions for pedagogical guidance and the model's JSON mode for
        high-reliability parsing.

        Args:
            prompt_instructions (str): Guidelines and role definitions for the AI.
            prompt_input (str): The raw source material and specific request.

        Returns:
            QuestionInputExtractedQuestionsUpdate: The parsed and validated question collection.

        Raises:
            HTTPException:
                - 400 (Bad Request): If the Google API client reports an issue (e.g., quota
                  exhausted or invalid arguments).
                - 502 (Bad Gateway): If the Google servers are overloaded or unreachable.
                - 500 (Internal Server Error): If an unexpected API error occurs, the response
                  structure is invalid, or parsing into the Pydantic schema fails.
        """
        try:
            response = self.client.models.generate_content(
                model=self.gemini_model,
                contents=prompt_input,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_instructions,
                    temperature=self.temperature,
                    max_output_tokens=self.max_output_tokens,
                    response_mime_type='application/json',
                    response_schema=QuestionInputExtractedQuestionsUpdate,
                )
            )

            if fastapi_settings.LLM_DEBUG:
                self._ai_response_debug(response.usage_metadata, response.text)

            if not response.parsed:
                raise ValueError(AIMessages.INVALID_RESPONSE_STRUCTURE)

            return response.parsed

        except errors.ClientError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{AIMessages.GOOGLE_CLIENT_ERROR} {str(error)}"
            ) from error
        except errors.ServerError as error:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{AIMessages.GOOGLE_SERVER_ERROR} {str(error)}"
            ) from error
        except errors.APIError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{AIMessages.GOOGLE_API_ERROR} {str(error)}"
            ) from error
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{AIMessages.UNEXPECTED_ERROR}: {str(error)}"
            ) from error


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
