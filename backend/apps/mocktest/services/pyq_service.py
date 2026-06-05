import logging
from django.db.models import Q

from ..models import Question
from apps.roadmap.models import PYQ

logger = logging.getLogger(__name__)

_TOPIC_STOPWORDS = {
    "and", "the", "for", "with", "from", "into", "using", "use", "based",
    "introduction", "basics", "advanced", "concepts", "theory", "problems"
}


class PYQService:
    @staticmethod
    def get_pyq_questions(topics, count):
        if not topics:
            logger.warning("[PYQ] No topics provided")
            return []

        logger.debug("[PYQ] Searching for PYQs in %s topics", len(topics))

        subject_ids, topic_keywords = PYQService._extract_keywords(topics)
        all_pyqs = PYQService._search_by_topic(topics, count)

        if len(all_pyqs) < count:
            all_pyqs = PYQService._search_by_subject_keyword(subject_ids, topic_keywords, count, all_pyqs)

        if len(all_pyqs) < count:
            all_pyqs = PYQService._search_by_subject_fallback(subject_ids, topic_keywords, count, all_pyqs)

        return PYQService._convert_to_questions(all_pyqs[:count])

    @staticmethod
    def _extract_keywords(topics):
        subject_ids = set()
        topic_keywords = set()
        for t in topics:
            if t.subject:
                subject_ids.add(t.subject.id)
            if t.name:
                keywords = t.name.lower().replace("-", " ").replace("_", " ").split()
                topic_keywords.update([k for k in keywords if len(k) > 3])
        logger.debug("[PYQ] Topic keywords: %s", list(topic_keywords)[:10])
        logger.debug("[PYQ] Subject IDs: %s", subject_ids)
        return subject_ids, topic_keywords

    @staticmethod
    def _search_by_topic(topics, count):
        topic_ids = [t.id for t in topics if t.id]
        if not topic_ids:
            return []
        pyqs = list(PYQ.objects.filter(topic_id__in=topic_ids, options__isnull=False).order_by("?")[:count * 2])
        logger.debug("[PYQ] Topic-exact match: %s PYQs", len(pyqs))
        return list(pyqs)

    @staticmethod
    def _search_by_subject_keyword(subject_ids, topic_keywords, count, existing_pyqs):
        if not subject_ids or not topic_keywords:
            return existing_pyqs

        keyword_query = Q()
        for kw in list(topic_keywords)[:10]:
            keyword_query |= Q(question_text__icontains=kw) | Q(topic__name__icontains=kw)

        pyqs = list(
            PYQ.objects.filter(keyword_query, topic__subject_id__in=subject_ids, options__isnull=False)
            .exclude(id__in=[p.id for p in existing_pyqs])
            .order_by("?")[:count]
        )
        filtered = [p for p in pyqs if PYQService._is_relevant(p.question_text, topic_keywords)]
        logger.debug("[PYQ] Subject+keyword match: %s PYQs (filtered %s)", len(pyqs), len(filtered))
        existing_pyqs.extend(filtered)
        return existing_pyqs

    @staticmethod
    def _search_by_subject_fallback(subject_ids, topic_keywords, count, existing_pyqs):
        if not subject_ids:
            return existing_pyqs
        pyqs = list(
            PYQ.objects.filter(topic__subject_id__in=subject_ids, options__isnull=False)
            .exclude(id__in=[p.id for p in existing_pyqs])
            .order_by("?")[:count]
        )
        filtered = [p for p in pyqs if PYQService._is_relevant(p.question_text, topic_keywords)]
        logger.debug("[PYQ] Subject fallback: %s PYQs (filtered %s)", len(pyqs), len(filtered))
        existing_pyqs.extend(filtered)
        return existing_pyqs

    @staticmethod
    def _is_relevant(text, keywords):
        import re
        if not text:
            return False
        if not keywords:
            return True
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        if not words:
            return False
        overlap = len(words.intersection(set(keywords)))
        return overlap >= 1

    @staticmethod
    def _convert_to_questions(pyqs):
        from .question_utils import QuestionUtils

        questions = []
        for pyq in pyqs:
            options = QuestionUtils.normalize_options(pyq.options)
            if not options or len(options) < 2:
                logger.warning("[PYQ] Skipping PYQ %s - insufficient options: %s", pyq.id, options)
                continue
            correct_answer = QuestionUtils.extract_correct_answer(pyq.correct_answer, options)
            if not correct_answer:
                logger.warning("[PYQ] Skipping PYQ %s - invalid correct_answer: %s", pyq.id, pyq.correct_answer)
                continue
            question = Question.objects.create(
                topic=pyq.topic,
                exam=pyq.exam,
                question_text=pyq.question_text,
                question_type=pyq.question_type or "mcq",
                options=options,
                correct_answer=correct_answer,
                explanation=pyq.explanation or "",
                difficulty="medium",
                marks=int(pyq.marks) if pyq.marks else 1,
                negative_marks=0.0,
                source="pyq",
                year=pyq.year,
            )
            questions.append(question)
        logger.info("[PYQ] Converted: %s questions", len(questions))
        return questions