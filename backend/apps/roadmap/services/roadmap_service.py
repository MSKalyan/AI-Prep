from django.db import transaction
from apps.roadmap.models import Roadmap, RoadmapTopic, Exam
from apps.roadmap.services.time_distribution_service import TimeDistributionService


class RoadmapService:

    @staticmethod
    @transaction.atomic
    def generate_deterministic_roadmap(
        user,
        exam_id,
        target_date,
        study_hours_per_day,
    ):

        exam = Exam.objects.get(id=exam_id)

        plan_result = TimeDistributionService.generate_plan(
            exam,
            target_date,
            study_hours_per_day
        )

        Roadmap.objects.filter(
            user=user,
            is_active=True
        ).update(is_active=False)

        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=target_date,
            total_weeks=plan_result["total_weeks"],
            description=f"Deterministic roadmap for {exam.name}",
            is_active=True
        )
       
        daily_limit = study_hours_per_day

        # -----------------------------
        # Convert weekly plan → daily plan
        # -----------------------------
        for week_data in plan_result["plan"]:

            week_number = week_data["week_number"]
            phase = week_data["phase"]

            current_day = 1
            remaining_day_hours = daily_limit

            for item in week_data["items"]:

                topic = item["topic"]
                topic_hours = int(round(item["hours"])) if item["hours"] > 0 else 1

                while topic_hours > 0:

                    allocated = min(topic_hours, remaining_day_hours)

                    RoadmapTopic.objects.create(
                        roadmap=roadmap,
                        week_number=week_number,
                        day_number=current_day,
                        topic=topic,
                        estimated_hours=allocated,
                        phase=phase,
                        priority=1
                    )

                    topic_hours -= allocated
                    remaining_day_hours -= allocated

                    # Move to next day if limit reached
                    if remaining_day_hours == 0:
                        current_day += 1
                        remaining_day_hours = daily_limit

        return roadmap
        