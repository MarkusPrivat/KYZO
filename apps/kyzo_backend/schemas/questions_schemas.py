from datetime import datetime
from typing import Optional

from pydantic import Field, model_validator

from apps.kyzo_backend.config import InputType, LLMProvider
from apps.kyzo_backend.schemas.base_schemas import BaseSchema


class ExtractedQuestionMetadata(BaseSchema):
    """
    Data container for pedagogical context and configuration used in the
    AI-driven question extraction process.

    This model bundles subject-specific metadata with the raw source content
    and model preferences, ensuring a consistent contract between the
    API layer and the LLM services.
    """
    subject_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The human-readable name of the school subject (e.g., 'History')."
    )
    topic_name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="The specific academic topic within the subject (e.g., 'Ancient Greece')."
    )
    grade: int = Field(
        ...,
        ge=1,
        le=13,
        description="The target school grade level (1-13) to calibrate difficulty and language."
    )
    num_of_questions: int = Field(
        ...,
        ge=1,
        le=15,
        description="Number of question to be generated."
    )
    raw_input: QuestionInputRawInput = Field(
        ...,
        description="The structured raw source material (text and metadata) for the AI to analyze."
    )
    llm_provider: LLMProvider = Field(
        default=LLMProvider.OPENAI,
        description=(
            "The specific AI service provider to be used for extraction. "
            "Defaults to OPENAI for general tasks; GOOGLE is recommended for higher precision."
        )
    )


class OCRResult(BaseSchema):
    """
    Schema for the structured output of the AI-driven OCR process.

    This model encapsulates the raw text extracted from document scans
    and provides a heuristic quality assessment to help the system
    decide if the extraction is reliable enough for further processing.
    """
    extracted_text: str = Field(
        ...,
        min_length=1,
        description="The full text extracted from the provided image(s)."
    )

    confidence_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="A heuristic quality score from 1 (unreadable) to 10 (perfectly clear). "
    )


class QuestionOption(BaseSchema):
    """
    Represents a single choice within a question's answer set.

    This schema defines the structure of individual answer options stored
    within the 'options' JSON field of a Question. It pairs the answer
    text with a boolean flag to identify the correct response.
    """
    answer: str = Field(
        ...,
        min_length=1,
        description="The literal text content of the answer choice displayed to the student."
    )
    is_correct: bool = Field(
        ...,
        description="Boolean flag indicating if this specific option is the valid answer."
    )


class QuestionExplanation(BaseSchema):
    """
    Represents a pedagogical explanation for a question's answer.

    This schema defines the structure of feedback items stored in the
    'explanations' JSON field. These texts are typically generated
    by an AI to provide context, reasoning, and learning support
    to help students understand the underlying concept.
    """
    explanation: str = Field(
        ...,
        min_length=5,
        description="The detailed instructional feedback or reasoning that "
                    "explains why an answer is correct or incorrect."
    )


class QuestionInputRawInput(BaseSchema):
    """
    Represents the source material and context used for AI question generation.

    This schema stores the raw text extracted from documents (PDFs, scans, etc.)
    and maintains metadata to ensure pedagogical traceability back to the
    original source.
    """
    content: str = Field(
        "",
        description="The full text content extracted from the source for AI analysis."
    )
    source_ref: Optional[str] = Field(
        "",
        description="A unique identifier for the source material, such as a filename, URL, or UUID."
    )


class QuestionInputExtractedQuestions(BaseSchema):
    """
    Represents a 'proto-question' drafted by the AI.

    This schema acts as an intermediate data structure for AI-generated content.
    It is designed to mirror the permanent Question model to facilitate seamless
    promotion (migration) to the global question pool after user review.
    """
    question_text: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="The draft text of the question as proposed by the AI."
    )
    options: list[QuestionOption] = Field(
        ...,
        min_length=2,
        description="A list of generated answer choices, including one correct option."
    )
    answer: int = Field(
        ...,
        ge=0,
        description="The zero-based index of the correct option within the options list."
    )
    explanations: Optional[list[QuestionExplanation]] = Field(
        None,
        description="Optional AI-generated reasoning or pedagogical feedback for each question"
    )
    difficulty: int = Field(
        5,
        ge=1,
        le=10,
        description="The estimated difficulty level (1-10) assigned by the AI."
    )
    grade: Optional[int] = Field(
        None,
        ge=1,
        le=13,
        description="The target school grade level (1-13) for this specific question."
    )


class QuestionCreate(BaseSchema):
    """
    Schema for creating a new learning question with integrated validation.

    This model handles the initial ingestion of question data into the global pool.
    It enforces the educational hierarchy and ensures that AI-generated variants
    are properly linked to their original sources for traceability.

    Key Constraints:
    - Must belong to a valid Subject, Topic, and Grade (1-13).
    - Requires at least two answer options.
    - Enforces a 1:1 relationship between the 'answer' index and the 'is_correct' flag.
    - Maintains strict traceability for AI-generated variants (LLM variants).
    """
    subject_id: int = Field(
        ...,
        gt=0,
        description="The unique database identifier of the parent subject."
    )
    topic_id: int = Field(
        ...,
        gt=0,
        description="The unique database identifier of the specific topic."
    )
    parent_question_id: Optional[int] = Field(
        None,
        gt=0,
        description="Reference to the original question ID; required if is_llm_variant is True."
    )
    grade: int = Field(
        ...,
        ge=1,
        le=13,
        description="The target school grade level (1-13) for the curriculum."
    )
    difficulty: int = Field(
        ...,
        ge=1,
        le=10,
        description="The difficulty ranking of the question, where 1 is easiest and 10 is hardest."
    )
    question_text: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="The core content of the question being asked."
    )
    options: list[QuestionOption] = Field(
        ...,
        min_length=2,
        description="A list of possible answer choices (at least two required)."
    )
    answer: int = Field(
        ...,
        ge=0,
        description="The zero-based index pointing to the correct option in the options list."
    )
    explanations: Optional[list[QuestionExplanation]] = Field(
        None,
        description="A list of feedback items providing pedagogical context for the answer."
    )
    is_llm_variant: bool = Field(
        False,
        description="Flag indicating if this is an AI-generated variation of an existing question."
    )

    @model_validator(mode='after')
    def validate_question_logic(self) -> 'QuestionCreate':
        """
        Validates the logical consistency of the question's answers and AI lineage.

        This validator enforces two critical business rules:
        1. **Answer Integrity**: Ensures a strict 1:1 mapping between the `is_correct`
           flag in the options list and the `answer` index.
        2. **AI Traceability**: Ensures that AI-generated variants (`is_llm_variant=True`)
           always reference a `parent_question_id`, while original questions do not.

        Returns:
            QuestionCreate: The validated data instance.

        Raises:
            ValueError: If the answer index is mismatched, multiple correct answers
                        are found, or AI metadata is inconsistent.
        """
        correct_indices = [index for index, option in enumerate(self.options) if option.is_correct]

        if len(correct_indices) != 1:
            raise ValueError(
                f"Validation Error: A question must have exactly one correct answer. "
                f"Found {len(correct_indices)} correct options."
            )

        if self.answer != correct_indices[0]:
            raise ValueError(
                f"Validation Error: The 'answer' index ({self.answer}) does not match "
                f"the option marked as 'is_correct' (Index {correct_indices[0]})."
            )

        if self.is_llm_variant and self.parent_question_id is None:
            raise ValueError(
                "Validation Error: AI-generated variants (is_llm_variant=True) "
                "require a 'parent_question_id' for traceability."
            )

        if not self.is_llm_variant and self.parent_question_id is not None:
            raise ValueError(
                "Validation Error: Original questions (is_llm_variant=False) "
                "cannot have a 'parent_question_id'."
            )

        return self


class QuestionInputExtractedQuestionsUpdate(BaseSchema):
    """
    Schema for batch-updating AI-generated question drafts.

    This model is primarily used by the AI-worker (QuestionGenerator) to return
    a collection of 'proto-questions' after processing the raw source text.
    It serves as a wrapper to maintain a structured list of draft items.
    """
    extracted_questions: list[QuestionInputExtractedQuestions] = Field(
        ...,
        description="A comprehensive list of all AI-generated question drafts "
                    "extracted from the associated raw input."
    )


class QuestionInputCreate(BaseSchema):
    """
    Schema for initializing a new QuestionInput record.

    This model is used when a user or a system service uploads raw content
    (e.g., PDF text, manual notes) to trigger the question generation pipeline.
    It defines the educational context and provides the source material for the LLM.
    """
    user_id: int = Field(
        ...,
        gt=0,
        description="The ID of the user who initiated the generation request."
    )
    subject_id: int = Field(
        ...,
        gt=0,
        description="The subject ID used to ground the AI's context (e.g., History, Biology)."
    )
    topic_id: int = Field(
        ...,
        gt=0,
        description="The specific topic ID to which the generated questions will belong."
    )
    grade: int = Field(
        ...,
        ge=1,
        le=13,
        description="The target school grade level (1-13) for the generated content."
    )
    input_type: InputType = Field(
        ...,
        description="The type of the input material ('scan', 'manual')."
    )
    raw_input: QuestionInputRawInput = Field(
        ...,
        description="The structured raw source material (text and metadata) for the AI to analyze."
    )
    extracted_questions: Optional[list[QuestionInputExtractedQuestions]] = Field(
        None,
        description="Optional pre-generated drafts. Usually left empty during initial creation "
                    "and populated later by the AI extraction service."
    )

    @model_validator(mode="after")
    def validate_raw_input_dependency(self) -> 'QuestionInputCreate':
        """
        Validates that 'raw_input' has sufficient content if the
        input type is not 'scan'. For 'scan', empty content is permitted
        to allow for later OCR processing.
        """
        if self.input_type != InputType.SCAN:

            raw: Optional[QuestionInputRawInput] = self.raw_input

            if len(raw.content.strip()) < 10:
                raise ValueError(
                    f"For input type '{self.input_type}', 'raw_input.content' "
                    "must be provided and at least 10 characters long."
                )
        return self


class QuestionInputRead(BaseSchema):
    """
    Comprehensive schema for reading a QuestionInput record.

    This model provides the full state of a question generation job, including
    the original source material, the AI-generated drafts, and the processing status.
    It is used to display progress in the UI and to retrieve drafts for user review.
    """
    id: int = Field(
        ...,
        description="The unique database primary key of this input record."
    )
    user_id: int = Field(
        ...,
        description="The ID of the user who owns/initiated this generation job."
    )
    subject_id: int = Field(
        ...,
        description="The subject context (e.g., Biology) associated with this input."
    )
    topic_id: int = Field(
        ...,
        description="The specific topic ID to which the resulting questions are linked."
    )
    grade: int = Field(
        ...,
        description="The targeted school grade level (1-13)."
    )
    input_type: InputType = Field(
        ...,
        description="The type of the input material ('scan', 'manual')."
    )
    raw_input: QuestionInputRawInput = Field(
        ...,
        description="The structured source text and metadata provided for extraction."
    )
    extracted_questions: Optional[list[QuestionInputExtractedQuestions]] = Field(
        None,
        description="The current list of AI-generated drafts available for review."
    )
    is_processed: bool = Field(
        ...,
        description="Status flag: True if these drafts have already been converted "
                    "into permanent questions in the global pool."
    )
    created_at: datetime = Field(
        ...,
        description="The UTC timestamp indicating when this record was first created."
    )


class QuestionInputUpdate(BaseSchema):
    """
    Schema for performing partial updates on an existing QuestionInput record.

    This model allows users or administrative services to correct metadata (like
    grade or topic) or adjust the raw source text after the initial upload but
    before the drafts are permanently promoted to the question pool.
    """
    subject_id: Optional[int] = Field(
        None,
        gt=0,
        description="Update the parent subject if the initial assignment was incorrect."
    )
    topic_id: Optional[int] = Field(
        None,
        gt=0,
        description="Update the specific topic to refine the categorization."
    )
    grade: Optional[int] = Field(
        None,
        ge=1,
        le=13,
        description="Adjust the target school grade level (1-13)."
    )
    input_type: Optional[InputType] = Field(
        None,
        description="Change the type of the input material ('scan', 'manual')."
    )
    raw_input: Optional[QuestionInputRawInput] = Field(
        None,
        description="Update or correct the raw source material and its associated metadata."
    )


class QuestionRead(BaseSchema):
    """
    Comprehensive schema for reading a finalized question record.

    This model provides a complete snapshot of a learning item ready for
    educational use. It includes structural metadata (topic, grade, difficulty),
    the core content (text, options, explanations), and its operational state.
    It supports both the adaptive testing engine and administrative auditing.
    """
    id: int = Field(
        ...,
        description="The unique primary key identifier of the question in the database."
    )
    subject_id: int = Field(
        ...,
        description="Foreign key referencing the parent subject curriculum."
    )
    topic_id: int = Field(
        ...,
        description="Foreign key referencing the specific topic this question covers."
    )
    parent_question_id: Optional[int] = Field(
        None,
        description="Reference to the source question ID for AI-generated variants; "
                    "null for original questions."
    )
    grade: int = Field(
        ...,
        ge=1,
        le=13,
        description="The target school grade level (1-13) for curriculum alignment."
    )
    difficulty: int = Field(
        ...,
        ge=1,
        le=10,
        description="The difficulty ranking (1-10) used for adaptive learning algorithms."
    )
    question_text: str = Field(
        ...,
        description="The actual question text to be displayed to the student."
    )
    options: list[QuestionOption] = Field(
        default_factory=list,
        description="A list of structured answer choices including the 'is_correct' indicator."
    )
    answer: int = Field(
        ...,
        description="The zero-based index of the correct choice within the options list."
    )
    explanations: list[QuestionExplanation] = Field(
        default_factory=list,
        description="A list of feedback items providing pedagogical context and reasoning."
    )
    is_llm_variant: bool = Field(
        ...,
        description="True if the question was generated or adapted by an AI model."
    )
    is_active: bool = Field(
        ...,
        description="Indicates if the question is currently available for active learning sessions."
    )


class QuestionStatus(BaseSchema):
    """
    Schema for updating the operational availability of a question.

    This model provides a dedicated interface to toggle a question's status
    within the learning engine. Deactivating a question preserves its
    historical data for analytics while immediately excluding it from
    student-facing practice sessions or exams.
    """
    is_active: bool = Field(
        ...,
        description="Set to True to make the question available for students; "
                    "False to archive it from active learning sessions."
    )


class QuestionUpdate(BaseSchema):
    """
    Schema for performing partial updates on an existing question.

    This model supports PATCH-style updates for metadata and instructional content.
    To maintain logical integrity, it enforces an 'atomic' update rule: if the
    'options' list is modified, the 'answer' index must be updated in the same
    request to prevent a mismatch between the index and the correct choice.
    """
    subject_id: Optional[int] = Field(
        None,
        gt=0,
        description="Update the parent subject reference."
    )
    topic_id: Optional[int] = Field(
        None,
        gt=0,
        description="Update the specific topic reference."
    )
    grade: Optional[int] = Field(
        None,
        ge=1,
        le=13,
        description="Adjust the target school grade level (1-13)."
    )
    difficulty: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Adjust the difficulty ranking (1-10)."
    )
    question_text: Optional[str] = Field(
        None,
        min_length=5,
        max_length=1000,
        description="Update the question wording."
    )
    options: Optional[list[QuestionOption]] = Field(
        None,
        min_length=2,
        description="Update the full list of answer choices. Must be paired with 'answer'."
    )
    answer: Optional[int] = Field(
        None,
        ge=0,
        description="Update the index of the correct option. Must be paired with 'options'."
    )
    explanations: Optional[list[QuestionExplanation]] = Field(
        None,
        description="Update the pedagogical feedback items."
    )

    @model_validator(mode='after')
    def validate_atomic_logic_update(self) -> 'QuestionUpdate':
        """
        Enforces consistency when updating core question logic.

        Rule 1: Atomic Pair - 'options' and 'answer' must be provided together
        to ensure the zero-based index remains valid for the new option set.

        Rule 2: Logical Integrity - The new 'options' list must contain exactly
        one correct choice, and 'answer' must point to it.
        """
        if (self.options is None) != (self.answer is None):
            raise ValueError(
                "Atomic Update Violation: You must provide both 'options' and 'answer' "
                "together to maintain logical consistency."
            )

        if self.options and self.answer is not None:
            correct_indices = [i for i, opt in enumerate(self.options) if opt.is_correct]

            if len(correct_indices) != 1:
                raise ValueError(
                    f"Integrity Error: The new options list must have exactly one "
                    f"correct answer. Found: {len(correct_indices)}"
                )

            if self.answer != correct_indices[0]:
                raise ValueError(
                    f"Logic Mismatch: The provided 'answer' index ({self.answer}) "
                    f"does not point to the option marked as 'is_correct' "
                    f"(Index {correct_indices[0]})."
                )

        return self
