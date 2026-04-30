from django.db.models import Count, Sum
import logging

from apps.roadmap.models import PYQ, Topic

logger = logging.getLogger(__name__)


class WeightageService:
    @staticmethod
    def _get_parent_topics(exam):
        return Topic.objects.filter(subject__exam=exam, parent__isnull=True)

    @staticmethod
    def _get_total_exam_marks(exam):
        return (
            PYQ.objects.filter(exam=exam).aggregate(total=Sum("marks")).get("total") or 0
        )

    @staticmethod
    def _get_agg_map(exam):
        aggregates = (
            PYQ.objects.filter(exam=exam)
            .values("topic")
            .annotate(total_marks=Sum("marks"), total_pyqs=Count("id"))
        )
        return {a["topic"]: a for a in aggregates}

    @staticmethod
    def _get_subtopics_map(exam):
        subtopics = Topic.objects.filter(subject__exam=exam, parent__isnull=False)
        subtopics_map = {}
        for sub in subtopics:
            subtopics_map.setdefault(sub.parent_id, []).append(sub)
        return subtopics_map

    @staticmethod
    def _update_parent_topic(topic, *, total_marks, total_pyqs, total_exam_marks):
        topic.pyq_total_marks = total_marks
        topic.pyq_count = total_pyqs
        topic.weightage = (total_marks / total_exam_marks * 100) if total_exam_marks else 0
        topic.save(update_fields=["pyq_total_marks", "pyq_count", "weightage"])

    @staticmethod
    def _project_children_weightage(parent_topic, children):
        if not children:
            return

        child_weight = parent_topic.weightage / len(children)
        for child in children:
            child.weightage = child_weight

        Topic.objects.bulk_update(children, ["weightage"])

    @staticmethod
    def compute_weightage(exam):
        parent_topics = WeightageService._get_parent_topics(exam)
        total_exam_marks = WeightageService._get_total_exam_marks(exam)

        if total_exam_marks == 0:
            logger.warning("No PYQs found for weightage computation")
            return

        agg_map = WeightageService._get_agg_map(exam)
        subtopics_map = WeightageService._get_subtopics_map(exam)

        for topic in parent_topics:
            data = agg_map.get(topic.id) or {}
            total_marks = data.get("total_marks") or 0
            total_pyqs = data.get("total_pyqs") or 0

            WeightageService._update_parent_topic(
                topic,
                total_marks=total_marks,
                total_pyqs=total_pyqs,
                total_exam_marks=total_exam_marks,
            )

            logger.info(
                "%s -> %s PYQs -> %s%%",
                topic.name,
                topic.pyq_count,
                round(topic.weightage, 2),
            )

            children = subtopics_map.get(topic.id, [])
            WeightageService._project_children_weightage(topic, children)
