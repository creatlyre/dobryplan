from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.sync.service import GoogleSyncService
from config import Settings

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/export-month")
async def export_month(
    year: int = Query(...),
    month: int = Query(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = GoogleSyncService(db)
    result = service.export_month(user, year, month)
    return {
        "users_synced": result.users_synced,
        "events_synced": result.events_synced,
        "errors": result.errors,
    }


@router.post("/import-month")
async def import_month(
    year: int = Query(...),
    month: int = Query(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    service = GoogleSyncService(db)
    result = service.import_month(user, year, month)
    requires_reauth = any(
        "insufficientPermissions" in err or "insufficient authentication scopes" in err.lower()
        for err in result.errors
    )
    return {
        "events_imported": result.events_imported,
        "events_updated": result.events_updated,
        "calendars_scanned": result.calendars_scanned,
        "requires_reauth": requires_reauth,
        "errors": result.errors,
    }


@router.get("/status")
async def sync_status(user=Depends(get_current_user), db=Depends(get_db)):
    household_size = db.count("users", {"calendar_id": f"eq.{user.calendar_id}"}) if user.calendar_id else 0
    settings = Settings()
    google_connected = bool(getattr(user, "google_refresh_token", None) or getattr(user, "google_access_token", None))
    oauth_configured = bool(getattr(settings, "GOOGLE_CLIENT_ID", None) and getattr(settings, "GOOGLE_CLIENT_SECRET", None))
    calendar_last_sync = None

    if user.calendar_id:
        rows = db.select("calendars", {"id": f"eq.{user.calendar_id}", "limit": "1"})
        if rows:
            calendar_last_sync = rows[0].get("last_sync_at")

    if not oauth_configured:
        status = "oauth_not_configured"
    elif not google_connected:
        status = "google_not_connected"
    else:
        status = "ready"

    return {
        "calendar_id": user.calendar_id,
        "household_users": household_size,
        "google_connected": google_connected,
        "oauth_configured": oauth_configured,
        "connect_url": "/auth/login",
        "last_successful_sync_at": calendar_last_sync,
        "status": status,
    }
