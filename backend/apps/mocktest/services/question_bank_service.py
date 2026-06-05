import logging

from ..models import Question

logger = logging.getLogger(__name__)


class QuestionBankService:
    @staticmethod
    def get_questions(topics, count, exclude_ids=None):
        from .question_utils import QuestionUtils

        topic_ids = [t.id for t in topics if t and t.id]
        if not topic_ids or count <= 0:
            return []

        queryset = Question.objects.filter(topic_id__in=topic_ids)
        if exclude_ids:
            queryset = queryset.exclude(id__in=exclude_ids)

        usable = []
        for q in queryset.order_by("?"):
            options = QuestionUtils.normalize_options(q.options)
            correct = QuestionUtils.extract_correct_answer(q.correct_answer, options)
            if len(options) < 2 or not correct:
                continue
            if correct != q.correct_answer:
                q.correct_answer = correct
                q.options = options
                q.save(update_fields=["correct_answer", "options"])
            usable.append(q)
            if len(usable) >= count:
                break

        return usable