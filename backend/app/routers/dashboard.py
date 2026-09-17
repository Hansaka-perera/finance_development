from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

LOW_BALANCE_THRESHOLD = 5000.0


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    today = date.today()
    month_start = today.replace(day=1)

    accounts = db.query(models.Account).all()
    cash_balance = sum(a.balance for a in accounts if a.type == "cash")
    bank_balance = sum(a.balance for a in accounts if a.type == "bank")
    current_balance = cash_balance + bank_balance

    cards = db.query(models.CreditCard).all()
    credit_card_debt = sum(c.current_balance for c in cards)

    monthly_income = (
        db.query(func.coalesce(func.sum(models.Income.amount), 0.0))
        .filter(models.Income.date >= month_start)
        .scalar()
    )
    monthly_expenses = (
        db.query(func.coalesce(func.sum(models.Expense.amount), 0.0))
        .filter(models.Expense.date >= month_start)
        .scalar()
    )

    goals = db.query(models.SavingsGoal).all()
    total_savings = sum(g.current_amount for g in goals)

    budgets = db.query(models.Budget).all()
    budget_status = []
    for b in budgets:
        spent = (
            db.query(func.coalesce(func.sum(models.Expense.amount), 0.0))
            .filter(
                models.Expense.category == b.category,
                models.Expense.date >= month_start,
            )
            .scalar()
        )
        pct = round((spent / b.monthly_limit) * 100, 1) if b.monthly_limit else 0
        budget_status.append({
            "category": b.category,
            "limit": b.monthly_limit,
            "spent": spent,
            "remaining": b.monthly_limit - spent,
            "percent_used": pct,
        })

    total_budget = sum(b.monthly_limit for b in budgets)
    remaining_budget = total_budget - monthly_expenses if total_budget else None

    upcoming_cutoff = today + timedelta(days=7)
    upcoming_bills = (
        db.query(models.Bill)
        .filter(models.Bill.status == "unpaid", models.Bill.due_date <= upcoming_cutoff)
        .order_by(models.Bill.due_date.asc())
        .all()
    )

    warnings = []
    for bs in budget_status:
        if bs["percent_used"] >= 100:
            warnings.append({
                "level": "critical",
                "message": f"You have exceeded your {bs['category']} budget.",
            })
        elif bs["percent_used"] >= 90:
            warnings.append({
                "level": "warning",
                "message": f"You've used {bs['percent_used']}% of your {bs['category']} budget.",
            })

    if current_balance < LOW_BALANCE_THRESHOLD:
        warnings.append({
            "level": "warning",
            "message": f"Your balance is below Rs. {LOW_BALANCE_THRESHOLD:,.0f}.",
        })

    for c in cards:
        if c.credit_limit:
            usage = c.current_balance / c.credit_limit * 100
            if usage >= 85:
                warnings.append({
                    "level": "warning",
                    "message": f"Your {c.card_name} card is at {usage:.0f}% of its limit.",
                })

    for bill in upcoming_bills:
        days_left = (bill.due_date - today).days
        if days_left <= 1:
            warnings.append({
                "level": "warning",
                "message": f"Your {bill.name} bill is due {'today' if days_left == 0 else 'tomorrow'}.",
            })

    if total_budget and monthly_expenses > total_budget:
        warnings.append({
            "level": "critical",
            "message": "You have exceeded your overall monthly budget.",
        })

    return {
        "current_balance": current_balance,
        "cash_balance": cash_balance,
        "bank_balance": bank_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "available_money": current_balance,
        "total_savings": total_savings,
        "credit_card_debt": credit_card_debt,
        "remaining_budget": remaining_budget,
        "budget_status": budget_status,
        "savings_goals": [
            {
                "id": g.id,
                "name": g.name,
                "target_amount": g.target_amount,
                "current_amount": g.current_amount,
                "progress_percent": round((g.current_amount / g.target_amount) * 100, 1) if g.target_amount else 0,
                "deadline": g.deadline,
            }
            for g in goals
        ],
        "upcoming_bills": [
            {"id": b.id, "name": b.name, "amount": b.amount, "due_date": b.due_date}
            for b in upcoming_bills
        ],
        "warnings": warnings,
    }
