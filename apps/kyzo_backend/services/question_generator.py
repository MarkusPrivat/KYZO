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
            question_count: int
    ) -> tuple[bool, QuestionInputExtractedQuestionsUpdate | str]:
        """
        Orchestrates the AI-driven extraction of question drafts from source material.

        This method merges instructional templates with the raw source content and
        requests a structured JSON response from the LLM. It focuses on maintaining
        the requested quantity and pedagogical quality of the generated items.

        Args:
            raw_input (QuestionInputRawInput): The validated source material,
                                               including the core text content.
            question_count (int): The target number of questions the AI is
                                  instructed to generate from the context.

        Returns:
            tuple[bool, QuestionInputExtractedQuestionsUpdate | str]:
                - If successful: (True, A validated DTO containing the list of drafted questions)
                - If failed: (False, A descriptive error message from the LLM service)

        Note:
            The quality of the output depends heavily on the 'MULTIPLE_CHOICE_INSTRUCTION'
            template defined in InputPrompts.
        """
        multiple_choice_instruction = InputPrompts.MULTIPLE_CHOICE_INSTRUCTION.format(
            question_count=question_count
        )

        input_prompt = f"{multiple_choice_instruction}\n{raw_input.content}"

        success, result = self.llm.get_extracted_questions_from_raw_input(input_prompt)

        if not success:
            return False, result

        return True, result
