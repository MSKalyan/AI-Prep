from django.db.models import Sum, Count
from apps.roadmap.models import Topic, PYQ


class WeightageService:

    @staticmethod
    def compute_weightage(exam):

        # Parent topics only
        parent_topics = Topic.objects.filter(
            subject__exam=exam,
            parent__isnull=True
        )

        # Total marks across exam
        total_exam_marks = (
            PYQ.objects.filter(exam=exam)
            .aggregate(total=Sum("marks"))
            .get("total") or 0
        )

        if total_exam_marks == 0:
            print("No PYQs found for weightage computation")
            return

        # Aggregate PYQs by topic
        aggregates = (
            PYQ.objects.filter(exam=exam)
            .values("topic")
            .annotate(
                total_marks=Sum("marks"),
                total_pyqs=Count("id")
            )
        )

        # Map: topic_id → aggregate data
        agg_map = {
            a["topic"]: a
            for a in aggregates
        }

        # Preload subtopics (avoids N+1 queries)
        subtopics = Topic.objects.filter(
            subject__exam=exam,
            parent__isnull=False
        )

        subtopics_map = {}
        for sub in subtopics:
            subtopics_map.setdefault(sub.parent_id, []).append(sub)

        # ---- Main Loop ----
        for topic in parent_topics:

            data = agg_map.get(topic.id)

            total_marks = data["total_marks"] if data and data.get("total_marks") else 0
            total_pyqs = data["total_pyqs"] if data and data.get("total_pyqs") else 0

            # Assign parent topic stats
            topic.pyq_total_marks = total_marks
            topic.pyq_count = total_pyqs

            topic.weightage = (
                total_marks / total_exam_marks * 100
            ) if total_exam_marks else 0

            topic.save(update_fields=[
                "pyq_total_marks",
                "pyq_count",
                "weightage"
            ])

            print(
                f"{topic.name} → "
                f"{topic.pyq_count} PYQs → "
                f"{round(topic.weightage, 2)}%"
            )

            # ---- Subtopic Projection ----
            children = subtopics_map.get(topic.id, [])

            if children:
                child_weight = topic.weightage / len(children)

                for child in children:
                    child.weightage = child_weight

                Topic.objects.bulk_update(children, ["weightage"])