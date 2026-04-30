import logging
from typing import Any

import requests
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

DEFAULT_LLM_TIMEOUT_SECONDS = 10
DEFAULT_GET_TIMEOUT_SECONDS = 5


class RetryableExternalAPIError(Exception):
    """Raised when an external API error is retryable (429/5xx)."""


def _extract_status_code(exc: BaseException) -> int | None:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status

    response = getattr(exc, "response", None)
    response_status = getattr(response, "status_code", None)
    if isinstance(response_status, int):
        return response_status

    return None


def _is_retryable_status(status_code: int | None) -> bool:
    if status_code is None:
        return False
    if status_code == 429:
        return True
    return 500 <= status_code < 600


def _is_non_retryable_status(status_code: int | None) -> bool:
    return status_code in {400, 401, 403}


def _before_sleep_log(retry_state: RetryCallState) -> None:
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "Retrying external API call (attempt %s/%s) due to: %s",
        retry_state.attempt_number,
        3,
        exception,
    )


def _log_final_failure(retry_state: RetryCallState) -> Any:
    exception = retry_state.outcome.exception() if retry_state.outcome else None
    logger.error("External API call failed after retries: %s", exception, exc_info=True)
    if exception is not None:
        raise exception
    raise RuntimeError("External API call failed after retries")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError, RetryableExternalAPIError)),
    before_sleep=_before_sleep_log,
    retry_error_callback=_log_final_failure,
    reraise=True,
)
def safe_get(url: str, **kwargs):
    kwargs.setdefault("timeout", DEFAULT_GET_TIMEOUT_SECONDS)

    response = requests.get(url, **kwargs)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        status_code = _extract_status_code(exc)
        if _is_non_retryable_status(status_code):
            raise
        if _is_retryable_status(status_code):
            raise RetryableExternalAPIError(str(exc)) from exc
        raise

    return response


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((requests.exceptions.RequestException, TimeoutError, RetryableExternalAPIError)),
    before_sleep=_before_sleep_log,
    retry_error_callback=_log_final_failure,
    reraise=True,
)
def safe_llm_call(client, **kwargs):
    kwargs.setdefault("timeout", DEFAULT_LLM_TIMEOUT_SECONDS)
    try:
        return client.chat.completions.create(**kwargs)
    except Exception as exc:
        status_code = _extract_status_code(exc)
        if _is_non_retryable_status(status_code):
            raise
        if _is_retryable_status(status_code):
            raise RetryableExternalAPIError(str(exc)) from exc
        if isinstance(exc, (requests.exceptions.RequestException, TimeoutError)):
            raise
        raise
