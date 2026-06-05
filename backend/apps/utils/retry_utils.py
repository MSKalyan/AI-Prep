import time
import logging
import requests

logger = logging.getLogger(__name__)


class APIError(Exception):
    pass


class RateLimitError(APIError):
    pass


class ServerError(APIError):
    pass


class ClientError(APIError):
    pass


def retry_request(func, max_retries=3, delay=1):
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            
            status_code = getattr(e, 'status_code', None) or getattr(getattr(e, 'response', None), 'status_code', None)
            if status_code in [400, 401, 403, 404]:
                raise
            
            if not isinstance(e, (requests.exceptions.RequestException, ServerError, RateLimitError, TimeoutError)):
                raise
            
            if status_code == 429 or (status_code and 500 <= status_code < 600):
                if attempt < max_retries:
                    wait_time = delay * (2 ** (attempt - 1))
                    logger.warning(f"Retry {attempt}/{max_retries} after {wait_time}s due to: {e}")
                    time.sleep(wait_time)
                continue
            
            if attempt < max_retries:
                logger.warning(f"Retry {attempt}/{max_retries} due to: {e}")
                time.sleep(delay)
    
    logger.error(f"Request failed after {max_retries} retries: {last_error}")
    raise last_error


def safe_get(url, timeout=5, params=None):
    def make_request():
        response = requests.get(url, params=params, timeout=timeout)
        if response.status_code >= 500:
            raise ServerError(f"Server error: {response.status_code}")
        if response.status_code == 429:
            raise RateLimitError(f"Rate limit: {response.status_code}")
        response.raise_for_status()
        return response
    
    return retry_request(make_request)


def safe_llm_call(client, **kwargs):
    kwargs.setdefault("timeout", 30)
    
    def make_request():
        return client.chat.completions.create(**kwargs)
    
    return retry_request(make_request, max_retries=3, delay=2)


async def async_retry_request(func, max_retries=3, delay=1):
    import asyncio
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_error = e
            
            status_code = getattr(e, 'status_code', None)
            if status_code in [400, 401, 403, 404]:
                raise
            
            if status_code == 429 or (status_code and 500 <= status_code < 600):
                if attempt < max_retries:
                    wait_time = delay * (2 ** (attempt - 1))
                    logger.warning(f"Async Retry {attempt}/{max_retries} after {wait_time}s due to: {e}")
                    await asyncio.sleep(wait_time)
                continue
            
            if attempt < max_retries:
                logger.warning(f"Async Retry {attempt}/{max_retries} due to: {e}")
                await asyncio.sleep(delay)
    
    logger.error(f"Async request failed after {max_retries} retries: {last_error}")
    raise last_error


async def safe_get_async(url, timeout=5, params=None):
    import httpx
    
    async def make_request():
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, params=params)
            if response.status_code >= 500:
                raise ServerError(f"Server error: {response.status_code}")
            if response.status_code == 429:
                raise RateLimitError(f"Rate limit: {response.status_code}")
            response.raise_for_status()
            return response
    
    return await async_retry_request(make_request)


async def safe_llm_call_async(client, **kwargs):
    kwargs.setdefault("timeout", 30)
    
    async def make_request():
        return await client.chat.completions.create(**kwargs)
    
    return await async_retry_request(make_request, max_retries=3, delay=2)


