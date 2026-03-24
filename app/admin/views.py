from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.admin.dependencies import get_admin_user
from app.admin.service import AdminService
from app.database.database import get_db
from app.i18n import inject_template_i18n, set_locale_cookie_if_param

router = APIRouter(prefix="/admin", tags=["admin-views"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user=Depends(get_admin_user),
    db=Depends(get_db),
):
    service = AdminService(db)
    stats = service.get_stats()

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "stats": stats,
        },
    )
    response = templates.TemplateResponse(
        request=request, name="admin_dashboard.html", context=context,
    )
    set_locale_cookie_if_param(response, request)
    return response


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    offset: int = 0,
    limit: int = 50,
    search: str | None = None,
    user=Depends(get_admin_user),
    db=Depends(get_db),
):
    service = AdminService(db)
    users = service.list_users(offset, limit, search)
    total = service.count_users(search)

    # Build plan map for user list
    plan_map = {}
    for u in users:
        detail = service.get_user_detail(u.id)
        if detail:
            plan_map[u.id] = detail["plan"]

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "users": users,
            "total": total,
            "offset": offset,
            "limit": limit,
            "search": search or "",
            "_plan_map": plan_map,
        },
    )
    response = templates.TemplateResponse(
        request=request, name="admin_users.html", context=context,
    )
    set_locale_cookie_if_param(response, request)
    return response


@router.get("/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail_page(
    request: Request,
    user_id: str,
    user=Depends(get_admin_user),
    db=Depends(get_db),
):
    service = AdminService(db)
    detail = service.get_user_detail(user_id)
    if not detail:
        raise HTTPException(status_code=404, detail="User not found")

    context = inject_template_i18n(
        request,
        {
            "request": request,
            "user": user,
            "target_user": detail["user"],
            "target_plan": detail["plan"],
            "target_subscription": detail["subscription"],
        },
    )
    response = templates.TemplateResponse(
        request=request, name="admin_user_detail.html", context=context,
    )
    set_locale_cookie_if_param(response, request)
    return response
