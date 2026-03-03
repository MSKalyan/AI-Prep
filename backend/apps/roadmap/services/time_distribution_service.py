from datetime import datetime
from math import ceil
from apps.roadmap.models import Topic


class TimeDistributionService:

    @staticmethod
    def generate_plan(exam, target_date, study_hours_per_day):

        today = datetime.now().date()
        days_remaining = (target_date - today).days

        if days_remaining < 7:
            raise ValueError("Not enough time to generate roadmap.")

        total_weeks = days_remaining // 7
        weekly_hours = int(study_hours_per_day * 7 *0.85)
        total_hours = weekly_hours * total_weeks
        print("WEEKLY HOURS:", weekly_hours)
        # Phase split (week-based strict 70/20/10)
        coverage_weeks = max(1, int(total_weeks * 0.7))
        practice_weeks = max(1, int(total_weeks * 0.2))
        revision_weeks = total_weeks - coverage_weeks - practice_weeks

        # Fetch root subjects
        subjects = list(
            Topic.objects.filter(
                exam=exam,
                parent__isnull=True
            ).order_by("-weightage")
        )

        if not subjects:
            raise ValueError("No subjects found for exam.")

        # -----------------------------
        # COVERAGE PHASE (SUBTOPIC LEVEL)
        # -----------------------------
        coverage_hours = total_hours * 0.7

        # Build flat subtopic workload queue
        work_queue = []

        for subject in subjects:

            subject_hours = (subject.weightage / 100) * coverage_hours

            subtopics = list(
                Topic.objects.filter(parent=subject).order_by("order")
            )

            # If no subtopics → treat subject as atomic
            if not subtopics:
                work_queue.append({
                    "topic": subject,
                    "remaining_hours": subject_hours
                })
                continue

            # Distribute subject hours across subtopics equally
            split_hours = subject_hours / len(subtopics)

            for subtopic in subtopics:
                work_queue.append({
                    "topic": subtopic,
                    "remaining_hours": split_hours
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
        # -----------------------------
        # PRACTICE PHASE
        # -----------------------------
        top_subjects = subjects[:5]

        for _ in range(practice_weeks):

            total_weight = sum(s.weightage for s in top_subjects)

            for subject in top_subjects:
                subject_hours = (subject.weightage / total_weight) * weekly_hours
            week_items = [
                {
                    "topic": subject,
                    "hours": round(subject_hours, 2)
                }
                for subject in top_subjects
            ]

            plan.append({
                "week_number": week_number,
                "phase": "practice",
                "items": week_items
            })

            week_number += 1

        # -----------------------------
        # REVISION PHASE
        # -----------------------------
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