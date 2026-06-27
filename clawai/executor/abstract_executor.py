from __future__ import annotations

from abc import ABC, abstractmethod

from .execution_request import ExecutionRequest
from .execution_result import ExecutionResult


class AbstractExecutor(ABC):
    @abstractmethod
    def run(self, request: ExecutionRequest) -> ExecutionResult: ...
