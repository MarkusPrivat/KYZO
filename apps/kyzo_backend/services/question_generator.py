from apps.kyzo_backend.config import InputPrompts
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
            raw_input: QuestionInputRawInput,
            num_of_questions: int
    ) -> QuestionInputExtractedQuestionsUpdate:
        """
        Orchestrates the AI-driven extraction of question drafts from source material.

        This method merges instructional templates with the raw source content and
        requests a structured response from the LLM. It serves as the high-level
        interface for question generation, handling prompt construction and
        quantity enforcement.

        Args:
            raw_input (QuestionInputRawInput): Validated source material containing
                                               the core text content.
            num_of_questions (int): The target number of questions to be generated.

        Returns:
            QuestionInputExtractedQuestionsUpdate: A validated collection of drafted questions.

        Raises:
            HTTPException:
                - 502 (Bad Gateway): If the LLM service is unavailable or fails.
                - 500 (Internal Server Error): If an unexpected processing error occurs.
        """
        multiple_choice_instruction = InputPrompts.MULTIPLE_CHOICE_INSTRUCTION.format(
            num_of_questions=num_of_questions
        )

        input_prompt = f"{multiple_choice_instruction}\n{raw_input.content}"

        return self.llm.get_extracted_questions_from_raw_input(input_prompt)
