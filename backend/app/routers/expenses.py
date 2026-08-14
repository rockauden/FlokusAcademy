import io
import csv
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, UfaComplianceSummary
from app.models import Expense, User
from app.auth import require_teacher_user
from app.repository import ExpenseRepository

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

# TODO: per-tenant configuration — ESA/UFA awards vary by state, year and student.
TOTAL_GRANT = 4000.0

@router.get("/", response_model=List[ExpenseResponse])
async def list_expenses(db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    return await ExpenseRepository.list(db, tenant_id=user.tenant_id)

@router.get("/summary", response_model=UfaComplianceSummary)
async def get_expense_summary(db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    expenses = await ExpenseRepository.list(db, tenant_id=user.tenant_id)

    total_spent = sum(e.cost for e in expenses)
    by_category: dict[str, float] = {}
    by_status: dict[str, float] = {}
    for e in expenses:
        by_category[e.category] = by_category.get(e.category, 0.0) + e.cost
        by_status[e.status] = by_status.get(e.status, 0.0) + e.cost

    return UfaComplianceSummary(
        total_grant=TOTAL_GRANT,
        total_spent=total_spent,
        remaining=TOTAL_GRANT - total_spent,
        by_category=by_category,
        by_status=by_status,
    )

@router.post("/", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    new_expense = Expense(**expense.model_dump(), tenant_id=user.tenant_id)
    db.add(new_expense)
    await db.commit()
    await db.refresh(new_expense)
    return new_expense

@router.put("/{id}", response_model=ExpenseResponse)
async def update_expense(id: int, expense_data: ExpenseUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    expense = await ExpenseRepository.get(db, tenant_id=user.tenant_id, expense_id=id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for key, value in expense_data.model_dump().items():
        setattr(expense, key, value)
    await db.commit()
    await db.refresh(expense)
    return expense

@router.patch("/{id}/status", response_model=ExpenseResponse)
async def update_expense_status(id: int, status: str = Body(..., embed=True), db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    expense = await ExpenseRepository.get(db, tenant_id=user.tenant_id, expense_id=id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.status = status
    await db.commit()
    await db.refresh(expense)
    return expense

@router.delete("/{id}")
async def delete_expense(id: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    expense = await ExpenseRepository.get(db, tenant_id=user.tenant_id, expense_id=id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()
    return {"message": "Expense deleted"}

@router.get("/export/csv")
async def export_expenses_csv(db: AsyncSession = Depends(get_db), user: User = Depends(require_teacher_user)):
    expenses = await ExpenseRepository.list(db, tenant_id=user.tenant_id)

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
