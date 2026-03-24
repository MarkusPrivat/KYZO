from typing import Optional

from pydantic import Field, model_validator

from .base_schemas import BaseSchema


class QuestionOption(BaseSchema):
    """
    Represents a single choice within a question's answer set.

    This schema defines the structure of individual answer options stored
    within the 'options' JSON field of a Question. It pairs the answer
    text with a boolean flag to identify the correct response.

    Attributes:
        answer (str): The literal text displayed to the user as a choice.
        is_correct (bool): Indicates if this option is the valid answer
                           for the parent question.
    """
    answer: str = Field(
        ...,
        min_length=1,
        description="The text content of the answer option."
    )
    is_correct: bool = Field(
        ...,
        description="Flag indicating if this specific option is the correct one."
    )


class QuestionExplanation(BaseSchema):
    """
    Represents a pedagogical explanation for a question's answer.

    This schema defines the structure of feedback items stored in the
    'explanations' JSON field. These texts are typically generated
    by an AI to provide context, reasoning, and learning support
    regardless of whether the student answered correctly.

    Attributes:
        explanation (str): The detailed feedback or instructional text.
    """
    explanation: str = Field(
        ...,
        min_length=5,
        description="The instructional content or reasoning behind the answer."
    )


class QuestionCreate(BaseSchema):
    """
    Schema for creating a new learning question with integrated validation.

    This model handles the initial ingestion of question data. It enforces
    the educational hierarchy by requiring a valid topic and ensures that
    AI-generated variants are properly linked to their original sources.
    Explanations are included as an optional field to allow for initial
    LLM-based or manual population during the creation process.

    Key Constraints:
    - Must belong to a valid Topic and Grade (1-13).
    - Requires at least two answer options.
    - Enforces a strict 1:1 relationship between the 'answer' index and
      the correct option flag.
    - Maintains traceability for AI-generated variants (LLM variants).
    """
    topic_id: int = Field(..., gt=0, description="The unique ID of the topic.")
    parent_question_id: Optional[int] = Field(
        None,
        gt=0,
        description="ID of parent if it's an AI variant."
    )
    grade: int = Field(..., ge=1, le=13, description="Target school grade (1-13).")
    difficulty: int = Field(..., ge=1, le=10, description="Difficulty ranking (1-10).")
    question_text: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="The question text."
    )
    options: list[QuestionOption] = Field(
        ...,
        min_length=2,
        description="List of possible answers."
    )
    answer: int = Field(..., ge=0, description="Index of the correct option (0-based).")
    explanations: Optional[list[QuestionExplanation]] = Field(
        None,
        description="A list of explanations providing pedagogical feedback."
    )
    is_llm_variant: bool = Field(False, description="True if AI-generated.")

    @model_validator(mode='after')
    def validate_question_logic(self) -> 'QuestionCreate':
        """
        Validates the logical consistency of the question's answers and AI metadata.

        This validator performs two critical checks:
        1. Answer Integrity: Ensures that exactly one option is marked 'is_correct'
           and that the 'answer' index points to that specific option.
        2. AI Lineage: Verifies that AI-generated variants (is_llm_variant=True)
           have a parent_question_id, and original questions do not.

        Returns:
            QuestionCreate: The validated data instance.

        Raises:
            ValueError: If answer logic is contradictory or AI metadata is incomplete.
        """
        correct_indices = [index for index, option in enumerate(self.options) if option.is_correct]

        if len(correct_indices) != 1:
            raise ValueError(f"Exactly one correct answer required. Found: {len(correct_indices)}")
        if self.answer != correct_indices[0]:
            raise ValueError(f"The 'answer' index {self.answer} must point "
                             f"to the option where is_correct is True.")

        if self.is_llm_variant and self.parent_question_id is None:
            raise ValueError("If 'is_llm_variant' is True, a "
                             "'parent_question_id' must be provided.")

        if not self.is_llm_variant and self.parent_question_id is not None:
            raise ValueError("An original question (is_llm_variant=False) "
                             "cannot have a parent_question_id.")

        return self


class QuestionRead(BaseSchema):
    """
    Schema for reading a comprehensive question record from the database.

    This model provides a complete snapshot of a learning item, including
    its structural metadata (topic, grade, difficulty), its content
    (text, options, explanations), and its operational state (is_active).
    It is designed to support both the testing engine and administrative
    overviews.

    Special Handling:
    - 'options' and 'explanations' are retrieved as JSON-mapped lists.
    - 'parent_question_id' facilitates tracking the content lineage for AI-generated variants.
    """
    id: int = Field(..., description="The unique database identifier of the question.")
    topic_id: int = Field(..., description="The ID of the topic this question belongs to.")
    parent_question_id: Optional[int] = Field(
        None,
        description="The ID of the original question if this is an AI-generated variant."
    )
    grade: int = Field(..., ge=1, le=13, description="The target school grade level (1-13).")
    difficulty: int = Field(..., ge=1, le=10, description="The difficulty level (1-10).")
    question_text: str = Field(..., description="The actual text of the question.")
    options: list[QuestionOption] = Field(
        default_factory=list,
        description="A list of dictionaries containing 'answer' and 'is_correct'."
    )
    answer: int = Field(..., description="The zero-based index of the correct option.")
    explanations: list[QuestionExplanation] = Field(
        default_factory=list,
        description="A list of dictionaries containing the 'explanation' text."
    )
    is_llm_variant: bool = Field(..., description="Flag indicating if it is an AI variant.")
    is_active: bool = Field(..., description="Flag to toggle availability.")


class QuestionStatus(BaseSchema):
    """
    Schema for updating the operational status of a question.

    This model is used to toggle a question's availability within the
    learning application. Deactivating a question (is_active=False)
    retains the record in the database for historical data and analytics
    but excludes it from being served in active testing or practice sessions.

    Attributes:
        is_active (bool): The desired visibility state of the question.
    """
    is_active: bool = Field(
        ...,
        description="True to enable the question for students, "
                    "False to hide it from active sessions."
    )


class QuestionUpdate(BaseSchema):
    """
    Schema for updating an existing question's metadata and instructional logic.

    This model allows for partial updates (PATCH-style). However, to maintain
    data integrity, it enforces an 'all-or-nothing' rule for the question's
    core logic: if the list of options is modified, the correct answer index
    must be updated simultaneously.

    Note:
        - Structural identity (is_llm_variant, parent_question_id) cannot be
          changed via this schema to preserve content lineage.
        - Status toggles (is_active) are handled via a separate Status schema.
    """
    topic_id: Optional[int] = Field(None, gt=0, description="The unique ID of the topic.")
    grade: Optional[int] = Field(None, ge=1, le=13, description="Target school grade (1-13).")
    difficulty: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Difficulty ranking (1-10)."
    )
    question_text: Optional[str] = Field(
        None,
        min_length=5,
        max_length=1000,
        description="The question text."
    )
    options: Optional[list[QuestionOption]] = Field(
        None,
        min_length=2,
        description="List of answer options."
    )
    answer: Optional[int] = Field(None, ge=0, description="Index of the correct option (0-based).")
    explanations: Optional[list[QuestionExplanation]] = Field(
        None,
        description="A list of explanations providing pedagogical feedback."
    )

    @model_validator(mode='after')
    def validate_atomic_logic_update(self) -> 'QuestionUpdate':
        """
        Enforces atomic consistency for question logic updates.

        This validator ensures that:
        1. Atomic Pair: 'options' and 'answer' are provided together. Updating
           one without the other would risk a mismatch between the index
           and the actual correct option.
        2. Logical Integrity: If updated, the new options list must contain
           exactly one correct choice, and the provided index must point to it.

        Returns:
            QuestionUpdate: The validated update instance.

        Raises:
            ValueError: If only one part of the logic pair is provided or
                        if the new logic is contradictory.
        """
        if (self.options is None) != (self.answer is None):
            raise ValueError(
                "Updating logic requires both 'options' and 'answer' to "
                "be provided together to ensure the index remains valid."
            )

        if self.options and self.answer is not None:
            correct_indices = [i for i, option in enumerate(self.options) if option.is_correct]
            if len(correct_indices) != 1:
                raise ValueError(f"Exactly one correct answer required. "
                                 f"Found: {len(correct_indices)}")
            if self.answer != correct_indices[0]:
                raise ValueError(
                    f"The 'answer' index {self.answer} does not "
                    f"match the option marked as correct."
                )

        return self
