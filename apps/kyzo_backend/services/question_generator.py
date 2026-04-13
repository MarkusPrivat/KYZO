from apps.kyzo_backend.config import InstructionsPrompts
from apps.kyzo_backend.services import LLMService
from apps.kyzo_backend.schemas import QuestionInputRawInput, QuestionInputExtractedQuestionsUpdate


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
        self.llm = LLMService()

    def generate_extracted_questions_from_raw_input(
            self,
            subject_name: str,
            topic_name: str,
            grade: int,
            raw_input: QuestionInputRawInput,
            num_of_questions: int
    ) -> QuestionInputExtractedQuestionsUpdate:
        """
        Orchestrates the AI-driven extraction of question drafts from source material.

        This method formats the pedagogical instruction template with specific metadata
        (subject, topic, grade) and delegates the structured extraction to the LLM service.
        It ensures that the AI receives a clear set of rules separately from the
        source content.

        Args:
            subject_name (str): The human-readable name of the subject for AI context.
            topic_name (str): The human-readable name of the topic for AI context.
            grade (int): The target school grade level (1-13).
            raw_input (QuestionInputRawInput): Validated source material containing
                                               the core text content.
            num_of_questions (int): The target number of questions to be generated.

        Returns:
            QuestionInputExtractedQuestionsUpdate: A collection of AI-generated question
                                                    drafts matching the internal schema.

        Raises:
            HTTPException:
                - 502 (Bad Gateway): If the LLM service is unavailable or fails.
                - 500 (Internal Server Error): If an unexpected processing error occurs.
        """
        multiple_choice_instruction = InstructionsPrompts.MULTIPLE_CHOICE_INSTRUCTION.format(
            subject_name=subject_name,
            topic_name=topic_name,
            grade=grade,
            num_of_questions=num_of_questions
        )

        return self.llm.get_extracted_questions_from_raw_input(
            prompt_instructions=multiple_choice_instruction,
            prompt_input=raw_input.content
        )
