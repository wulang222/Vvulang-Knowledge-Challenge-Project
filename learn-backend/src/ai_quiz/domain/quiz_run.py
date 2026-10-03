"""Minimal quiz-run state used by the in-memory MVP repository."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    READY = "READY"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True, slots=True)
class QuizRunSnapshot:
    run_id: str
    status: RunStatus
    payload: dict[str, Any]
    created_at: datetime
    expires_at: datetime


class QuizRunNotFound(LookupError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Quiz run not found: {run_id}")
        self.run_id = run_id


class QuizRunExpired(LookupError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Quiz run expired: {run_id}")
        self.run_id = run_id


class QuizRunAlreadyExists(ValueError):
    def __init__(self, run_id: str) -> None:
        super().__init__(f"Quiz run already exists: {run_id}")
        self.run_id = run_id
