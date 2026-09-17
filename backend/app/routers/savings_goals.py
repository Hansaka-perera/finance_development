from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/savings-goals", tags=["savings-goals"])


@router.get("", response_model=list[schemas.SavingsGoalOut])
def list_goals(db: Session = Depends(get_db)):
    return db.query(models.SavingsGoal).all()


@router.post("", response_model=schemas.SavingsGoalOut)
def create_goal(payload: schemas.SavingsGoalCreate, db: Session = Depends(get_db)):
    goal = models.SavingsGoal(**payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.post("/{goal_id}/contribute", response_model=schemas.SavingsGoalOut)
def contribute(goal_id: int, payload: schemas.SavingsGoalContribution, db: Session = Depends(get_db)):
    goal = db.query(models.SavingsGoal).get(goal_id)
    account = db.query(models.Account).get(payload.account_id)
    if not goal or not account:
        raise HTTPException(404, "Goal or account not found")
    if payload.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if account.balance < payload.amount:
        raise HTTPException(400, "Insufficient account balance")

    account.balance -= payload.amount
    goal.current_amount += payload.amount
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}")
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(models.SavingsGoal).get(goal_id)
    if not goal:
        raise HTTPException(404, "Goal not found")
    db.delete(goal)
    db.commit()
    return {"deleted": True}
