from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/income", tags=["income"])


@router.get("", response_model=list[schemas.IncomeOut])
def list_income(db: Session = Depends(get_db)):
    return db.query(models.Income).order_by(models.Income.date.desc()).all()


@router.post("", response_model=schemas.IncomeOut)
def create_income(payload: schemas.IncomeCreate, db: Session = Depends(get_db)):
    account = db.query(models.Account).get(payload.account_id)
    if not account:
        raise HTTPException(404, "Account not found")

    income = models.Income(**payload.model_dump())
    account.balance += payload.amount

    db.add(income)
    db.commit()
    db.refresh(income)
    return income


@router.delete("/{income_id}")
def delete_income(income_id: int, db: Session = Depends(get_db)):
    income = db.query(models.Income).get(income_id)
    if not income:
        raise HTTPException(404, "Income not found")
    account = db.query(models.Account).get(income.account_id)
    if account:
        account.balance -= income.amount
    db.delete(income)
    db.commit()
    return {"deleted": True}
