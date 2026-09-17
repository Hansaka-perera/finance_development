from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/transfers", tags=["transfers"])


@router.get("", response_model=list[schemas.TransferOut])
def list_transfers(db: Session = Depends(get_db)):
    return db.query(models.Transfer).order_by(models.Transfer.date.desc()).all()


@router.post("", response_model=schemas.TransferOut)
def create_transfer(payload: schemas.TransferCreate, db: Session = Depends(get_db)):
    if payload.from_account_id == payload.to_account_id:
        raise HTTPException(400, "Cannot transfer to the same account")

    from_acc = db.query(models.Account).get(payload.from_account_id)
    to_acc = db.query(models.Account).get(payload.to_account_id)
    if not from_acc or not to_acc:
        raise HTTPException(404, "Account not found")
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")

    from_acc.balance -= payload.amount
    to_acc.balance += payload.amount

    transfer = models.Transfer(**payload.model_dump())
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer
