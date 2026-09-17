from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=list[schemas.ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(models.Expense).order_by(models.Expense.date.desc()).all()


@router.post("", response_model=schemas.ExpenseOut)
def create_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    if bool(payload.account_id) == bool(payload.credit_card_id):
        raise HTTPException(
            400, "Provide exactly one of account_id or credit_card_id"
        )

    if payload.account_id:
        account = db.query(models.Account).get(payload.account_id)
        if not account:
            raise HTTPException(404, "Account not found")
        account.balance -= payload.amount
    else:
        card = db.query(models.CreditCard).get(payload.credit_card_id)
        if not card:
            raise HTTPException(404, "Credit card not found")
        card.current_balance += payload.amount

    expense = models.Expense(**payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(models.Expense).get(expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")

    if expense.account_id:
        account = db.query(models.Account).get(expense.account_id)
        if account:
            account.balance += expense.amount
    elif expense.credit_card_id:
        card = db.query(models.CreditCard).get(expense.credit_card_id)
        if card:
            card.current_balance -= expense.amount

    db.delete(expense)
    db.commit()
    return {"deleted": True}
