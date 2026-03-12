from datetime import datetime
from apps.roadmap.models import Topic


class TimeDistributionService:

    @staticmethod
    def generate_plan(exam, target_date, study_hours_per_day):

        today = datetime.now().date()
        days_remaining = (target_date - today).days

        if days_remaining < 7:
            raise ValueError("Not enough time to generate roadmap.")

        total_weeks = days_remaining // 7

        weekly_hours = int(study_hours_per_day * 7 * 0.85)
        total_hours = weekly_hours * total_weeks

        coverage_weeks = max(1, int(total_weeks * 0.7))
        practice_weeks = max(1, int(total_weeks * 0.2))
        revision_weeks = total_weeks - coverage_weeks - practice_weeks

        subjects = list(
            Topic.objects.filter(
                exam=exam,
                parent__isnull=True
            ).order_by("-weightage")
        )

        if not subjects:
            raise ValueError("No subjects found for exam.")

        coverage_hours = total_hours * 0.7

        work_queue = []

        # ---------------------------------
        # BUILD WORK QUEUE
        # ---------------------------------
        for subject in subjects:

            subject_weight = subject.weightage or 0
            subject_hours = (subject_weight / 100) * coverage_hours

            subtopics = list(
                Topic.objects.filter(parent=subject).order_by("order")
            )

            if not subtopics:

                work_queue.append({
                    "topic": subject,
                    "remaining_hours": subject_hours
                })
                continue

            scores = []
            total_score = 0

            for subtopic in subtopics:

                weight = subtopic.weightage or 0
                marks = subtopic.pyq_total_marks or 0
                count = subtopic.pyq_count or 0

                score = (
                    weight * 0.5 +
                    marks * 0.3 +
                    count * 0.2
                )

                if subtopic.is_core:
                    score *= 1.25

                scores.append((subtopic, score))
                total_score += score

            if total_score == 0:

                split_hours = subject_hours / len(subtopics)

                for subtopic in subtopics:
                    work_queue.append({
                        "topic": subtopic,
                        "remaining_hours": split_hours
                    })

            else:

                for subtopic, score in scores:

                    allocated_hours = (score / total_score) * subject_hours

                    work_queue.append({
                        "topic": subtopic,
                        "remaining_hours": allocated_hours
                    })

        # ---------------------------------
        # WEEKLY ALLOCATION
        # ---------------------------------
        plan = []
        week_number = 1

        for _ in range(coverage_weeks):

            week_items = []
            remaining_week_hours = weekly_hours

            while remaining_week_hours > 0 and work_queue:

                current = work_queue[0]

                allocated = min(
                    current["remaining_hours"],
                    remaining_week_hours
                )

                if allocated <= 0:
                    work_queue.pop(0)
                    continue

                week_items.append({
                    "topic": current["topic"],
                    "hours": round(allocated, 2)
                })

                current["remaining_hours"] -= allocated
                remaining_week_hours -= allocated

                if current["remaining_hours"] <= 0:
                    work_queue.pop(0)

            plan.append({
                "week_number": week_number,
                "phase": "coverage",
                "items": week_items
            })

            week_number += 1

        # ---------------------------------
        # PRACTICE PHASE
        # ---------------------------------
        top_subjects = subjects[:5]

        for _ in range(practice_weeks):

            total_weight = sum((s.weightage or 0) for s in top_subjects)

            week_items = []

            for subject in top_subjects:

                subject_hours = (
                    (subject.weightage or 0) / total_weight
                ) * weekly_hours

                week_items.append({
                    "topic": subject,
                    "hours": round(subject_hours, 2)
                })

            plan.append({
                "week_number": week_number,
                "phase": "practice",
                "items": week_items
            })

            week_number += 1

        # ---------------------------------
        # REVISION PHASE
        # ---------------------------------
        for _ in range(revision_weeks):

            split_hours = weekly_hours / len(top_subjects)

            week_items = [
                {
                    "topic": subject,
                    "hours": round(split_hours, 2)
                }
                for subject in top_subjects
            ]

            plan.append({
                "week_number": week_number,
                "phase": "revision",
                "items": week_items
            })

            week_number += 1

        return {
            "total_weeks": total_weeks,
            "weekly_hours": weekly_hours,
            "plan": plan
        }
class DayDistributionService:

    @staticmethod
    def distribute_week(week_items, daily_limit):

        days = []
        current_day = 1
        remaining_day_hours = daily_limit

        for item in week_items:

            topic = item["topic"]
            hours = item["hours"]

            while hours > 0:

                allocate = min(hours, remaining_day_hours)

                days.append({
                    "day": current_day,
                    "topic": topic,
                    "hours": round(allocate, 2)
                })

                hours -= allocate
                remaining_day_hours -= allocate

                if remaining_day_hours <= 0:
                    current_day += 1
                    remaining_day_hours = daily_limit

        return days