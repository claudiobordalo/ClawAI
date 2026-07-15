"""
EVO-18: Ciclo de Auto-Verificação Proativa

Este módulo implementa um monitor que verifica a saúde do sistema
em intervalos regulares, garantindo a estabilidade da ClawAI.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent

logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    timestamp: float
    tests_passed: bool
    api_health: bool
    memory_integrity: bool
    errors: list[str]

class ProactiveMonitor:
    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("ProactiveMonitor started")

    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ProactiveMonitor stopped")

    async def _monitor_loop(self):
        while self._running:
            try:
                status = await self._run_checks()
                self._process_status(status)
            except Exception as e:
                logger.error(f"ProactiveMonitor error: {e}")
            await asyncio.sleep(self.interval)

    async def _run_checks(self) -> HealthStatus:
        errors = []
        tests_passed = await self._check_tests()
        api_health = await self._check_api()
        memory_integrity = await self._check_memory()

        if not tests_passed: errors.append("Tests failed")
        if not api_health: errors.append("API health check failed")
        if not memory_integrity: errors.append("Memory integrity check failed")

        return HealthStatus(
            timestamp=time.time(),
            tests_passed=tests_passed,
            api_health=api_health,
            memory_integrity=memory_integrity,
            errors=errors
        )

    async def _check_tests(self) -> bool:
        try:
            import subprocess
            result = subprocess.run(
                ["python", "-m", "pytest", "-q", "--tb=no"],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Test check failed: {e}")
            return False

    async def _check_api(self) -> bool:
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"API check failed: {e}")
            return False

    async def _check_memory(self) -> bool:
        try:
            memory_file = ROOT / ".clawai" / "memory" / "vector_store.json"
            if not memory_file.exists():
                return True # No file yet is okay
            content = memory_file.read_text()
            # Basic integrity check
            return len(content) > 0 and content.strip().startswith("{")
        except Exception as e:
            logger.warning(f"Memory check failed: {e}")
            return False

    def _process_status(self, status: HealthStatus):
        if status.errors:
            logger.warning(f"Proactive checks detected issues: {status.errors}")
        else:
            logger.info(f"Proactive checks passed: {status.timestamp}")
