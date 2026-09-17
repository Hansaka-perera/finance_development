# Ledger — Personal Finance Management System (v1)

A working first version of the system described in the development report:
income, expenses, cash, bank accounts, credit cards, transfers, budgets,
savings goals, bills, a dashboard, and smart spending warnings.

**Scope note:** to get you a real, running app instead of a half-built
sprawl, this v1 deliberately skips user authentication (single local user)
and the double-entry accounting layer (Section 18 of the report). Those are
Phase 3+/Phase 6 items — see "What's next" below for how to add them without
having to rebuild the core.

## Stack

- **Backend:** Python + FastAPI + SQLAlchemy + SQLite (`backend/`)
- **Frontend:** HTML + CSS + vanilla JavaScript, no build step (`frontend/`)

## Running it

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://127.0.0.1:8000`. A `finance.db` SQLite
file is created automatically on first run. Interactive API docs are at
`http://127.0.0.1:8000/docs`.

### 2. Frontend

The frontend is static files that call the API directly — no build tool
needed. From the `frontend/` folder, serve it with any static server, e.g.:

```bash
cd frontend
python3 -m http.server 5500
```

Then open `http://127.0.0.1:5500` in your browser. (Opening `index.html`
directly with `file://` also works in most browsers, since the frontend
only talks to the API over `http://127.0.0.1:8000`.)

If you serve the frontend from a different host/port, update `API_BASE` in
`frontend/js/api.js`.

## What's implemented

- **Accounts** — cash and bank accounts, balances update automatically
- **Credit cards** — purchases increase the balance owed, payments reduce it
  and debit the paying account
- **Income / Expenses** — categorized, tied to an account or a credit card
- **Transfers** — move money between accounts without it counting as spend
- **Budgets** — a monthly limit per category, compared against actual spend
- **Savings goals** — target + progress, contributions pull from an account
- **Bills** — recurring (monthly/yearly) or one-time, "mark paid" rolls
  recurring bills forward and logs an expense
- **Dashboard** — balances, income/expenses this month, budget and goal
  progress, upcoming bills, and generated warnings (low balance, budget
  90%+/exceeded, credit card 85%+ utilization, bill due tomorrow)

## What's next (from the original phased plan)

- **Phase 3 remainder:** notifications/reminders beyond the dashboard banner
- **Phase 4:** the double-entry ledger (`journal_entries` /
  `journal_entry_lines`) described in Section 18 — recommended to build as a
  layer that's *generated from* income/expense/transfer records rather than
  a second source of truth, to avoid the two ever disagreeing
- **Phase 5:** charts (income vs. expenses, category breakdown, budget
  usage) and the daily/weekly/yearly report views
- **Phase 6:** real user accounts (register/login/password reset/JWT),
  PostgreSQL, and multi-device sync — the API is already structured with
  one router per resource, so adding a `user_id` foreign key and an auth
  dependency to each router is mechanical, not a rewrite
- The "Financial Health Score" and "Can I Afford This?" features, since both
  depend on the above being reliable first

## Project layout

```text
backend/
  app/
    main.py          FastAPI app, router wiring, CORS
    database.py       SQLAlchemy engine/session
    models.py          ORM models
    schemas.py          Pydantic request/response models
    routers/              accounts, credit_cards, income, expenses,
                            transfers, budgets, savings_goals, bills, dashboard
  requirements.txt

frontend/
  index.html
  css/style.css
  js/api.js    thin fetch wrapper
  js/app.js     navigation, rendering, form handling
```
