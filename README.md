# Day 16 Practice Project — Persist the Library Lending API

Not a new app. Take your Day 11 project and convert its storage layer from in-memory
dicts/lists to real SQLAlchemy models backed by SQLite, using everything from Days 12–15.
No new theory today — this is where it all gets applied at once.

DB choice: **SQLite** (`sqlite:///library.db`). Nothing below is SQLite-specific — if you
want Postgres instead, the only thing that changes is the connection string in `database.py`.

---

## What stays the same

- All endpoints, paths, query params, and response shapes from Day 11. If you did the
  Day 11 spec's "don't write code that makes swapping storage backends obviously impossible"
  correctly, your **routers barely change at all**. That's the actual test of whether
  your Day 11 layering held up — a router that imports a service function and calls it
  shouldn't care whether that function hits a dict or a database.
- Your custom exception hierarchy (`LibraryError` and subclasses) and the single global
  exception handler — unchanged.
- Business rules: copies-available check, loan limits (3 basic / 10 premium), loan periods
  (14 / 30 days), ISBN validation, uniqueness on email/ISBN. Same rules — now enforced
  against a real table instead of a dict.

## What changes

- **`services/`** — every dict/list operation becomes a real `Session` query: `select()`,
  `.scalars()`, `.execute()`, `commit()` (Day 13). Services now take a `db: Session` param
  instead of touching a module-level dict.
- **`dependencies.py`** — add a real `get_db` yield dependency. You already built a toy
  version of this exact shape in Day 11 (`get_store`, opening/closing request scope) —
  replace it with the real thing rather than keeping both.
- **`schemas/`** — mostly unchanged, but every response schema needs
  `model_config = ConfigDict(from_attributes=True)` now, so Pydantic can read straight off
  SQLAlchemy ORM objects instead of dicts (Day 6 config, this is what it was for).
- **`models/`** (new) — SQLAlchemy declarative models. This directory holds SQLAlchemy
  classes, not Pydantic ones — same `models/` vs `schemas/` split from Day 9, now finally
  populated on the `models/` side.

---

## Required project structure

```
library_api/
├── main.py
├── database.py              # NEW — engine, SessionLocal, get_db
├── alembic.ini               # NEW
├── alembic/                  # NEW
├── core/
│   └── exceptions.py
├── models/                   # NEW — SQLAlchemy classes
│   ├── book.py
│   ├── member.py
│   ├── loan.py
│   └── publisher.py
├── routers/
│   ├── books.py
│   ├── members.py
│   └── loans.py
├── schemas/
│   ├── book.py
│   ├── member.py
│   └── loan.py
├── services/
│   ├── book_service.py
│   ├── member_service.py
│   └── loan_service.py
├── dependencies.py
└── middleware.py
```

---

## Required relationships (Day 14)

Three genuine relationships, not one — this is the main new rep beyond Day 11:

1. **`Publisher` → `Book`, one-to-many.** In Day 11, `Publisher` was a nested Pydantic
   model on `BookCreate` only — data went in, nothing was done with it. Promote it to a
   real table: `Publisher(id, name, country)`, `Book.publisher_id` FK, `relationship()`
   with `back_populates` on both sides. Creating a book now either links to an existing
   publisher or creates one — your call, pick one and be consistent.

2. **`Member` → `Loan`, one-to-many.** `member.loans`, `loan.member`, `back_populates`
   both sides.

3. **`Book` → `Loan`, one-to-many.** `book.loans`, `loan.book`, `back_populates` both sides.

Notice `Loan` sits between `Book` and `Member` the way a many-to-many join table would —
except it has its own columns (`loan_date`, `due_date`, `status`, `return_date`) that a
bare `secondary=` association table can't hold. This is exactly the "association object"
escape hatch flagged at the end of the Day 14 lesson — `Loan` **is** that pattern, already
present in your domain without you having to invent a contrived example for it.

**Eager loading requirement:** `GET /loans` and `GET /loans/{id}` must eager-load `book`
and `member` — many-to-one, so use `joinedload`. Before you add it, deliberately run the
endpoint with a query-count hook (same one from the Day 14 lesson) against several loans
and confirm you actually see N+1 happening. Then fix it and confirm the count drops. Don't
skip straight to the fixed version — the point is seeing the bug you're fixing.

---

## Database-level enforcement (Day 12/13 — new corollary, not new theory)

Day 11 checked ISBN/email uniqueness by scanning the in-memory dict. That check has a race
condition in any real app and was only ever a stopgap. Now that you have a real database,
enforce it at the schema level too:

```python
isbn: Mapped[str] = mapped_column(unique=True)
email: Mapped[str] = mapped_column(unique=True)
```

This means a duplicate insert will raise `sqlalchemy.exc.IntegrityError` from the database
itself, not from your Python logic. **Catch it in the service layer and re-raise your own
`DuplicateISBNError` / `DuplicateEmailError`** so the response shape stays exactly what it
was in Day 11 — the client should never see a raw `IntegrityError` traceback or a bare 500.

---

## Alembic (Day 15)

1. `alembic init alembic`, wire `sqlalchemy.url` and `target_metadata = Base.metadata`.
2. Generate and apply the **initial migration** — all four tables (`books`, `members`,
   `loans`, `publishers`), all FKs, all relationships reflected correctly in the DDL.
3. **Do not call `Base.metadata.create_all()` anywhere in `main.py`.** `alembic upgrade
   head` is what creates your tables now — run it once before starting `uvicorn`.
4. After you have real data in the tables (create a few books/members/loans through the
   running API), add **one new column** to an existing model — e.g. `book.publication_year`
   or `member.phone_number` — and generate a **second migration**. Apply it and confirm,
   by inspecting the actual `.db` file, that your existing rows are still there and the
   new column exists alongside them. Then `alembic downgrade -1`, confirm the column is
   gone, then `alembic upgrade head` again to get back to current.

---

## What "done" looks like

- `alembic upgrade head` creates all four tables; `uvicorn main:app --reload` starts clean
  with no `create_all()` anywhere in `main.py`.
- Restart `uvicorn` and confirm your data is still there — that's the actual point of Day 16.
- Create a publisher, create a book linked to it, `GET /books/{id}` shows publisher info
  pulled through the real relationship, not hardcoded.
- Borrow a book, hit the loan limit, get your existing 409 — now backed by a real
  `COUNT`-style query against the `loans` table instead of a dict scan.
- Two books with the same ISBN: first succeeds, second returns your `DuplicateISBNError`
  shape from Day 11 — not a 500, not a raw `IntegrityError`.
- `GET /loans` with several loans in the DB: confirm via a query-count hook that it's not
  doing N+1 — book and member should come back in a small, fixed number of queries
  regardless of how many loans exist.
- You can point to two real migration files in `alembic/versions/`, both reviewed by you
  before being applied, and you've successfully downgraded and re-upgraded at least once.

Bring me the code when it runs. Same review process as Day 5 and Day 11.