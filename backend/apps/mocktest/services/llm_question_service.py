import json
import logging
import re

from groq import Groq
from django.conf import settings

from ..models import Question

logger = logging.getLogger(__name__)

_TOPIC_STOPWORDS = {
    "and", "the", "for", "with", "from", "into", "using", "use", "based",
    "introduction", "basics", "advanced", "concepts", "theory", "problems"
}
_OPTION_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class LLMQuestionService:
    @staticmethod
    def generate_with_retry(topics, count, max_retries=2):
        if not topics or count <= 0:
            return []

        for _ in range(max_retries):
            try:
                questions = LLMQuestionService._generate(topics, count)
            except (TimeoutError, ValueError, TypeError, AttributeError):
                logger.error("Retry attempt for LLM question generation failed", exc_info=True)
                continue
            if questions:
                return questions
        return []

    @staticmethod
    def _generate(topics, count):
        from apps.utils.retry_utils import safe_llm_call

        client = Groq(api_key=settings.GROQ_API_KEY)
        main_topic = topics[0] if topics else None
        topic_name = main_topic.name if main_topic else "maths"
        topic_names = [t.name for t in topics[:3]] if topics else [topic_name]

        prompt = LLMQuestionService._build_prompt(topic_name, count, topic_names)
        content = LLMQuestionService._call_api(client, prompt)
        return LLMQuestionService._process_response(content, topics)

    @staticmethod
    def _build_prompt(topic_name, count, topic_names=None):
        constrained_topics = topic_names or [topic_name]
        if len(constrained_topics) > 3:
            constrained_topics = constrained_topics[:3]
        topic_block = ", ".join(constrained_topics)
        return f"Generate {count} GATE MCQ on {topic_block}. Return JSON array with: question, options (A,B,C,D), correct_answer, explanation. No markdown."

    @staticmethod
    def _call_api(client, prompt):
        try:
            from apps.utils.retry_utils import safe_llm_call
            response = safe_llm_call(
                client,
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
                timeout=30,
            )
            content = response.choices[0].message.content if hasattr(response, 'choices') and response.choices else ""
            logger.debug("[LLM] Response length: %s", len(content) if content else 0)
            return content if content else ""
        except (TimeoutError, ValueError, TypeError, AttributeError):
            logger.error("LLM question generation failed", exc_info=True)
            raise

    @staticmethod
    def _process_response(content, topics):
        if not content:
            return []

        content = content.strip()
        content = LLMQuestionService._clean_markdown(content)
        start = content.find('[')
        if start == -1:
            return []

        content = LLMQuestionService._extract_json_array(content, start)
        questions_data = LLMQuestionService._parse_json(content)
        if not questions_data:
            return []

        return LLMQuestionService._create_questions(questions_data, topics)

    @staticmethod
    def _clean_markdown(content):
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        if content.startswith('```'):
            content = re.sub(r'^```\w*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        return content.strip()

    @staticmethod
    def _extract_json_array(content, start):
        depth = 0
        for i, c in enumerate(content[start:], start):
            if c == '[':
                depth += 1
            elif c == ']':
                depth -= 1
                if depth == 0:
                    return content[start:i+1]
        return content[start:]

    @staticmethod
    def _parse_json(content):
        content = content.replace('}{', '},{').replace('\n', '').replace('  ', '')
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = LLMQuestionService._extract_objects(content)

        if not isinstance(data, list):
            return []
        logger.debug("[LLM] Parsed %s questions", len(data))
        return data

    @staticmethod
    def _extract_objects(content):
        questions_list = []
        pattern = r'\{(?:[^{}]|\{[^{}]*\})*\}'
        for match in re.finditer(pattern, content):
            try:
                obj = json.loads(match.group())
                if "question" in obj and "options" in obj:
                    questions_list.append(obj)
            except (json.JSONDecodeError, OSError):
                continue
        if not questions_list:
            logger.warning("[LLM] No valid question objects found via regex")
        return questions_list

    @staticmethod
    def _create_questions(questions_data, topics):
        from .question_utils import QuestionUtils

        created_questions = []
        for idx, q_data in enumerate(questions_data):
            question = LLMQuestionService._create_single(q_data, topics, idx, len(questions_data))
            if question:
                created_questions.append(question)
        return created_questions

    @staticmethod
    def _create_single(q_data, topics, idx, total):
        from .question_utils import QuestionUtils

        try:
            opts = QuestionUtils.normalize_options(q_data.get("options", {}))
            if not opts or len(opts) < 2:
                logger.warning("Skipping generated question - insufficient options: %s", opts)
                return None

            correct_answer = QuestionUtils.extract_correct_answer(
                q_data.get("correct_answer", "") or q_data.get("answer", ""),
                opts,
            )
            if not correct_answer:
                logger.warning("Skipping generated question - invalid correct_answer: %s", q_data.get("correct_answer", ""))
                return None

            topic_keywords = LLMQuestionService._get_keywords(topics)
            if not LLMQuestionService._is_relevant(q_data.get("question", ""), topic_keywords):
                logger.warning("Skipping generated question - not relevant to selected topic keywords")
                return None

            logger.debug("[LLM] Creating question %s/%s: %s...", idx + 1, total, q_data.get("question", "")[:50])

            return Question.objects.create(
                topic=topics[0] if topics else None,
                question_text=q_data.get("question", ""),
                question_type="mcq",
                options=opts,
                correct_answer=correct_answer,
                explanation=q_data.get("explanation", ""),
                difficulty="medium",
                marks=1,
                negative_marks=0.0,
                source="llm",
            )
        except (TypeError, ValueError, KeyError):
            logger.warning("Skipping invalid generated question payload", exc_info=True)
            return None

    @staticmethod
    def _get_keywords(topics):
        keywords = set()
        for t in topics or []:
            if not t or not t.name:
                continue
            words = re.findall(r"[a-z0-9]+", t.name.lower())
            for w in words:
                if len(w) >= 4 and w not in _TOPIC_STOPWORDS:
                    keywords.add(w)
        return keywords

    @staticmethod
    def _is_relevant(text, keywords):
        if not text:
            return False
        if not keywords:
            return True
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        if not words:
            return False
        overlap = len(words.intersection(set(keywords)))
        return overlap >= 1