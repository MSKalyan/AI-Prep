from datetime import datetime
from apps.roadmap.models import Topic


class TimeDistributionService:

    @staticmethod
    def generate_plan(exam, target_date, study_hours_per_day):

        today = datetime.now().date()
        days_remaining = (target_date - today).days

        if days_remaining < 7:
            raise ValueError("Not enough time to generate roadmap.")

        total_weeks = max(1, days_remaining // 7)

        weekly_hours = round(study_hours_per_day * 7 * 0.85, 2)
        total_hours = round(study_hours_per_day * days_remaining * 0.85, 2)

        coverage_weeks = max(1, int(total_weeks * 0.6))
        practice_weeks = max(1, int(total_weeks * 0.2))
        revision_weeks = max(1, total_weeks - coverage_weeks - practice_weeks)

        subjects = list(
            Topic.objects.filter(
                subject__exam=exam,
                parent__isnull=True
            ).order_by("-weightage")
        )

        if not subjects:
            raise ValueError("No subjects found for exam.")

        coverage_hours = round(total_hours * 0.65, 2)

        total_weight = sum((s.weightage or 0) for s in subjects)
        if total_weight <= 0:
            total_weight = len(subjects)

        work_queue = []

        for subject in subjects:

            subject_ratio = (
                (subject.weightage or 0) / total_weight
                if total_weight else 1 / len(subjects)
            )

            subject_hours = max(1, round(coverage_hours * subject_ratio, 2))

            subtopics = list(subject.child_topics.all())

            if subtopics:

                score_sum = 0
                scored = []

                for sub in subtopics:

                    score = (
                        (sub.weightage or 0) * 0.4 +
                        (sub.pyq_total_marks or 0) * 0.4 +
                        (sub.pyq_count or 0) * 0.2
                    )

                    if score <= 0:
                        score = 1

                    scored.append((sub, score))
                    score_sum += score

                for sub, score in scored:

                    allocated = round(
                        (score / score_sum) * subject_hours, 2
                    )

                    work_queue.append({
                        "topic": sub,
                        "remaining_hours": max(1, allocated)
                    })

            else:

                work_queue.append({
                    "topic": subject,
                    "remaining_hours": max(1, subject_hours)
                })

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

                if current_day > 7:
                    break

        return days