from __future__ import annotations

from typing import Any, Dict, List, Optional
import json

import httpx
import jwt

from config import Settings


class SupabaseStoreError(RuntimeError):
    def __init__(
        self,
        operation: str,
        table: str,
        status_code: int,
        response_text: str,
        *,
        request_id: str | None = None,
        auth_context: dict[str, Any] | None = None,
        payload_keys: list[str] | None = None,
        payload_preview: dict[str, Any] | None = None,
        filters: dict[str, str] | None = None,
    ):
        self.operation = operation
        self.table = table
        self.status_code = status_code
        self.response_text = response_text
        self.request_id = request_id
        self.auth_context = auth_context or {}
        self.payload_keys = payload_keys or []
        self.payload_preview = payload_preview or {}
        self.filters = filters or {}

        detail = self._safe_detail(response_text)
        msg = (
            f"Supabase {operation} failed"
            f" | table={table}"
            f" | status={status_code}"
            f" | req_id={request_id or 'n/a'}"
            f" | code={detail.get('code', 'n/a')}"
            f" | message={detail.get('message', response_text)}"
            f" | hint={detail.get('hint', 'n/a')}"
            f" | auth={self.auth_context}"
            f" | payload_keys={self.payload_keys}"
            f" | payload_preview={self.payload_preview}"
            f" | filters={self.filters}"
        )
        super().__init__(msg)

    @staticmethod
    def _safe_detail(response_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        return {}


_shared_client: httpx.Client | None = None


def _get_shared_client() -> httpx.Client:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.Client(timeout=20.0)
    return _shared_client


class SupabaseStore:
    def __init__(self):
        self.settings = Settings()
        self.base_url = self.settings.SUPABASE_URL.rstrip("/")
        self.api_key = self.settings.SUPABASE_SERVICE_ROLE_KEY or self.settings.SUPABASE_ANON_KEY
        self._client = _get_shared_client()

    def _auth_context(self, auth_token: str | None) -> dict[str, Any]:
        if not auth_token:
            return {"token": "none"}

        context: dict[str, Any] = {"token": "provided", "token_suffix": auth_token[-8:]}
        try:
            claims = jwt.decode(auth_token, options={"verify_signature": False})
            context.update(
                {
                    "sub": claims.get("sub"),
                    "email": claims.get("email"),
                    "role": claims.get("role"),
                    "aud": claims.get("aud"),
                }
            )
        except Exception:
            context["claims"] = "unavailable"
        return context

    @staticmethod
    def _payload_preview(payload: Dict[str, Any]) -> dict[str, Any]:
        preview_keys = {
            "id",
            "owner_user_id",
            "calendar_id",
            "inviter_user_id",
            "email",
            "google_id",
            "status",
        }
        preview: dict[str, Any] = {}
        for key in preview_keys:
            if key in payload:
                preview[key] = payload[key]
        return preview

    def _headers(
        self,
        auth_token: str | None = None,
        content_type_json: bool = True,
        prefer: str | None = None,
    ) -> Dict[str, str]:
        if not self.base_url or not self.api_key:
            raise RuntimeError("Supabase config is missing SUPABASE_URL/SUPABASE key")

        headers: Dict[str, str] = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {auth_token or self.api_key}",
        }
        if content_type_json:
            headers["Content-Type"] = "application/json"
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def select(self, table: str, params: Dict[str, str], auth_token: str | None = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        query = {"select": "*", **params}
        response = self._client.get(url, params=query, headers=self._headers(auth_token=auth_token, content_type_json=False))
        if response.status_code >= 400:
            raise SupabaseStoreError(
                "select",
                table,
                response.status_code,
                response.text,
                request_id=response.headers.get("x-request-id"),
                auth_context=self._auth_context(auth_token),
                filters=params,
            )
        return response.json()

    def insert(
        self,
        table: str,
        payload: Dict[str, Any],
        auth_token: str | None = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/rest/v1/{table}"
        response = self._client.post(
            url,
            json=payload,
            headers=self._headers(auth_token=auth_token, prefer="return=representation"),
        )
        if response.status_code >= 400:
            raise SupabaseStoreError(
                "insert",
                table,
                response.status_code,
                response.text,
                request_id=response.headers.get("x-request-id"),
                auth_context=self._auth_context(auth_token),
                payload_keys=sorted(payload.keys()),
                payload_preview=self._payload_preview(payload),
            )
        data = response.json()
        return data[0] if data else {}

    def update(
        self,
        table: str,
        filters: Dict[str, str],
        payload: Dict[str, Any],
        auth_token: str | None = None,
    ) -> Dict[str, Any] | None:
        url = f"{self.base_url}/rest/v1/{table}"
        response = self._client.patch(
            url,
            params=filters,
            json=payload,
            headers=self._headers(auth_token=auth_token, prefer="return=representation"),
        )
        if response.status_code >= 400:
            raise SupabaseStoreError(
                "update",
                table,
                response.status_code,
                response.text,
                request_id=response.headers.get("x-request-id"),
                auth_context=self._auth_context(auth_token),
                payload_keys=sorted(payload.keys()),
                payload_preview=self._payload_preview(payload),
                filters=filters,
            )
        data = response.json()
        return data[0] if data else None

    def count(self, table: str, filters: Dict[str, str], auth_token: str | None = None) -> int:
        url = f"{self.base_url}/rest/v1/{table}"
        headers = self._headers(auth_token=auth_token, content_type_json=False, prefer="count=exact")
        query = {"select": "id", **filters}
        response = self._client.get(url, params=query, headers=headers)
        if response.status_code >= 400:
            raise SupabaseStoreError(
                "count",
                table,
                response.status_code,
                response.text,
                request_id=response.headers.get("x-request-id"),
                auth_context=self._auth_context(auth_token),
                filters=filters,
            )
        content_range = response.headers.get("content-range", "")
        if "/" in content_range:
            try:
                return int(content_range.split("/")[-1])
            except ValueError:
                return len(response.json())
        return len(response.json())

    def delete(self, table: str, filters: Dict[str, str], auth_token: str | None = None) -> int:
        url = f"{self.base_url}/rest/v1/{table}"
        response = self._client.delete(
            url,
            params=filters,
            headers=self._headers(auth_token=auth_token, content_type_json=False, prefer="return=representation"),
        )
        if response.status_code >= 400:
            raise SupabaseStoreError(
                "delete",
                table,
                response.status_code,
                response.text,
                request_id=response.headers.get("x-request-id"),
                auth_context=self._auth_context(auth_token),
                filters=filters,
            )
        data = response.json()
        return len(data) if isinstance(data, list) else (1 if data else 0)