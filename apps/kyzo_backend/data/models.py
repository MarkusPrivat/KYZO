"""
models.py - Database models for the Kyzo adaptive learning platform.

This module defines the complete SQLAlchemy ORM model structure for the Kyzo application,
a digital learning platform that combines traditional subject-based learning with
AI-powered question generation and adaptive testing. The models support a hierarchical
knowledge structure (Subjects → Topics → Questions) and track user performance,
competency levels, and test history.

Core Components:
----------------
1. Knowledge Hierarchy:
   - Subject: High-level academic disciplines (e.g., Mathematics, Biology)
   - Topic: Specific learning areas within subjects (e.g., Algebra, Photosynthesis)
   - Question: Individual learning items with adaptive difficulty and AI support
   - QuestionInput: Stores raw user-provided content for AI question generation
   - QuestionOrigin: Provides traceability between generated questions and sources

2. User Management:
   - User: Represents students, teachers, and admins with role-based access
   - UserCompetence: Tracks mastery levels per topic for adaptive learning

3. Testing System:
   - Test: Records assessment sessions with performance metrics
   - TestQuestion: Links tests to specific questions and captures responses

Key Features:
-------------
- Hierarchical Knowledge Structure: Subjects contain Topics contain Questions
- Adaptive Learning: UserCompetence tracks mastery scores (0.0-1.0) per topic
- AI-Powered Content: Questions can be original or AI-generated variants
- Comprehensive Testing: Supports both subject-wide and topic-specific assessments
- Role-Based Access: Users have distinct roles (STUDENT, TEACHER, ADMIN)
- Temporal Tracking: All models include timestamps for created/updated records
- JSON Support: Complex data like question options stored as structured JSON

Relationships:
--------------
- User ↔ Test (1:n): Users take multiple tests
- User ↔ UserCompetence (1:n): Users have mastery scores for multiple topics
- Subject ↔ Topic (1:n): Subjects contain multiple topics
- Topic ↔ Question (1:n): Topics contain multiple questions
- Test ↔ TestQuestion (1:n): Tests contain multiple question instances
- Question ↔ QuestionInput (n:m): Questions can originate from multiple inputs
- Question ↔ Question (1:n): Original questions can have AI-generated variants

Usage Notes:
-----------
- All datetime fields use UTC timezone
- String fields have appropriate length limits
- JSON fields store structured data like question options and explanations
- Cascade deletes ensure data integrity when parent records are removed
- The UserRole and InputType enums are imported from the config module
"""
from datetime import datetime, timezone
from typing import Optional, Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from apps.kyzo_backend.config.config import UserRole, InputType


class Base(DeclarativeBase):
    """
    Base class for all declarative models in the Kyzo application.

    This class inherits from SQLAlchemy's `DeclarativeBase` and serves
    as the central registry for the ORM mapping. All database models
    must inherit from this class to be recognized by the SQLAlchemy
    mapper and to be included in the database schema generation.
    """

db = SQLAlchemy(model_class=Base)


class Subject(db.Model):
    """
    Represents a high-level academic field or school subject (e.g., Mathematics, Biology).

    This model serves as the top-level container in the knowledge hierarchy.
    It groups various topics and allows for subject-wide testing and reporting.

    Attributes:
        id (int): Unique identifier and primary key.
        name (str): Unique name of the subject (e.g., 'Physics').
        is_active (bool): Flag to toggle the visibility/availability of the subject.
        topics (list[Topic]): Relationship linking to all specific topics within this subject.
    """
    __tablename__ = 'subjects'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    topics: Mapped[list["Topic"]] = relationship("Topic", back_populates="subject")

    def __repr__(self):
        return f"<subject(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def __str__(self):
        return f"{self.name} (active = {self.is_active})"


class Test(db.Model):
    """
    Represents an individual assessment session for a user.

    A test can be either subject-wide (general) or focused on a specific topic.
    It tracks the user's performance, difficulty level, and stores AI-generated
    feedback upon completion.

    Attributes:
        id (int): Primary key for the test instance.
        user_id (int): Foreign key linking to the user who took the test.
        subject_id (int): Foreign key linking to the academic subject.
        topic_id (int, optional): Foreign key to a specific topic. If null,
            it represents a general subject test.
        grade (int): The school grade level the test was designed for.
        difficulty (float): The dynamic difficulty level of the test (1.0 to 10.0).
        score (int, optional): The final percentage or points achieved (0-100).
        ai_feedback_summary (str, optional): LLM-generated summary of the test results.
        is_done (bool): Flag indicating if the test session is completed.
        started_at (datetime): Timestamp when the test was initialized (UTC).
        completed_at (datetime, optional): Timestamp when the test was finished (UTC).
    """
    __tablename__ = 'tests'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.id'), nullable=False)
    topic_id: Mapped[Optional[int]] = mapped_column(ForeignKey('topics.id'), nullable=True)

    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    score: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    ai_feedback_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="tests")
    test_questions: Mapped[list["TestQuestion"]] = relationship(
        "TestQuestion",
        back_populates="test"
    )

    def __repr__(self):
        return f"<test(id={self.id}, user_id='{self.user_id}', is_done={self.is_done})>"

    def __str__(self):
        return f"Test-ID: {self.id} (done = {self.is_done})"


class TestQuestion(db.Model):
    """
    Represents the association between a specific test run and a single question.

    This model stores the student's response, the correctness of the answer,
    and performance metrics like time spent. It acts as the primary data
    source for calculating mastery scores and providing granular feedback.

    Attributes:
        id (int): Primary key for the test-question association.
        test_id (int): Foreign key linking to the parent test session.
        question_id (int): Foreign key linking to the specific question asked.
        student_choice (int, optional): The index of the option selected by
            the student (e.g., 0, 1, 2).
        is_correct (bool, optional): Flag indicating if the student's
            choice was correct.
        is_done (bool): Flag indicating if this specific question has
            been answered.
        points_earned (int, optional): Points awarded for this question,
            usually weighted by difficulty.
        time_spent_milliseconds (int, optional): Duration in milliseconds
            the student spent on this question.
        question (Question): Relationship back to the Question model.
        test (Test): Relationship back to the Test model.
    """
    __tablename__ = 'test_questions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    test_id: Mapped[int] = mapped_column(ForeignKey('tests.id'), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=False)

    student_choice: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, default=None, nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    points_earned: Mapped[Optional[int]] = mapped_column(Integer, default=None, nullable=True)
    time_spent_milliseconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=None,
        nullable=True
    )

    question: Mapped["Question"] = relationship("Question", back_populates="test_occurrences")
    test: Mapped["Test"] = relationship("Test", back_populates="test_questions")

    def __repr__(self):
        return f"<test_question(id={self.id}, test_id='{self.test_id}', is_done={self.is_done})>"

    def __str__(self):
        return f"Test-Question-ID: {self.id} (done = {self.is_done})"


class Topic(db.Model):
    """
    Represents a specific subject area or learning module (e.g., 'Photosynthesis',
    'Linear Equations').

    Topics are nested within a Subject and serve as the primary categorization
    level for questions and user competence tracking. They include metadata
    regarding the expected school grade for curriculum alignment.

    Attributes:
        id (int): Unique identifier and primary key for the topic.
        subject_id (int): Foreign key linking the topic to its parent subject.
        name (str): Descriptive name of the topic.
        is_active (bool): Flag to toggle whether the topic is available for study.
        grade_expected (int): The curriculum-standard school grade for this topic.
        subject (Subject): Relationship back to the parent Subject model.
    """
    __tablename__ = 'topics'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.id'), nullable=False)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    grade_expected: Mapped[int] = mapped_column(Integer, nullable=False)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="topics")

    def __repr__(self):
        return f"<topic(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def __str__(self):
        return f"{self.name} (active = {self.is_active})"


class User(db.Model):
    """
    Represents a registered person within the Kyzo App (Student, Teacher, or Admin).

    This model serves as the central identity for authentication and progress tracking.
    It maintains the user's current grade level and provides access to their
    complete testing history and competency profiles across different topics.

    Attributes:
        id (int): Unique identifier and primary key for the user.
        name (str): The display name or username.
        email (str): As a unique user identifier.
        password (str, optional): Hashed password for authentication.
        grade (int): The current school grade level of the student.
        role (UserRole): The authorization level (STUDENT, TEACHER, or ADMIN).
        is_active (bool): Flag to enable or disable the account.
        created_at (datetime): Timestamp of account registration (UTC).
        tests (list[Test]): Relationship to all tests taken by the user.
            Includes cascading deletes.
        competences (list[UserCompetence]): Relationship to the user's
            mastery levels across topics.
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(100), default=None, nullable=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    tests: Mapped[list["Test"]] = relationship(
        "Test",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    competences: Mapped[list["UserCompetence"]] = relationship(
        "UserCompetence",
        back_populates="user"
    )

    def __repr__(self):
        return (f"<user(id={self.id}, name='{self.name}', role={self.role}, "
                f"is_active={self.is_active})>")

    def __str__(self):
        return f"{self.name} (active = {self.is_active})"


class UserCompetence(db.Model):
    """
    Tracks and stores the aggregated knowledge level (mastery) of a user per topic.

    This model serves as the primary data source for Kyzo's adaptive learning engine.
    It calculates how well a student understands a specific area based on their
    historical performance, allowing for personalized difficulty adjustments.

    Attributes:
        id (int): Unique identifier and primary key for the competence entry.
        user_id (int): Foreign key linking to the specific user.
        topic_id (int): Foreign key linking to the academic topic.
        mastery_score (float): A calculated score (0.0 to 1.0) representing
            the user's proficiency level in this topic.
        total_attempts (int): The cumulative number of questions the user
            has answered for this topic.
        last_improved_at (datetime): Timestamp of the last successful
            update or performance increase (UTC).
    """
    __tablename__ = 'user_competence'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'), nullable=False)

    mastery_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_improved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return (f"<user_competence(id={self.id}, user_id='{self.user_id}', "
                f"topic_id={self.topic_id}, mastery_score={self.mastery_score})>")

    def __str__(self):
        return (f"User-Competence-ID: {self.id} (topic = {self.topic_id}, "
                f"mastery score = {self.mastery_score})")



class Question(db.Model):
    """
    Represents an individual learning item or quiz question.

    This model supports both original content and AI-generated variations
    through a parent-child relationship. It stores multiline text,
    multiple-choice options, and detailed pedagogical explanations
    using JSON structures.

    Attributes:
        id (int): Unique identifier and primary key for the question.
        topic_id (int): Foreign key linking the question to a specific topic.
        parent_question_id (int, optional): Self-referencing foreign key for
            linking variations back to an original question.
        grade (int): Target school grade level for this question.
        difficulty (int): Difficulty ranking (e.g., 1 to 10) for adaptive logic.
        question_text (str): The actual content or prompt of the question.
        options (list[dict]): JSON array containing the possible answer
            texts (e.g., [{'text': 'Option A'}, {'text': 'Option B'}]).
        answer (int): The index of the correct option (e.g., 0 for the first option).
        explanations (list[dict]): JSON array containing detailed feedback
            and reasoning for each option.
        is_llm_variant (bool): Flag indicating if the question was
            automatically generated or modified by an AI.
        is_active (bool): Flag to toggle whether the question is available
            in tests.
        test_occurrences (list[TestQuestion]): Relationship to all test
            instances where this question was used.
    """
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'))
    parent_question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=True)

    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    answer: Mapped[int] = mapped_column(Integer, nullable=False)
    explanations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    is_llm_variant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    test_occurrences: Mapped[list["TestQuestion"]] = relationship(
        "TestQuestion",
        back_populates="question"
    )

    def __repr__(self):
        return (f"<question(id={self.id}, is_llm_variant={self.is_llm_variant}, "
                f"is_active={self.is_active})>")

    def __str__(self):
        return f"Question-ID: {self.id} (active = {self.is_active})"


class QuestionInput(db.Model):
    """
    Represents the raw data source provided by a user to generate questions.

    This model stores the original input (e.g., PDF content, text, or URLs)
    before it is processed by the AI. It also holds the temporarily
    extracted JSON structures before they are validated and converted into
    individual Question records.

    Attributes:
        id (int): Unique identifier and primary key.
        user_id (int): Foreign key linking to the user who uploaded the content.
        topic_id (int): Foreign key linking the input to a specific topic.
        input_type (InputType): Enum indicating the source format (e.g., PDF, TEXT).
        raw_input (dict): JSON object containing the raw source data or metadata.
        extracted_questions (list[dict], optional): Preliminary JSON data
            parsed by the LLM before final Question objects are created.
        created_at (datetime): Timestamp of the upload/creation (UTC).
    """
    __tablename__ = 'question_inputs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'))

    input_type: Mapped[InputType] = mapped_column(Enum(InputType), nullable=False)
    raw_input: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    extracted_questions: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        return f"<question_input(id={self.id}, user_id={self.user_id}, topic_id={self.topic_id})>"

    def __str__(self):
        return f"Question-Input-ID: {self.id} (user = {self.user_id})"


class QuestionOrigin(db.Model):
    """
    A many-to-many junction table linking Questions to their original Inputs.

    This model provides traceability, allowing the system to track exactly
    which upload or raw data source (QuestionInput) was used to create
    a specific Question. This is crucial for debugging AI extractions and
    managing content lineage.

    Attributes:
        id (int): Unique identifier and primary key.
        question_id (int): Foreign key linking to the resulting Question.
        question_input_id (int): Foreign key linking to the source QuestionInput.
    """
    __tablename__ = 'question_origins'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'))
    question_input_id: Mapped[int] = mapped_column(ForeignKey('question_inputs.id'))

    def __repr__(self):
        return (f"<question_origin(id={self.id}, question_id={self.question_id}, "
                f"question_input_id={self.question_input_id})>")

    def __str__(self):
        return f"Question-ID {self.question_id} originates from Input-ID {self.question_input_id}"
