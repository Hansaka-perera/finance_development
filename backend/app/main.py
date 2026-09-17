from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import (
    accounts, credit_cards, income, expenses, transfers,
    budgets, savings_goals, bills, dashboard,
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Finance Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(credit_cards.router)
app.include_router(income.router)
app.include_router(expenses.router)
app.include_router(transfers.router)
app.include_router(budgets.router)
app.include_router(savings_goals.router)
app.include_router(bills.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Personal Finance Management System API"}
