from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.admin.dependencies import get_admin_user
from app.admin.service import AdminService, ALLOWED_PLANS
from app.database.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PlanChangeRequest(BaseModel):
    plan: str


class AdminToggleRequest(BaseModel):
    is_admin: bool


@router.get("/users")
async def list_users(
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    admin=Depends(get_admin_user),
    db=Depends(get_db),
):
    service = AdminService(db)
    users = service.list_users(offset, limit, search)
    total = service.count_users(search)
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "is_admin": u.is_admin,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": total,
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin=Depends(get_admin_user),
    db=Depends(get_db),
):
    service = AdminService(db)
    detail = service.get_user_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")
    user = detail["user"]
    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "calendar_id": user.calendar_id,
        },
        "plan": detail["plan"],
        "subscription": detail["subscription"],
    }


@router.patch("/users/{user_id}/plan")
async def change_user_plan(
    user_id: str,
    body: PlanChangeRequest,
    admin=Depends(get_admin_user),
    db=Depends(get_db),
):
    if body.plan not in ALLOWED_PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Allowed: {', '.join(sorted(ALLOWED_PLANS))}",
        )
    service = AdminService(db)
    service.change_user_plan(user_id, body.plan)
    return {"message": "Plan updated", "plan": body.plan}


@router.patch("/users/{user_id}/admin")
async def toggle_admin(
    user_id: str,
    body: AdminToggleRequest,
    admin=Depends(get_admin_user),
    db=Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(
            status_code=400, detail="Cannot change your own admin status"
        )
    service = AdminService(db)
    service.toggle_admin(user_id, body.is_admin)
    return {"message": "Admin status updated", "is_admin": body.is_admin}


@router.get("/stats")
async def get_stats(
    admin=Depends(get_admin_user),
    db=Depends(get_db),
):
    service = AdminService(db)
    return service.get_stats()
