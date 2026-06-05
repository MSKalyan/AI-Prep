import json
import logging

logger = logging.getLogger(__name__)


def normalize_options(raw_options):
    if raw_options is None:
        return {}

    if isinstance(raw_options, dict):
        return raw_options

    if isinstance(raw_options, str):
        try:
            parsed = json.loads(raw_options)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                raw_options = parsed
        except (TypeError, ValueError):
            logger.warning("Failed to parse question options payload", exc_info=True)
            return {}

    if isinstance(raw_options, list):
        option_keys = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        normalized = {}
        for idx, value in enumerate(raw_options):
            if idx >= len(option_keys):
                break
            normalized[option_keys[idx]] = str(value)
        return normalized

    return {}


def format_options(q):
    options_dict = normalize_options(q.options)
    return [{"key": k, "text": v} for k, v in options_dict.items()]


def get_selected_answer(attempt, q):
    ans = attempt.answers.filter(question=q).first()
    return ans.user_answer if ans else None


def explain_question(question_id):
    from groq import Groq
    from apps.mocktest.models import Question
    from apps.utils.retry_utils import safe_llm_call
    from django.conf import settings

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return None, "Question not found", None

    client = Groq(api_key=settings.GROQ_API_KEY)
    prompt = f"""Explain this MCQ...

    Question: {question.question_text}
    Options: {question.options}
    Correct Answer: {question.correct_answer}
    """

    try:
        response = safe_llm_call(
            client,
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        explanation = "\n".join([line for line in text.split("\n") if line.strip()])
        return explanation, None, None
    except Exception as e:
        return None, str(e), None