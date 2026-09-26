"""HTTP helper with retries + exponential backoff for flaky APIs."""
from __future__ import annotations

import logging
import random
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}


class APIError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


def request_with_retry(
    method: str,
    url: str,
    *,
    max_attempts: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    timeout: float = 180.0,
    session: requests.Session | None = None,
    **kwargs: Any,
) -> requests.Response:
    """Send a request, retrying on network errors and 429/5xx responses.

    Honors a numeric Retry-After header. Raises APIError on a non-retryable
    error or when attempts are exhausted.
    """
    http = session or requests
    last_err: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            resp = http.request(method, url, timeout=timeout, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_err = exc
            log.warning("Network error on %s (attempt %d/%d): %s", _short(url), attempt, max_attempts, exc)
        else:
            if resp.ok:
                return resp
            body = resp.text[:800]
            if resp.status_code not in RETRYABLE_STATUS:
                raise APIError(f"{method} {_short(url)} failed: HTTP {resp.status_code}: {body}",
                               status=resp.status_code, body=body)
            last_err = APIError(f"HTTP {resp.status_code}: {body}", status=resp.status_code, body=body)
            log.warning("HTTP %s from %s (attempt %d/%d)", resp.status_code, _short(url), attempt, max_attempts)
            retry_after = resp.headers.get("Retry-After", "")
            if retry_after.isdigit() and attempt < max_attempts:
                time.sleep(min(float(retry_after), max_delay))
                continue

        if attempt < max_attempts:
            delay = min(max_delay, base_delay * 2 ** (attempt - 1)) * (0.75 + random.random() / 2)
            time.sleep(delay)

    raise APIError(f"{method} {_short(url)} failed after {max_attempts} attempts: {last_err}")


def _short(url: str) -> str:
    """Strip query string (may contain API keys) for logging."""
    return url.split("?", 1)[0]
