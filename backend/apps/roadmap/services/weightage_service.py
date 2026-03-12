from django.db.models import Sum, Count
from apps.roadmap.models import Topic


class WeightageService:

    @staticmethod
    def compute_weightage(exam):
        """
        Computes subject-level weightage for an exam.

        Updates:
        - pyq_total_marks
        - pyq_count
        - weightage (%)
        """

        # Only compute weightage for main subjects
        topics = Topic.objects.filter(
            exam=exam,
            parent=None
        )

        # Total marks of the entire exam dataset
        total_exam_marks = topics.aggregate(
            total=Sum("pyqs__marks")
        )["total"] or 0

        for topic in topics:

            aggregates = topic.pyqs.aggregate(
                total_marks=Sum("marks"),
                total_pyqs=Count("id")
            )

            topic.pyq_total_marks = aggregates["total_marks"] or 0
            topic.pyq_count = aggregates["total_pyqs"] or 0

            if total_exam_marks > 0:
                topic.weightage = (
                    topic.pyq_total_marks / total_exam_marks
                ) * 100
            else:
                topic.weightage = 0

            topic.save(update_fields=[
                "pyq_total_marks",
                "pyq_count",
                "weightage"
            ])