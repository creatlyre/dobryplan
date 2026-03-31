from __future__ import annotations

from datetime import datetime, timezone

from app.database.models import ShoppingItem, ShoppingSection, ShoppingKeywordOverride
from app.database.supabase_store import SupabaseStore


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def _to_section(row: dict) -> ShoppingSection:
    return ShoppingSection(
        id=row.get("id", ""),
        calendar_id=row.get("calendar_id", ""),
        name=row.get("name", ""),
        emoji=row.get("emoji", ""),
        sort_order=int(row.get("sort_order", 0)),
        is_preset=bool(row.get("is_preset", True)),
        created_at=_parse_dt(row.get("created_at")),
        updated_at=_parse_dt(row.get("updated_at")),
    )


def _to_item(row: dict) -> ShoppingItem:
    return ShoppingItem(
        id=row.get("id", ""),
        calendar_id=row.get("calendar_id", ""),
        name=row.get("name", ""),
        section_id=row.get("section_id"),
        created_at=_parse_dt(row.get("created_at")),
        updated_at=_parse_dt(row.get("updated_at")),
    )


def _to_override(row: dict) -> ShoppingKeywordOverride:
    return ShoppingKeywordOverride(
        id=row.get("id", ""),
        calendar_id=row.get("calendar_id", ""),
        keyword=row.get("keyword", ""),
        section_id=row.get("section_id", ""),
        created_at=_parse_dt(row.get("created_at")),
    )


_PRESET_SECTIONS = [
    ("🍅", "Warzywa i Owoce", 1),
    ("🥩", "Lada Tradycyjna / Mięso", 2),
    ("🐟", "Ryby", 3),
    ("🧀", "Nabiał i Lodówki", 4),
    ("🥫", "Puszki, Sosy, Przetwory", 5),
    ("🧁", "Pieczenie / Bakalie", 6),
    ("👶", "Dział Dziecięcy", 7),
    ("🧃", "Napoje", 8),
    ("🍺", "Alkohol", 9),
    ("🧻", "Chemia / Higiena", 10),
]


class ShoppingRepository:
    def __init__(self, db: SupabaseStore):
        self.db = db

    # ── Section methods ──────────────────────────────────────────────────

    def get_sections(self, calendar_id: str) -> list[ShoppingSection]:
        rows = self.db.select(
            "shopping_sections",
            {"calendar_id": f"eq.{calendar_id}", "order": "sort_order.asc"},
        )
        return [_to_section(row) for row in rows]

    def create_section(
        self,
        calendar_id: str,
        name: str,
        emoji: str = "",
        sort_order: int = 0,
        is_preset: bool = False,
    ) -> ShoppingSection:
        row = self.db.insert(
            "shopping_sections",
            {
                "calendar_id": calendar_id,
                "name": name,
                "emoji": emoji,
                "sort_order": sort_order,
                "is_preset": is_preset,
            },
        )
        return _to_section(row)

    def update_section(self, section_id: str, data: dict) -> ShoppingSection | None:
        data["updated_at"] = datetime.utcnow().isoformat()
        row = self.db.update(
            "shopping_sections", {"id": f"eq.{section_id}"}, data
        )
        return _to_section(row) if row else None

    def delete_section(self, section_id: str) -> bool:
        count = self.db.delete("shopping_sections", {"id": f"eq.{section_id}"})
        return count > 0

    def init_preset_sections(self, calendar_id: str) -> list[ShoppingSection]:
        results: list[ShoppingSection] = []
        for emoji, name, sort_order in _PRESET_SECTIONS:
            row = self.db.insert(
                "shopping_sections",
                {
                    "calendar_id": calendar_id,
                    "name": name,
                    "emoji": emoji,
                    "sort_order": sort_order,
                    "is_preset": True,
                },
            )
            results.append(_to_section(row))
        return results

    # ── Item methods ─────────────────────────────────────────────────────

    def get_items(self, calendar_id: str) -> list[ShoppingItem]:
        rows = self.db.select(
            "shopping_items",
            {"calendar_id": f"eq.{calendar_id}", "order": "created_at.asc"},
        )
        return [_to_item(row) for row in rows]

    def create_item(
        self, calendar_id: str, name: str, section_id: str | None = None
    ) -> ShoppingItem:
        data: dict = {"calendar_id": calendar_id, "name": name}
        if section_id:
            data["section_id"] = section_id
        row = self.db.insert("shopping_items", data)
        return _to_item(row)

    def create_multiple_items(self, calendar_id: str, items_data: list[dict]) -> list[ShoppingItem]:
        if not items_data:
            return []
        payloads = []
        for item in items_data:
            data = {"calendar_id": calendar_id, "name": item["name"]}
            if item.get("section_id"):
                data["section_id"] = item["section_id"]
            payloads.append(data)
        rows = self.db.bulk_insert("shopping_items", payloads)
        return [_to_item(row) for row in rows]

    def update_item(self, item_id: str, data: dict) -> ShoppingItem | None:
        data["updated_at"] = datetime.utcnow().isoformat()
        row = self.db.update("shopping_items", {"id": f"eq.{item_id}"}, data)
        return _to_item(row) if row else None

    def delete_item(self, item_id: str) -> bool:
        count = self.db.delete("shopping_items", {"id": f"eq.{item_id}"})
        return count > 0

    # ── Keyword override methods ─────────────────────────────────────────

    def get_overrides(self, calendar_id: str) -> list[ShoppingKeywordOverride]:
        rows = self.db.select(
            "shopping_keyword_overrides",
            {"calendar_id": f"eq.{calendar_id}"},
        )
        return [_to_override(row) for row in rows]

    def upsert_override(
        self, calendar_id: str, keyword: str, section_id: str
    ) -> ShoppingKeywordOverride:
        # Check if override already exists
        existing = self.db.select(
            "shopping_keyword_overrides",
            {"calendar_id": f"eq.{calendar_id}", "keyword": f"eq.{keyword}"},
        )
        if existing:
            row = self.db.update(
                "shopping_keyword_overrides",
                {"id": f"eq.{existing[0]['id']}"},
                {"section_id": section_id},
            )
            return _to_override(row) if row else _to_override(existing[0])
        row = self.db.insert(
            "shopping_keyword_overrides",
            {
                "calendar_id": calendar_id,
                "keyword": keyword,
                "section_id": section_id,
            },
        )
        return _to_override(row)
