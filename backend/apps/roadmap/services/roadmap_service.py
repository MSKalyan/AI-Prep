from django.db import transaction, IntegrityError
from apps.roadmap.models import Roadmap, RoadmapTopic, Exam
from apps.roadmap.services.pyq.time_distribution_service import TimeDistributionService
from apps.roadmap.services.pyq.weightage_service import WeightageService


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

        # update weights from PYQ data before generating plan
        WeightageService.compute_weightage(exam)

        plan_result = TimeDistributionService.generate_plan(
            exam,
            target_date,
            study_hours_per_day
        )

        # deactivate existing roadmap
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

        # ----------------------------------
        # Convert weekly plan → daily plan
        # ----------------------------------
        for week_data in plan_result["plan"]:

            week_number = week_data["week_number"]
            phase = week_data["phase"]

            current_day = 1
            remaining_day_hours = daily_limit

            for item in week_data["items"]:

                topic = item["topic"]
                topic_hours = item["hours"]

                while topic_hours > 0:

                    if current_day > 7:
                        break

                    allocated = min(topic_hours, remaining_day_hours)

                    # Avoid duplicate topic/day insertion by advancing day if needed
                    inserted = False
                    attempt_day = current_day
                    while not inserted and attempt_day <= 7:
                        if RoadmapTopic.objects.filter(
                            roadmap=roadmap,
                            week_number=week_number,
                            day_number=attempt_day,
                            topic=topic
                        ).exists():
                            attempt_day += 1
                            continue

                        RoadmapTopic.objects.create(
                            roadmap=roadmap,
                            week_number=week_number,
                            day_number=attempt_day,
                            topic=topic,
                            estimated_hours=round(allocated, 2),
                            phase=phase,
                            priority=1
                        )
                        inserted = True

                    if not inserted:
                        # if cannot insert in this week due duplicates, skip remaining hours
                        break

                    topic_hours -= allocated
                    remaining_day_hours -= allocated

                    if remaining_day_hours <= 0:
                        current_day += 1
                        remaining_day_hours = daily_limit

        return roadmap