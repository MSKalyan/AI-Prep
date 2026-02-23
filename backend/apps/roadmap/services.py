import json
from datetime import datetime
from django.db import transaction
from .models import Roadmap, RoadmapTopic, Exam


class RoadmapService:
    """
    Service layer responsible for:
    - roadmap creation
    - AI topic generation
    - fallback logic
    - topic completion
    """

    # =====================================================
    # MAIN GENERATION METHOD
    # =====================================================

    @staticmethod
    @transaction.atomic
    def generate_roadmap(
        user,
        exam_id,
        target_date,
        difficulty_level,
        study_hours_per_day,
        current_knowledge="",
        target_marks=None
    ):

        from apps.ai_service.services import AIService

        # -------------------------------------
        # Fetch exam
        # -------------------------------------

        exam = Exam.objects.get(id=exam_id)

        # -------------------------------------
        # Calculate duration
        # -------------------------------------

        today = datetime.now().date()
        days_until_exam = (target_date - today).days
        total_weeks = max(1, days_until_exam // 7)

        # -------------------------------------
        # Create roadmap
        # -------------------------------------

        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=target_date,
            difficulty_level=difficulty_level,
            total_weeks=total_weeks,
            description=f"Personalized {exam.name} preparation roadmap",
        )

        # -------------------------------------
        # Build AI prompt
        # -------------------------------------

        prompt = f"""
        Create structured weekly roadmap for {exam.name} exam.

        Target date: {target_date}
        Duration: {total_weeks} weeks
        Study hours per day: {study_hours_per_day}
        Difficulty level: {difficulty_level}
        Target marks: {target_marks or "Not specified"}
        Current knowledge: {current_knowledge or "Not specified"}

        Return JSON array:

        [
          {{
            "week_number": 1,
            "title": "Topic title",
            "description": "Explanation",
            "estimated_hours": 10,
            "resources": [],
            "priority": 1
          }}
        ]
        """

        # -------------------------------------
        # Generate topics
        # -------------------------------------

        try:

            ai_response = AIService.generate_structured_content(
                prompt=prompt,
                context="Roadmap generation"
            )

            topics_data = json.loads(ai_response)

            for topic_data in topics_data:

                RoadmapTopic.objects.create(
                    roadmap=roadmap,
                    **topic_data
                )

        except Exception:

            # fallback if AI fails
            RoadmapService._create_default_topics(
                roadmap,
                total_weeks,
                exam.name
            )

        return roadmap

    # =====================================================
    # FALLBACK DEFAULT TOPICS
    # =====================================================

    @staticmethod
    def _create_default_topics(roadmap, total_weeks, exam_name):

        sections = [
            ("Foundation & Core Concepts", f"{exam_name} fundamentals"),
            ("Advanced Topics", "Advanced concepts"),
            ("Practice & Problem Solving", "Problem solving sessions"),
            ("Revision & Mock Tests", "Final preparation"),
        ]

        weeks_per_section = max(1, total_weeks // len(sections))

        week_counter = 1

        for title, description in sections:

            for _ in range(weeks_per_section):

                RoadmapTopic.objects.create(
                    roadmap=roadmap,
                    week_number=week_counter,
                    title=title,
                    description=description,
                    estimated_hours=35,
                    priority=1
                )

                week_counter += 1

    # =====================================================
    # TOPIC COMPLETION
    # =====================================================

    @staticmethod
    def mark_topic_completed(topic_id, user):

        try:

            topic = RoadmapTopic.objects.get(
                id=topic_id,
                roadmap__user=user
            )

            topic.is_completed = True
            topic.completed_at = datetime.now()
            topic.save()

            return topic

        except RoadmapTopic.DoesNotExist:

            return None
