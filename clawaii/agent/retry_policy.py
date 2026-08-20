from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Type


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    retryable_errors: Tuple[Type[Exception], ...] = (Exception,)
    timeout: Optional[float] = None

    def compute_delay(self, attempt: int) -> float:
        delay = self.base_delay * (self.backoff_factor**attempt)
        return min(delay, self.max_delay)

    def is_retryable(self, error: Exception) -> bool:
        return isinstance(error, self.retryable_errors)

    def execute(
        self,
        fn: Callable[[], object],
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ) -> object:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn()
            except Exception as e:
                last_error = e
                if not self.is_retryable(e):
                    raise
                if attempt >= self.max_retries:
                    raise
                if on_retry:
                    on_retry(attempt + 1, e)
                delay = self.compute_delay(attempt)
                time.sleep(delay)
        if last_error is None:
            raise RuntimeError("unreachable")
        raise last_error  # pragma: no cover
