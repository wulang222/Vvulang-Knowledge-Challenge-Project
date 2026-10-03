"""Thread-safe, process-local storage for the anonymous MVP."""

from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import RLock
from typing import Any

from ai_quiz.domain.quiz_run import (
    QuizRunAlreadyExists,
    QuizRunExpired,
    QuizRunNotFound,
    QuizRunSnapshot,
    RunStatus,
)

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


class MemoryQuizRunRepository:
    """Store defensive snapshots and expire them without external infrastructure."""

    def __init__(self, *, ttl: timedelta, clock: Clock = utc_now) -> None:
        if ttl <= timedelta(0):
            raise ValueError("ttl must be positive")
        self._ttl = ttl
        self._clock = clock
        self._records: dict[str, QuizRunSnapshot] = {}
        self._lock = RLock()

    def create(
        self,
        run_id: str,
        payload: dict[str, Any],
        *,
        status: RunStatus = RunStatus.READY,
    ) -> QuizRunSnapshot:
        now = self._aware_now()
        with self._lock:
            if run_id in self._records:
                raise QuizRunAlreadyExists(run_id)
            snapshot = QuizRunSnapshot(
                run_id=run_id,
                status=status,
                payload=deepcopy(payload),
                created_at=now,
                expires_at=now + self._ttl,
            )
            self._records[run_id] = snapshot
            return self._copy(snapshot)

    def get(self, run_id: str) -> QuizRunSnapshot:
        now = self._aware_now()
        with self._lock:
            snapshot = self._records.get(run_id)
            if snapshot is None:
                raise QuizRunNotFound(run_id)
            if snapshot.expires_at <= now:
                del self._records[run_id]
                raise QuizRunExpired(run_id)
            return self._copy(snapshot)

    def replace(
        self,
        run_id: str,
        *,
        payload: dict[str, Any],
        status: RunStatus,
    ) -> QuizRunSnapshot:
        current = self.get(run_id)
        replacement = QuizRunSnapshot(
            run_id=current.run_id,
            status=status,
            payload=deepcopy(payload),
            created_at=current.created_at,
            expires_at=current.expires_at,
        )
        with self._lock:
            self._records[run_id] = replacement
        return self._copy(replacement)

    def purge_expired(self) -> int:
        now = self._aware_now()
        with self._lock:
            expired_ids = [
                run_id for run_id, snapshot in self._records.items() if snapshot.expires_at <= now
            ]
            for run_id in expired_ids:
                del self._records[run_id]
            return len(expired_ids)

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def _aware_now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        return now

    @staticmethod
    def _copy(snapshot: QuizRunSnapshot) -> QuizRunSnapshot:
        return QuizRunSnapshot(
            run_id=snapshot.run_id,
            status=snapshot.status,
            payload=deepcopy(snapshot.payload),
            created_at=snapshot.created_at,
            expires_at=snapshot.expires_at,
        )
