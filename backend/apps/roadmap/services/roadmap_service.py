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

        roadmap = Roadmap.objects.create(
            user=user,
            exam=exam,
            target_date=target_date,
            total_weeks=plan_result["total_weeks"],
            description=f"Deterministic roadmap for {exam.name}",
        )

        # Single unified weekly structure
        for week_data in plan_result["plan"]:

            for item in week_data["items"]:

                RoadmapTopic.objects.create(
                    roadmap=roadmap,
                    week_number=week_data["week_number"],
                    topic=item["topic"],
                    estimated_hours = int(round(item["hours"])) if item["hours"] > 0 else 1,  # Ensure at least 1 hour if 
                    phase=week_data["phase"],
                    priority=1
                )

        return roadmap