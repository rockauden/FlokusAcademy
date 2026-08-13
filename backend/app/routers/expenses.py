import io
import csv
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.database import get_db
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, UfaComplianceSummary
from app.models import Expense
from app.auth import require_teacher

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

@router.get("/", response_model=List[ExpenseResponse])
async def list_expenses(db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Expense).order_by(Expense.created_at.desc()))
    return result.scalars().all()

@router.get("/summary", response_model=UfaComplianceSummary)
async def get_expense_summary(db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Expense))
    expenses = result.scalars().all()
    
    total_grant = 4000.0
    total_spent = sum(e.cost for e in expenses)
    remaining = total_grant - total_spent
    
    by_category = {}
    by_status = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0.0) + e.cost
        by_status[e.status] = by_status.get(e.status, 0.0) + e.cost
        
    return UfaComplianceSummary(
        total_grant=total_grant,
        total_spent=total_spent,
        remaining=remaining,
        by_category=by_category,
        by_status=by_status
    )

@router.post("/", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    new_expense = Expense(**expense.model_dump())
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense

@router.put("/{id}", response_model=ExpenseResponse)
async def update_expense(id: int, expense_data: ExpenseUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Expense).where(Expense.id == id))
    expense = result.scalars().first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in expense_data.model_dump().items():
        setattr(expense, key, value)
    await db.commit()
    await db.refresh(expense)
    return expense

@router.patch("/{id}/status", response_model=ExpenseResponse)
async def update_expense_status(id: int, status: str = Body(..., embed=True), db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Expense).where(Expense.id == id))
    expense = result.scalars().first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.status = status
    await db.commit()
    await db.refresh(expense)
    return expense

@router.delete("/{id}")
async def delete_expense(id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Expense).where(Expense.id == id))
    expense = result.scalars().first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()
    return {"message": "Expense deleted"}

@router.get("/export/csv")
async def export_expenses_csv(db: AsyncSession = Depends(get_db), current_user: dict = Depends(require_teacher)):
    result = await db.execute(select(Expense).order_by(Expense.created_at.desc()))
    expenses = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Item Name", "Cost", "Category", "Status", "Purchase Date", "Odyssey Ref", "Notes"])
    
    for e in expenses:
        writer.writerow([e.id, e.item_name, e.cost, e.category, e.status, e.purchase_date, e.odyssey_ref, e.notes])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"}
    )
