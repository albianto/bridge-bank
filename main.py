#!/usr/bin/env python3
import logging
import os
from app import config
from app.web.server import start

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ---------------------------------------------------------------------------
# Monkey-patch actualpy to fix SQLite syntax error with Actual Budget >= 26.3.0
# Bug: apply_change passes Column objects as keys in the ON CONFLICT SET clause,
# which causes SQLAlchemy to emit table-qualified names (e.g. custom_reports.tombstone)
# that are invalid in SQLite's ON CONFLICT DO UPDATE SET.
# Fix: convert Column keys to plain column-name strings for the set_ clause.
# Upstream: https://github.com/bvanelli/actualpy/issues (to be reported)
# ---------------------------------------------------------------------------
def _patch_actualpy():
    try:
        import actual.database as _adb
        from sqlalchemy import Table, Column, insert
        from sqlmodel import Session

        _original = _adb.apply_change

        def _patched_apply_change(
            session: Session,
            table: Table,
            table_id: str,
            values: dict,
        ) -> None:
            set_dict = {
                (col.name if isinstance(col, Column) else col): val
                for col, val in values.items()
            }
            insert_stmt = (
                insert(table)
                .values({"id": table_id, **values})
                .on_conflict_do_update(index_elements=["id"], set_=set_dict)
            )
            session.exec(insert_stmt)

        _adb.apply_change = _patched_apply_change
    except Exception:
        pass  # actualpy not installed or API changed — sync will fail with original error

_patch_actualpy()

if __name__ == "__main__":
    config._load()
    port = int(os.environ.get("INGRESS_PORT", os.environ.get("PORT", "3000")))
    start(host="0.0.0.0", port=port)
