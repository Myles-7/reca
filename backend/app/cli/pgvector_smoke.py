"""Verify that the configured PostgreSQL server supports pgvector.

This probe is intentionally independent of PowerShell quoting and performs no
schema changes or writes to business tables.
"""

from __future__ import annotations

import sys

from sqlalchemy import text

from app.core.db import engine


def main() -> int:
    try:
        with engine.connect() as connection:
            extension = connection.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            ).scalar_one_or_none()
            if extension != "vector":
                print("pgvector extension is unavailable", file=sys.stderr)  # noqa: T201
                return 1
            value = connection.execute(
                text("SELECT '[1,2,3]'::vector <-> '[1,2,3]'::vector")
            ).scalar_one()
            if value != 0:
                print(  # noqa: T201
                    "pgvector distance operation returned an unexpected value",
                    file=sys.stderr,
                )
                return 1
    except Exception as error:
        print(f"pgvector probe failed: {type(error).__name__}", file=sys.stderr)  # noqa: T201
        return 1
    print("pgvector smoke passed")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
