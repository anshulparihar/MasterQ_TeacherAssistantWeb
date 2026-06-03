import asyncio
import json
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.config import settings

async def seed_data():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    subjects = [
        {"name": "Physics", "levels": ["11", "12", "UG"]},
        {"name": "Chemistry", "levels": ["11", "12", "UG"]},
        {"name": "Mathematics", "levels": ["11", "12", "UG"]},
        {"name": "Biology", "levels": ["11", "12", "UG"]},
        {"name": "History", "levels": ["9", "10", "11", "12"]},
        {"name": "Geography", "levels": ["9", "10", "11", "12"]},
        {"name": "Economics", "levels": ["11", "12"]},
        {"name": "Political Science", "levels": ["11", "12"]},
        {"name": "English", "levels": ["9", "10", "11", "12"]},
        {"name": "Computer Science", "levels": ["11", "12", "UG"]}
    ]

    exam_types = [
        {
            "name": "CBSE Class 12",
            "guidelines": {
                "easy": {"mcq_marks": 1, "theory_marks": 2, "topic_scope": "single"},
                "medium": {"mcq_marks": 1, "theory_marks": 3, "topic_scope": "2-3 topics"},
                "hard": {"mcq_marks": 1, "theory_marks": 5, "topic_scope": "multi-topic"},
                "complexity_description": "Standard board level questions strictly adhering to NCERT syllabus constraints.",
                "pattern_notes": "MCQs have 4 options. Theory questions expect step-by-step descriptive answers."
            }
        },
        {
            "name": "JEE Mains",
            "guidelines": {
                "easy": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "single formula application"},
                "medium": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "2-3 concept integration"},
                "hard": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "deep analytical reasoning"},
                "complexity_description": "High complexity reasoning testing conceptual clarity over speed. -1 penalty for incorrect MCQs.",
                "pattern_notes": "Single correct option. Heavy focus on numerical calculation and graph analysis."
            }
        },
        {
            "name": "JEE Advanced",
            "guidelines": {
                "easy": {"mcq_marks": 3, "theory_marks": 3, "topic_scope": "2 topics minimum"},
                "medium": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "multi-topic deep integration"},
                "hard": {"mcq_marks": 5, "theory_marks": 5, "topic_scope": "extreme reasoning / unseen scenarios"},
                "complexity_description": "The toughest engineering entrance exam. Expect multi-correct options, integer types, and paragraph-based logic.",
                "pattern_notes": "Partial marking applies. Never ask direct formula-based questions."
            }
        },
        {
            "name": "NEET",
            "guidelines": {
                "easy": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "single"},
                "medium": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "2-3 topics"},
                "hard": {"mcq_marks": 4, "theory_marks": 4, "topic_scope": "multi-topic application"},
                "complexity_description": "Fast-paced medical entrance examination. High accuracy requirement.",
                "pattern_notes": "Strictly MCQ. +4 for correct, -1 for incorrect. Focus on diagram-based memory and fast calculation."
            }
        },
        {
            "name": "UPSC Prelims",
            "guidelines": {
                "easy": {"mcq_marks": 2, "theory_marks": 2, "topic_scope": "single"},
                "medium": {"mcq_marks": 2, "theory_marks": 2, "topic_scope": "2-3 topics"},
                "hard": {"mcq_marks": 2, "theory_marks": 2, "topic_scope": "multi-topic analytical"},
                "complexity_description": "Administrative services preliminary exam. Heavy current affairs and deep conceptual linkage.",
                "pattern_notes": "MCQ format with -0.66 penalty. Often uses 'Statement 1 and 2 are correct' logic structures."
            }
        },
        {
            "name": "UPSC Mains",
            "guidelines": {
                "easy": {"mcq_marks": 0, "theory_marks": 10, "topic_scope": "descriptive single topic"},
                "medium": {"mcq_marks": 0, "theory_marks": 15, "topic_scope": "comparative 2-3 topics"},
                "hard": {"mcq_marks": 0, "theory_marks": 20, "topic_scope": "essay-style broad integration"},
                "complexity_description": "Subjective paper testing articulation, multidimensional views, and analytical depth.",
                "pattern_notes": "No MCQs. Answers must be structured with introduction, body (points/paragraphs), and conclusion."
            }
        },
        {
            "name": "Class 10 CBSE",
            "guidelines": {
                "easy": {"mcq_marks": 1, "theory_marks": 2, "topic_scope": "single direct concept"},
                "medium": {"mcq_marks": 1, "theory_marks": 3, "topic_scope": "2 topics basic linkage"},
                "hard": {"mcq_marks": 1, "theory_marks": 4, "topic_scope": "application based"},
                "complexity_description": "Foundational board examination. Straightforward questions testing basic comprehension.",
                "pattern_notes": "Includes MCQs, very short answer (VSA), short answer (SA), and long answer (LA)."
            }
        }
    ]

    async with async_session() as session:
        # Seed Subjects
        for sub in subjects:
            sql_check = "SELECT id FROM subjects WHERE name = :name"
            res = await session.execute(text(sql_check), {"name": sub["name"]})
            if not res.first():
                sql_insert = "INSERT INTO subjects (id, name, academic_levels) VALUES (:id, :name, :levels)"
                await session.execute(text(sql_insert), {
                    "id": str(uuid.uuid4()),
                    "name": sub["name"],
                    "levels": json.dumps(sub["levels"])
                })
        
        # Seed Exam Types
        for ext in exam_types:
            sql_check = "SELECT id FROM exam_types WHERE name = :name"
            res = await session.execute(text(sql_check), {"name": ext["name"]})
            if not res.first():
                sql_insert = "INSERT INTO exam_types (id, name, guidelines) VALUES (:id, :name, :guidelines)"
                await session.execute(text(sql_insert), {
                    "id": str(uuid.uuid4()),
                    "name": ext["name"],
                    "guidelines": json.dumps(ext["guidelines"])
                })

        await session.commit()
        print("Database seeded successfully with Subjects and Exam Types!")

if __name__ == "__main__":
    asyncio.run(seed_data())
