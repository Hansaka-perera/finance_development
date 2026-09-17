from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/credit-cards", tags=["credit-cards"])


@router.get("", response_model=list[schemas.CreditCardOut])
def list_cards(db: Session = Depends(get_db)):
    return db.query(models.CreditCard).all()


@router.post("", response_model=schemas.CreditCardOut)
def create_card(payload: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    card = models.CreditCard(**payload.model_dump())
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


@router.put("/{card_id}", response_model=schemas.CreditCardOut)
def update_card(card_id: int, payload: schemas.CreditCardCreate, db: Session = Depends(get_db)):
    card = db.query(models.CreditCard).get(card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    for k, v in payload.model_dump().items():
        setattr(card, k, v)
    db.commit()
    db.refresh(card)
    return card


@router.delete("/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db)):
    card = db.query(models.CreditCard).get(card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    db.delete(card)
    db.commit()
    return {"deleted": True}


@router.post("/pay")
def pay_credit_card(payload: schemas.CreditCardPaymentCreate, db: Session = Depends(get_db)):
    """Pay down a credit card from a cash/bank account. Decreases the card
    balance and decreases the paying account's balance by the same amount."""
    card = db.query(models.CreditCard).get(payload.credit_card_id)
    account = db.query(models.Account).get(payload.account_id)
    if not card or not account:
        raise HTTPException(404, "Card or account not found")
    if payload.amount <= 0:
        raise HTTPException(400, "Payment amount must be positive")

    payment = models.CreditCardPayment(
        credit_card_id=payload.credit_card_id,
        account_id=payload.account_id,
        amount=payload.amount,
        date=payload.date,
    )
    card.current_balance -= payload.amount
    account.balance -= payload.amount

    db.add(payment)
    db.commit()
    return {
        "card_balance": card.current_balance,
        "account_balance": account.balance,
    }
