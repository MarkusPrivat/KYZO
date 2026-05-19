from fastapi import HTTPException, status

from apps.kyzo_backend.config import AIMessages, fastapi_settings, InstructionsPrompts
from apps.kyzo_backend.schemas import (ExtractedQuestionMetadata,
                                       OCRResult,
                                       QuestionInputExtractedQuestionsUpdate)
from .openai_service import OpenaiLLMService
from .google_gen_ai_service import GoogleLLMService


class LLMOrchestrator:
    """
    High-level orchestrator for transforming raw pedagogical content into structured questions.

    This service serves as the specialized logic layer between raw input data and the
    generic LLMService. It manages prompt engineering by injecting specific parameters
    (like question count and instructional constraints) into predefined templates
    to ensure the AI produces high-quality, curriculum-aligned questions.
    """

    def __init__(self):
        """
        Initializes the LLMOrchestrator with encapsulated LLMServices.
        """
        self.openai_llm = OpenaiLLMService()
        self.google_llm = GoogleLLMService()

    def generate_extracted_questions_from_raw_input(
            self,
            extraction_metadata: ExtractedQuestionMetadata
    ) -> QuestionInputExtractedQuestionsUpdate:
        """
        Orchestrates the AI-driven extraction of question drafts with an automated fallback.

        This method formats the pedagogical instructions and attempts extraction
        primarily via Google Gemini. If the primary provider fails due to service
        errors or quota limits, the method automatically initiates a fallback
        attempt using OpenAI GPT-4o-mini to ensure high availability.

        Args:
            extraction_metadata (ExtractedQuestionMetadata): A container holding all
                necessary context including subject, topic, grade, the raw input
                material, and target question count.

        Returns:
            QuestionInputExtractedQuestionsUpdate: A collection of AI-generated question
                                                    drafts matching the internal schema.

        Raises:
            HTTPException:
                - 500 (Internal Server Error): If both the primary (Google) and
                  fallback (OpenAI) LLM services fail, providing a combined error detail.
        """
        multiple_choice_instruction = InstructionsPrompts.MULTIPLE_CHOICE_INSTRUCTION.format(
            subject_name=extraction_metadata.subject_name,
            topic_name=extraction_metadata.topic_name,
            grade=extraction_metadata.grade,
            num_of_questions=extraction_metadata.num_of_questions
        )

        try:
            return self.google_llm.get_extracted_questions_from_raw_input(
                prompt_instructions=multiple_choice_instruction,
                prompt_input=extraction_metadata.raw_input.content
            )

        except HTTPException as google_error:

            try:
                return self.openai_llm.get_extracted_questions_from_raw_input(
                    prompt_instructions=multiple_choice_instruction,
                    prompt_input=extraction_metadata.raw_input.content
                )

            except Exception as openai_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=AIMessages.EXTRACT_QUESTION_ERROR.format(
                        google_error=google_error.detail,
                        openai_error=str(openai_error)
                    )
                ) from openai_error

    def generate_raw_input_from_scan(
            self,
            base64_image: str,
            mime_type: str = "image/jpeg"
    ) -> OCRResult:
        """
        Performs AI-driven OCR to extract structured text from images with a
        multimodel fallback.

        This method coordinates the transformation of visual document data into a
        validated OCRResult. It primarily utilizes Gemini 3.1 for high-precision
        extraction. If Gemini fails due to service interruptions or quota limits,
        it automatically falls back to the Gemma model to maintain service continuity.

        Args:
            base64_image (str): The image data encoded as a base64 string.
            mime_type (str): The IANA media type of the image (e.g., "image/jpeg", "image/png").

        Returns:
            OCRResult: The extracted text content and associated metadata.

        Raises:
            HTTPException:
                - 500 (Internal Server Error): If both the primary (Gemini) and
                  fallback (Gemma) models fail to process the image, returning
                  a combined error report.
        """
        try:
            return self.google_llm.get_generated_raw_input_from_scan(
                model=fastapi_settings.GEMINI_MODEL,
                base64_image=base64_image,
                mime_type=mime_type
            )

        except HTTPException as gemini_error:

            try:
                return self.google_llm.get_generated_raw_input_from_scan(
                    model=fastapi_settings.GEMMA_MODEL,
                    base64_image=base64_image,
                    mime_type=mime_type
                )

            except Exception as gemma_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=AIMessages.OCR_ERROR.format(
                        gemini_error=gemini_error.detail,
                        gemma_error=str(gemma_error)
                    )
                ) from gemma_error

llm_orchestrator_instance = LLMOrchestrator()
