from datetime import timedelta
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/bills", tags=["bills"])


@router.get("", response_model=list[schemas.BillOut])
def list_bills(db: Session = Depends(get_db)):
    return db.query(models.Bill).order_by(models.Bill.due_date.asc()).all()


@router.post("", response_model=schemas.BillOut)
def create_bill(payload: schemas.BillCreate, db: Session = Depends(get_db)):
    bill = models.Bill(**payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@router.post("/{bill_id}/pay", response_model=schemas.BillOut)
def pay_bill(bill_id: int, db: Session = Depends(get_db)):
    """Marks a bill paid, deducts from its linked account, and rolls
    recurring bills forward to their next due date."""
    bill = db.query(models.Bill).get(bill_id)
    if not bill:
        raise HTTPException(404, "Bill not found")
    if bill.status == "paid":
        raise HTTPException(400, "Bill already paid")

    if bill.account_id:
        account = db.query(models.Account).get(bill.account_id)
        if not account:
            raise HTTPException(404, "Linked account not found")
        account.balance -= bill.amount

        expense = models.Expense(
            amount=bill.amount,
            category="Bills",
            date=bill.due_date,
            account_id=bill.account_id,
            description=f"Bill payment: {bill.name}",
        )
        db.add(expense)

    if bill.frequency == "monthly":
        bill.due_date = bill.due_date + relativedelta(months=1)
        bill.status = "unpaid"
    elif bill.frequency == "yearly":
        bill.due_date = bill.due_date + relativedelta(years=1)
        bill.status = "unpaid"
    else:  # one-time
        bill.status = "paid"

    db.commit()
    db.refresh(bill)
    return bill


@router.delete("/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = db.query(models.Bill).get(bill_id)
    if not bill:
        raise HTTPException(404, "Bill not found")
    db.delete(bill)
    db.commit()
    return {"deleted": True}
