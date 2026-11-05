import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite://")

from src.configs.db import Base
from src.models.model import Url
from src.utils.url import ShortUrlConflictError, create_short_url


@pytest.fixture(scope="module")
def postgres_session_factory():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL concurrency tests")

    engine = create_engine(database_url, pool_size=5, max_overflow=5)
    if engine.dialect.name != "postgresql":
        engine.dispose()
        pytest.fail("TEST_DATABASE_URL must point to a PostgreSQL test database")

    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False), engine
    engine.dispose()


def synchronize_initial_checks(engine, synchronize_alias_check=False):
    barriers = {"long_url": Barrier(2)}
    if synchronize_alias_check:
        barriers["short_code"] = Barrier(2)

    counts = {key: 0 for key in barriers}
    lock = Lock()

    def listener(conn, cursor, statement, parameters, context, executemany):
        sql = statement.lower()
        if not sql.lstrip().startswith("select") or "from urls" not in sql:
            return

        for column, barrier in barriers.items():
            if f"urls.{column}" not in sql:
                continue

            with lock:
                should_wait = counts[column] < 2
                if should_wait:
                    counts[column] += 1

            if should_wait:
                barrier.wait(timeout=10)
            return

    event.listen(engine, "after_cursor_execute", listener)
    return listener


def run_concurrently(session_factory, long_url, custom_alias=None):
    with session_factory() as db:
        try:
            return create_short_url(
                db=db,
                long_url=long_url,
                base_url="https://short.example/",
                custom_alias=custom_alias,
            )
        except Exception as exc:
            return exc


def test_concurrent_requests_for_same_url_return_same_short_url(
    postgres_session_factory,
):
    session_factory, engine = postgres_session_factory
    long_url = f"https://{uuid4().hex}.example.test/resource"
    listener = synchronize_initial_checks(engine)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(run_concurrently, session_factory, long_url)
                for _ in range(2)
            ]
            results = [future.result(timeout=20) for future in futures]
    finally:
        event.remove(engine, "after_cursor_execute", listener)

    try:
        assert all(isinstance(result, dict) for result in results)
        assert results[0]["short_code"] == results[1]["short_code"]

        with session_factory() as db:
            assert db.query(Url).filter(Url.long_url == long_url).count() == 1
    finally:
        with session_factory() as db:
            db.query(Url).filter(Url.long_url == long_url).delete(
                synchronize_session=False
            )
            db.commit()


def test_concurrent_requests_for_same_alias_return_one_conflict(
    postgres_session_factory,
):
    session_factory, engine = postgres_session_factory
    alias = f"race-{uuid4().hex}"
    long_urls = [
        f"https://{uuid4().hex}.example.test/resource",
        f"https://{uuid4().hex}.example.test/resource",
    ]
    listener = synchronize_initial_checks(engine, synchronize_alias_check=True)

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    run_concurrently,
                    session_factory,
                    long_url,
                    alias,
                )
                for long_url in long_urls
            ]
            results = [future.result(timeout=20) for future in futures]
    finally:
        event.remove(engine, "after_cursor_execute", listener)

    try:
        successes = [result for result in results if isinstance(result, dict)]
        conflicts = [
            result for result in results
            if isinstance(result, ShortUrlConflictError)
        ]

        assert len(successes) == 1
        assert len(conflicts) == 1

        with session_factory() as db:
            assert db.query(Url).filter(Url.short_code == alias).count() == 1
    finally:
        with session_factory() as db:
            db.query(Url).filter(Url.long_url.in_(long_urls)).delete(
                synchronize_session=False
            )
            db.commit()
