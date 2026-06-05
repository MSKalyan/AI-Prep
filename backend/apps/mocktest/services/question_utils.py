import json
import re

_OPTION_KEYS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class QuestionUtils:
    @staticmethod
    def normalize_options(raw_options):
        payload = QuestionUtils._deserialize_options_payload(raw_options)
        if isinstance(payload, dict):
            return QuestionUtils._normalize_option_dict(payload)
        if isinstance(payload, list):
            return QuestionUtils._normalize_option_list(payload)
        return {}

    @staticmethod
    def _deserialize_options_payload(raw_options):
        if raw_options is None:
            return None
        if not isinstance(raw_options, str):
            return raw_options
        try:
            return json.loads(raw_options)
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _normalize_option_dict(raw_options):
        normalized = {}
        for key, value in raw_options.items():
            key_str = str(key).strip().upper()
            if key_str:
                normalized[key_str] = str(value).strip()
        return normalized

    @staticmethod
    def _normalize_option_list(raw_options):
        normalized = {}
        for idx, value in enumerate(raw_options[:len(_OPTION_KEYS)]):
            normalized[_OPTION_KEYS[idx]] = str(value).strip()
        return normalized

    @staticmethod
    def extract_correct_answer(correct, options=None):
        options_map = QuestionUtils.normalize_options(options)
        option_keys = set(options_map.keys())
        for candidate in QuestionUtils._collect_answer_candidates(correct):
            raw = str(candidate).strip()
            if not raw:
                continue
            cleaned = QuestionUtils._extract_option_letter(raw)
            if len(cleaned) == 1 and (not option_keys or cleaned in option_keys):
                return cleaned
            matched_key = QuestionUtils._find_option_key_by_value(raw, options_map)
            if matched_key:
                return matched_key
        return ""

    @staticmethod
    def _collect_answer_candidates(correct):
        if isinstance(correct, list):
            return [c for c in correct if c is not None]
        if isinstance(correct, dict):
            values = [c for c in correct.values() if c is not None]
            keys = [c for c in correct.keys() if c is not None]
            return values + keys
        return [correct] if correct is not None else []

    @staticmethod
    def _extract_option_letter(raw_value):
        cleaned = re.sub(r"^[\(\[\{]?\s*([A-Za-z])[\)\]\}\.\:\-]?\s*$", r"\1", raw_value)
        return cleaned.strip().upper()

    @staticmethod
    def _find_option_key_by_value(raw_value, options_map):
        lowered = raw_value.lower().strip()
        for key, value in options_map.items():
            if lowered == str(value).lower().strip():
                return key
        return ""

    @staticmethod
    def normalize_text_answer(raw_value):
        return str(raw_value).upper().strip() if raw_value else ""

    @staticmethod
    def resolve_answer_values(question, raw_user_answer):
        options = QuestionUtils.normalize_options(question.options)
        normalized_user_answer = QuestionUtils.extract_correct_answer(raw_user_answer, options) or QuestionUtils.normalize_text_answer(raw_user_answer)
        normalized_correct_answer = QuestionUtils.extract_correct_answer(question.correct_answer, options) or QuestionUtils.normalize_text_answer(question.correct_answer)
        is_correct = bool(normalized_user_answer) and (normalized_user_answer == normalized_correct_answer)
        return normalized_user_answer, normalized_correct_answer, is_correct