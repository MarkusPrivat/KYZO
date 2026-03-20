from datetime import datetime, timezone
from typing import Optional, Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from apps.kyzo.config.config import UserRole, InputType


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
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
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
    __tablename__ = 'questions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id'))
    parent_question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'), nullable=True)

    grade: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    options: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
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
    __tablename__ = 'question_origins'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    question_id: Mapped[int] = mapped_column(ForeignKey('questions.id'))
    question_input_id: Mapped[int] = mapped_column(ForeignKey('question_inputs.id'))

    def __repr__(self):
        return (f"<question_origin(id={self.id}, question_id={self.question_id}, "
                f"question_input_id={self.question_input_id})>")

    def __str__(self):
        return f"Question-ID {self.question_id} originates from Input-ID {self.question_input_id}"
