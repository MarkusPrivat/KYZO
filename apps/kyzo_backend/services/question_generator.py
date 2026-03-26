from apps.kyzo_backend.config import InputPrompts
from apps.kyzo_backend.services import LLMService
from apps.kyzo_backend.schemas import QuestionInputExtractedQuestionsUpdate


class QuestionGenerator:
    """
    High-level orchestrator for generating pedagogical questions from raw text.

    This service acts as the bridge between the raw input data and the LLMService.
    It formats templates with specific parameters (like question count) and
    handles the logical flow of the generation process.
    """
    def __init__(self):
        """
        Initializes the QuestionGenerator with a dedicated LLMService instance.
        """
        self.llm = LLMService()

    def generate_extracted_questions_from_raw_input(
            self,
            raw_input: str,
            count: int
    ) -> tuple[bool, list[QuestionInputExtractedQuestionsUpdate] | str]:
        """
        Orchestrates the extraction of a specific number of questions from a text.

        It takes the raw source text, injects the desired question count into
        the predefined prompt template, and triggers the structured extraction
        via the LLM.

        Args:
            raw_input (str): The source content to be analyzed by the AI.
            count (int): The exact number of questions the AI should attempt
                to generate from the provided text.

        Returns:
            tuple[bool, QuestionInputExtractedQuestionsUpdate | str]:
                A tuple containing:
                - bool: True if the generation and validation were successful.
                - result: The validated QuestionInputExtractedQuestionsUpdate
                  object on success, or an error message (str) on failure.
        """
        multiple_choice_instruction = InputPrompts.MULTIPLE_CHOICE_INSTRUCTION.format(count=count)
        input_prompt = f"{multiple_choice_instruction}\n{raw_input}"

        success, result = self.llm.get_extracted_questions_from_raw_input(input_prompt)

        if not success:
            return False, result

        return True, result
