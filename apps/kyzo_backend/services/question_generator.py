from apps.kyzo_backend.config import LLMProvider, InstructionsPrompts
from apps.kyzo_backend.schemas import (ExtractedQuestionMetadata,
                                       QuestionInputExtractedQuestionsUpdate)
from apps.kyzo_backend.services import OpenaiLLMService, GoogleLLMService


class QuestionGenerator:
    """
    High-level orchestrator for transforming raw pedagogical content into structured questions.

    This service serves as the specialized logic layer between raw input data and the
    generic LLMService. It manages prompt engineering by injecting specific parameters
    (like question count and instructional constraints) into predefined templates
    to ensure the AI produces high-quality, curriculum-aligned questions.
    """

    def __init__(self):
        """
        Initializes the QuestionGenerator with an encapsulated LLMService.
        """
        self.openai_llm = OpenaiLLMService()
        self.google_llm = GoogleLLMService()

    def generate_extracted_questions_from_raw_input(
            self,
            extraction_metadata: ExtractedQuestionMetadata
    ) -> QuestionInputExtractedQuestionsUpdate:
        """
        Orchestrates the AI-driven extraction of question drafts from source material.

        This method formats the pedagogical instruction template using the provided
        metadata and delegates the structured extraction to the selected LLM service.
        It separates system-level pedagogical rules from the raw source content to
        optimize model performance.

        Args:
            extraction_metadata (ExtractedQuestionMetadata): A container holding all
                necessary context including subject, topic, grade, the raw input
                material, and the preferred LLM provider.

        Returns:
            QuestionInputExtractedQuestionsUpdate: A collection of AI-generated question
                                                    drafts matching the internal schema.

        Raises:
            HTTPException:
                - 502 (Bad Gateway): If the LLM service is unavailable or fails.
                - 500 (Internal Server Error): If an unexpected processing error occurs.
        """
        multiple_choice_instruction = InstructionsPrompts.MULTIPLE_CHOICE_INSTRUCTION.format(
            subject_name=extraction_metadata.subject_name,
            topic_name=extraction_metadata.topic_name,
            grade=extraction_metadata.grade,
            num_of_questions=extraction_metadata.num_of_questions
        )

        if extraction_metadata.llm_provider == LLMProvider.GOOGLE:
            return self.google_llm.get_extracted_questions_from_raw_input(
                prompt_instructions=multiple_choice_instruction,
                prompt_input=extraction_metadata.raw_input.content
            )

        return self.openai_llm.get_extracted_questions_from_raw_input(
            prompt_instructions=multiple_choice_instruction,
            prompt_input=extraction_metadata.raw_input.content
        )
