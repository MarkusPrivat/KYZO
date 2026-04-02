from typing import Optional
from datetime import datetime

from pydantic import Field, field_validator

from apps.kyzo_backend.config import SchemasMessages
from .base_schemas import BaseSchema


class TestGenerate(BaseSchema):
    """
    Schema for initializing a new assessment session.

    This DTO (Data Transfer Object) carries the necessary configuration
    to generate a tailored test, supporting both broad subject-level
    assessments and granular topic-specific drills.

    Attributes:
        user_id (int): ID of the student taking the test.
        subject_id (int): ID of the academic discipline.
        topic_id (int, optional): Specific topic filter. If None, the test
            will pull questions from the entire subject pool.
        grade (int): Target school grade (e.g., 5 to 13).
        difficulty (float): Initial difficulty level (range: 1.0 to 10.0).
    """
    user_id: int = Field(..., description="The ID of the user starting the test")
    subject_id: int = Field(..., description="The subject ID for the test")
    topic_id: Optional[int] = Field(None, description="Optional topic ID for focused tests")

    grade: int = Field(..., ge=1, le=13, description="School grade level (1-13)")
    difficulty: float = Field(
        5.0,
        ge=1.0,
        le=10.0,
        description="Initial difficulty level from 1.0 to 10.0"
    )

    @field_validator("difficulty")
    @classmethod
    def round_difficulty(cls, value: float) -> float:
        """Ensures the difficulty has a maximum of one decimal place."""
        return round(value, 1)


class TestFinalize(BaseSchema):
    """
    Schema for submitting and finalizing an assessment session.

    This DTO is used when a student finishes their test. It triggers the
    transition of the test state to 'completed', which typically
    initiates the scoring logic and AI feedback generation on the server.

    Attributes:
        is_active (bool): Must be True to signal completion.
        completed_at (datetime): The client-side timestamp of when the
            user clicked 'Submit'.
    """
    is_done: bool = Field(
        ...,
        description="Flag to confirm the test is finished. Must be True."
    )
    completed_at: datetime = Field(
        ...,
        description="The ISO-formatted UTC timestamp of completion."
    )

    @field_validator("is_done")
    @classmethod
    def validate_is_done(cls, value: bool) -> bool:
        """
        Validates the completion flag for the finalization process.

        Since this schema is specifically designed for the 'finalize'
        transition, the 'is_done' attribute must be explicitly True.
        This prevents accidental or malformed requests from reaching
        the scoring logic without a clear intent to finish the test.

        Args:
            value (bool): The boolean flag sent by the client.

        Returns:
            bool: The validated True value.

        Raises:
            ValueError: If 'is_done' is False, as a partial update
                is not permitted via this specific DTO.
        """
        if not value:
            raise ValueError(SchemasMessages.IS_DONE_MUST_BE_TRUE)
        return value


class TestQuestionCreate(BaseSchema):
    """
    Schema for initializing a specific question instance within a test session.

    This DTO is primarily used by the test generation engine to link a
    pre-existing question template to a unique test run. It sets the
    foundational scoring parameters for that specific occurrence.

    Attributes:
        test_id (int): Foreign key referencing the active test session.
        question_id (int): Foreign key referencing the static question content.
        points_max (int): The maximum weight of this question within the
            context of this test (defaults to 1).
    """
    test_id: int = Field(
        ...,
        gt=0,
        description="The unique database ID of the parent test session."
    )
    question_id: int = Field(
        ...,
        gt=0,
        description="The unique database ID of the question template."
    )
    points_max: int = Field(
        1,
        ge=1,
        description="The maximum achievable points for this question instance."
    )


class TestQuestionFinalize(BaseSchema):
    """
    Schema for submitting a student's response to a specific test question.

    This DTO is used during an active test session when a student selects an
    option. Submitting this data triggers the server-side evaluation logic,
    which calculates correctness, awards points, and updates the 'is_done'
    status of the question instance.

    Attributes:
        student_choice (int): The 0-based index of the option selected by
            the student. Must correspond to the available options for
            the linked question.
        time_spent_milliseconds (int): The total duration the student spent
            viewing and processing this specific question before submission.
    """
    student_choice: int = Field(
        ...,
        ge=0,
        description="The 0-based index of the chosen answer option."
    )
    time_spent_milliseconds: int = Field(
        ...,
        ge=0,
        description="Engagement time in milliseconds (used for performance analytics)."
    )

    @field_validator("student_choice")
    @classmethod
    def validate_choice_format(cls, value: int) -> int:
        """
        Ensures the choice index is a valid non-negative integer.

        Args:
            value (int): The index provided by the client.

        Returns:
            int: The validated index.

        Raises:
            ValueError: If the index is negative.
        """
        if value < 0:
            raise ValueError("The selected option index cannot be negative.")
        return value


class TestQuestionRead(BaseSchema):
    """
    DTO for displaying a question's result within a test context.

    Includes the student's interaction data and the final evaluation.
    Can be used for both active test screens and post-test reviews.

    Attributes:
        id (int): Unique ID of this test-question occurrence.
        question_id (int): ID of the original question content.
        student_choice (Optional[int]): The index selected by the student.
        is_correct (Optional[bool]): Whether the answer was right.
        is_done (bool): Whether this question has been answered.
        points_earned (Optional[int]): Points awarded.
        points_max (int): Total possible points.
        time_spent_milliseconds (Optional[int]): Duration of engagement.
    """
    id: int = Field(..., description="Unique ID of the test-question entry.")
    question_id: int = Field(..., description="ID of the underlying question.")
    student_choice: Optional[int] = Field(None, description="The selected option index.")
    is_correct: Optional[bool] = Field(None, description="Correctness flag.")
    is_done: bool = Field(..., description="Answer status.")
    points_earned: Optional[int] = Field(None, description="Points achieved.")
    points_max: int = Field(..., description="Maximum possible points.")
    time_spent_milliseconds: Optional[int] = Field(
        None,
        description="Time spent on this question in ms."
    )


class TestRead(BaseSchema):
    """
    Data transfer object (DTO) for returning comprehensive test session details.

    This schema provides a complete read-only snapshot of an assessment,
    including its configuration, progress status, achieved scores, and the
    associated collection of questions. It serves as the primary data
    structure for test results and review screens.

    Attributes:
        id (int): Unique database identifier for the test session.
        user_id (int): Reference to the student who took the test.
        subject_id (int): Reference to the academic subject.
        topic_id (Optional[int]): Reference to the specific topic (if applicable).
        grade (int): The school grade level targeted by this test.
        difficulty (float): The calculated or initial difficulty level (1.0-10.0).
        score (Optional[int]): The total points achieved by the student.
            Only available once 'is_done' is True.
        max_score (Optional[int]): The maximum possible points for this test.
        ai_feedback_summary (Optional[str]): AI-generated qualitative analysis
            of the overall performance.
        started_at (datetime): Timestamp of when the test was initialized.
        is_done (bool): Flag indicating if the test has been submitted.
        completed_at (Optional[datetime]): Timestamp of completion.
            Null if 'is_done' is False.
        test_question (list[TestQuestionRead]): Nested list of question objects
            linking the session to specific question content.
    """
    id: int = Field(..., description="Unique database ID of the test session.")
    user_id: int = Field(..., description="The ID of the user who owns this test.")
    subject_id: int = Field(..., description="The ID of the subject being assessed.")
    topic_id: Optional[int] = Field(
        None,
        description="The ID of the specific topic, if it's a focused test."
    )
    grade: int = Field(..., description="The academic grade level (1-13).")
    difficulty: float = Field(
        ...,
        description="The difficulty level of the test session (1.0 to 10.0)."
    )
    score: Optional[int] = Field(
        None,
        description="Achieved points. Usually null until the test is submitted."
    )
    max_score: Optional[int] = Field(
        None,
        description="Total possible points reachable in this assessment."
    )
    ai_feedback_summary: Optional[str] = Field(
        None,
        description="A summary of the AI's feedback on the student's performance."
    )
    started_at: datetime = Field(
        ...,
        description="The ISO-formatted UTC timestamp when the test started."
    )
    is_done: bool = Field(
        ...,
        description="Boolean flag indicating whether the test is completed."
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp of completion. Only present if is_done is True."
    )
    test_question: list[TestQuestionRead] = Field(
        default_factory=list,
        description="The list of questions associated with this test session."
    )


class TestSessionRead(BaseSchema):
    """
    Composite DTO representing the live state of a test session.

    Bundles the core test metadata with the next actionable question.
    This allows the frontend to manage transitions between questions
    and the final completion state seamlessly.

    Attributes:
        test (TestRead): The full metadata of the current test session
            (e.g., total score, user_id, subject_id).
        next_question (Optional[TestQuestionRead]): The next unanswered
            question in the sequence. Returns None if all questions
            are already completed.
        all_done (bool): A flag indicating if there are no more pending
            questions left in this session.
    """
    test: TestRead = Field(
        ...,
        description="The full metadata of the current test session (score, user, subject)."
    )
    next_question: Optional[TestQuestionRead] = Field(
        None,
        description="The next unanswered question in the sequence. Returns None if all questions are completed."
    )
    all_done: bool = Field(
        ...,
        description="A flag indicating if there are no more pending questions in this session."
    )
