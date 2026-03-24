from django.db.models import Sum, Count
from apps.roadmap.models import Topic, PYQ


class WeightageService:

    @staticmethod
    def compute_weightage(exam):

        topics = Topic.objects.filter(
            subject__exam=exam,
            parent__isnull=True
        )

        # total marks across exam
        total_exam_marks = (
            PYQ.objects.filter(exam=exam)
            .aggregate(total=Sum("marks"))["total"] or 0
        )

        if total_exam_marks == 0:
            print("No PYQs found for weightage computation")
            return

        # aggregate PYQs by topic
        aggregates = (
            PYQ.objects.filter(exam=exam)
            .values("topic")
            .annotate(
                total_marks=Sum("marks"),
                total_pyqs=Count("id")
            )
        )

        agg_map = {
            a["topic"]: a
            for a in aggregates
        }

        for topic in topics:

            data = agg_map.get(topic.id)

            topic.pyq_total_marks = data["total_marks"] if data else 0
            topic.pyq_count = data["total_pyqs"] if data else 0

            topic.weightage = (
                topic.pyq_total_marks / total_exam_marks * 100
            ) if total_exam_marks else 0

            topic.save(update_fields=[
                "pyq_total_marks",
                "pyq_count",
                "weightage"
            ])

            print(
                f"{topic.name} → "
                f"{topic.pyq_count} PYQs → "
                f"{round(topic.weightage,2)}%"
            )

        # 1. Calculate for Parent Topics (as you do now)
        parent_topics = Topic.objects.filter(subject__exam=exam, parent__isnull=True)
        # ... (Your existing agg_map logic) ...

        for p in parent_topics:
            data = agg_map.get(p.id)
            p.weightage = (data["total_marks"] / total_exam_marks * 100) if total_exam_marks else 0
            p.save()

            # 2. PROJECTION: Give subtopics a portion of parent weightage 
            # so the TimeDistributor can rank them.
            subtopics = Topic.objects.filter(parent=p)
            if subtopics.exists():
                child_weight = p.weightage / subtopics.count()
                subtopics.update(weightage=child_weight)