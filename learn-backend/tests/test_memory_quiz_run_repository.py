from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai_quiz.domain.quiz_run import (
    QuizRunAlreadyExists,
    QuizRunExpired,
    QuizRunNotFound,
    RunStatus,
)
from ai_quiz.repositories.memory_quiz_runs import MemoryQuizRunRepository, utc_now


@dataclass
class MutableClock:
    current: datetime

    def now(self) -> datetime:
        return self.current

    def advance(self, delta: timedelta) -> None:
        self.current += delta


def test_repository_creates_and_reads_an_isolated_snapshot() -> None:
    clock = MutableClock(datetime(2026, 10, 3, tzinfo=UTC))
    repository = MemoryQuizRunRepository(ttl=timedelta(minutes=60), clock=clock.now)
    payload = {"quiz": {"title": "RAG 基础"}}

    created = repository.create("run_1", payload)
    payload["quiz"]["title"] = "外部修改"
    loaded = repository.get("run_1")

    assert created.status is RunStatus.READY
    assert created.created_at == clock.current
    assert created.expires_at == clock.current + timedelta(minutes=60)
    assert loaded.payload == {"quiz": {"title": "RAG 基础"}}


def test_repository_distinguishes_expired_and_missing_runs() -> None:
    clock = MutableClock(datetime(2026, 10, 3, tzinfo=UTC))
    repository = MemoryQuizRunRepository(ttl=timedelta(minutes=60), clock=clock.now)
    repository.create("run_expired", {"quiz": {}})
    clock.advance(timedelta(minutes=61))

    with pytest.raises(QuizRunExpired, match="run_expired"):
        repository.get("run_expired")

    with pytest.raises(QuizRunNotFound, match="run_expired"):
        repository.get("run_expired")


def test_repository_replaces_payload_without_extending_ttl() -> None:
    clock = MutableClock(datetime(2026, 10, 3, tzinfo=UTC))
    repository = MemoryQuizRunRepository(ttl=timedelta(minutes=60), clock=clock.now)
    original = repository.create("run_1", {"result": None})
    clock.advance(timedelta(minutes=10))

    completed = repository.replace(
        "run_1",
        payload={"result": {"correct": 5}},
        status=RunStatus.COMPLETED,
    )

    assert completed.status is RunStatus.COMPLETED
    assert completed.payload == {"result": {"correct": 5}}
    assert completed.expires_at == original.expires_at


def test_repository_purges_only_expired_runs() -> None:
    clock = MutableClock(datetime(2026, 10, 3, tzinfo=UTC))
    repository = MemoryQuizRunRepository(ttl=timedelta(minutes=60), clock=clock.now)
    repository.create("run_old", {})
    clock.advance(timedelta(minutes=30))
    repository.create("run_new", {})
    clock.advance(timedelta(minutes=31))

    assert repository.purge_expired() == 1
    assert repository.count == 1
    assert repository.get("run_new").run_id == "run_new"


def test_repository_rejects_duplicate_run_ids() -> None:
    clock = MutableClock(datetime(2026, 10, 3, tzinfo=UTC))
    repository = MemoryQuizRunRepository(ttl=timedelta(minutes=60), clock=clock.now)
    repository.create("run_1", {})

    with pytest.raises(QuizRunAlreadyExists, match="run_1") as error:
        repository.create("run_1", {})

    assert error.value.run_id == "run_1"


def test_repository_requires_a_positive_ttl() -> None:
    with pytest.raises(ValueError, match="ttl must be positive"):
        MemoryQuizRunRepository(ttl=timedelta(0))


def test_repository_rejects_a_naive_clock() -> None:
    repository = MemoryQuizRunRepository(
        ttl=timedelta(minutes=60),
        clock=lambda: datetime(2026, 10, 3),
    )

    with pytest.raises(ValueError, match="timezone-aware"):
        repository.create("run_1", {})


def test_default_clock_returns_an_aware_utc_datetime() -> None:
    now = utc_now()

    assert now.tzinfo is UTC
    assert now.utcoffset() == timedelta(0)
