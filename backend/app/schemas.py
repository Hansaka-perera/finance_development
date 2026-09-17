from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ---------- Accounts ----------
class AccountCreate(BaseModel):
    name: str
    type: str  # "cash" or "bank"
    bank_name: Optional[str] = None
    balance: float = 0.0


class AccountOut(AccountCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Credit Cards ----------
class CreditCardCreate(BaseModel):
    card_name: str
    bank_name: Optional[str] = None
    credit_limit: float
    current_balance: float = 0.0
    billing_date: Optional[int] = None
    due_date: Optional[int] = None
    minimum_payment: Optional[float] = 0.0


class CreditCardOut(CreditCardCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class CreditCardPaymentCreate(BaseModel):
    credit_card_id: int
    account_id: int
    amount: float
    date: date = None


# ---------- Income ----------
class IncomeCreate(BaseModel):
    amount: float
    category: str
    date: date
    account_id: int
    description: Optional[str] = None


class IncomeOut(IncomeCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Expenses ----------
class ExpenseCreate(BaseModel):
    amount: float
    category: str
    date: date
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    description: Optional[str] = None


class ExpenseOut(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Transfers ----------
class TransferCreate(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float
    date: date
    description: Optional[str] = None


class TransferOut(TransferCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Budgets ----------
class BudgetCreate(BaseModel):
    category: str
    monthly_limit: float


class BudgetOut(BudgetCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Savings Goals ----------
class SavingsGoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: Optional[date] = None


class SavingsGoalContribution(BaseModel):
    amount: float
    account_id: int


class SavingsGoalOut(SavingsGoalCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------- Bills ----------
class BillCreate(BaseModel):
    name: str
    amount: float
    due_date: date
    frequency: str = "monthly"
    account_id: Optional[int] = None
    status: str = "unpaid"


class BillOut(BillCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
