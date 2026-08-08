# Fix: 500 ServerSelectionTimeoutError when MongoDB is unavailable

## Root Cause
MongoDB is not running at `localhost:27017`. In-memory endpoints work, but any
endpoint hitting MongoDB (`/api/agents/{agent}/history`, `/api/simulation/start`,
`/api/simulation/runs/{id}/log`) crashes with `pymongo.errors.ServerSelectionTimeoutError`.

## Plan (approved)
Add an in-memory database fallback in `backend/app/database/mongodb.py` that mirrors the
Motor async interface used by the routes. When MongoDB is unreachable, `get_database()`
returns the in-memory store so all existing routes work unchanged.

## Steps
- [x] Analyze the codebase and identify root cause
- [x] Confirm plan with user
- [x] Add `InMemoryCursor` / `InMemoryCollection` / `InMemoryDatabase` classes
- [x] Modify `connect_to_mongo()` to detect MongoDB availability and fall back
- [x] Update `close_mongo_connection()` and `get_database()` for the fallback
- [x] Run backend test suite (pytest) to verify no regressions
- [x] Verify fallback path (start app without MongoDB)

