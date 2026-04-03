from pydantic import ValidationError
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


from apps.kyzo_backend.core.database import SESSION_LOCAL, engine
from apps.kyzo_backend.data import Base, Subject, Topic, User, QuestionInput
from apps.kyzo_backend.schemas import (UserCreate, SubjectCreate,
                                       TopicCreate, QuestionInputCreate)
from apps.kyzo_backend.scripts.seed_data import SeedData


def seed_data():
    """
    Orchestrates the database initialization and seeding process.

    The function performs the following steps:
    1. Database Guard: Checks if the 'users' table already exists to prevent
       accidental data corruption or duplicate seeding.
    2. Schema Creation: Generates all database tables defined in the metadata.
    3. Sequential Seeding: Validates and inserts seed data from 'SeedData'
       in a specific order (Users -> Subjects -> Topics -> Question Inputs)
        to maintain referential integrity.
    4. Validation & Error Handling: Uses Pydantic schemas for data validation
       and handles SQLAlchemy exceptions with automatic rollbacks on failure.

    Note:
        If seeding fails at any stage, a rollback is performed to ensure
        database consistency.
    """
    # --- DATABASE GUARD ---
    inspector = inspect(engine)
    if inspector.has_table("users"):
        print("⚠️ Database is not empty. Seeding aborted to prevent data corruption.")
        print("💡 Hint: Delete the database file /data/kyzo-data.sqlite if you want to re-seed.")
        return

    print("📦 Initializing database schema...")
    Base.metadata.create_all(bind=engine)

    db: Session = SESSION_LOCAL()
    print("🚀 Starting database seeding...")

    try:
        # --- 1. SEED USERS ---
        print("  -> Seeding Users...")
        validated_users = [UserCreate(**user) for user in SeedData.USERS]
        for user in validated_users:
            user_dict = user.model_dump()
            new_user = User(**user_dict)
            db.add(new_user)

        db.flush()
        print(f"✅ Database successfully seeded with {len(SeedData.USERS)} users.")

        # --- 2. SEED SUBJECTS ---
        print("  -> Seeding Subjects...")
        validated_subjects = [SubjectCreate(**subject) for subject in SeedData.SUBJECTS]
        for subject in validated_subjects:
            subject_dict = subject.model_dump()
            new_subject = Subject(**subject_dict)
            db.add(new_subject)

        db.flush()
        print(f"✅ Database successfully seeded with {len(SeedData.SUBJECTS)} subjects.")

        # --- 3. SEED TOPICS ---
        print("  -> Seeding Topics...")
        validated_topics = [TopicCreate(**topic) for topic in SeedData.TOPICS]
        for topic in validated_topics:
            topic_dict = topic.model_dump()
            new_topic = Topic(**topic_dict)
            db.add(new_topic)

        db.flush()
        print(f"✅ Database successfully seeded with {len(SeedData.TOPICS)} topics.")

        # --- 4. SEED QUESTION_INPUTS ---
        print("  -> Seeding Question inputs...")
        validated_question_input = [QuestionInputCreate(**question_input)
                                    for question_input in SeedData.QUESTION_INPUTS]
        for question_input in validated_question_input:
            question_input_dict = question_input.model_dump()
            new_question_input = QuestionInput(**question_input_dict)
            db.add(new_question_input)

        db.flush()
        print(f"✅ Database successfully seeded with {len(SeedData.QUESTION_INPUTS)} "
              f"question inputs.")

        db.commit()

    except ValidationError as error:
        db.rollback()
        print(f"❌ Validation failed: {error.errors()}")
    except SQLAlchemyError as error:
        db.rollback()
        print(f"❌ Database error: {error}")
    except Exception as error:
        db.rollback()
        print(f"❌ Unexpected error: {error}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
