from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from app.shopping.repository import ShoppingRepository
from app.database.models import ShoppingItem, ShoppingSection

_KEYWORDS_PATH = Path(__file__).parent / "keywords.json"


def _normalize(text: str) -> str:
    """Lowercase, strip diacritics (including Polish ł→l), collapse whitespace."""
    text = text.lower().replace("ł", "l")
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _load_keywords() -> dict[str, list[str]]:
    with open(_KEYWORDS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


SECTION_KEYWORDS: dict[str, list[str]] = _load_keywords()

# Pre-normalize keywords to avoid O(N) unicodedata.normalize overhead in hot loops
NORMALIZED_SECTION_KEYWORDS: dict[str, list[str]] = {
    section: [_normalize(kw) for kw in keywords]
    for section, keywords in SECTION_KEYWORDS.items()
}


class ShoppingService:
    def __init__(self, repo: ShoppingRepository):
        self.repo = repo

    # ── Section methods ──────────────────────────────────────────────────

    def ensure_sections(self, calendar_id: str) -> list[ShoppingSection]:
        sections = self.repo.get_sections(calendar_id)
        if not sections:
            sections = self.repo.init_preset_sections(calendar_id)
        return sections

    def list_sections(self, calendar_id: str) -> list[ShoppingSection]:
        return self.ensure_sections(calendar_id)

    def create_section(
        self, calendar_id: str, name: str, emoji: str = "", sort_order: int = 0
    ) -> ShoppingSection:
        return self.repo.create_section(calendar_id, name, emoji, sort_order)

    def update_section(self, section_id: str, data: dict) -> ShoppingSection | None:
        return self.repo.update_section(section_id, data)

    def delete_section(self, section_id: str) -> bool:
        return self.repo.delete_section(section_id)

    # ── Item methods ─────────────────────────────────────────────────────

    def list_items(self, calendar_id: str) -> dict:
        sections = self.ensure_sections(calendar_id)
        items = self.repo.get_items(calendar_id)

        section_map = {s.id: s for s in sections}
        grouped: dict[str, list[dict]] = {s.id: [] for s in sections}
        uncategorized: list[dict] = []

        for item in items:
            item_dict = {
                "id": item.id,
                "name": item.name,
                "section_id": item.section_id,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            if item.section_id and item.section_id in grouped:
                grouped[item.section_id].append(item_dict)
            else:
                uncategorized.append(item_dict)

        sections_out = []
        for s in sections:
            section_items = grouped.get(s.id, [])
            sections_out.append({
                "id": s.id,
                "name": s.name,
                "emoji": s.emoji,
                "sort_order": s.sort_order,
                "is_preset": s.is_preset,
                "items": section_items,
            })

        return {
            "sections": sections_out,
            "uncategorized": uncategorized,
        }

    def add_item(
        self, calendar_id: str, name: str, section_id: str | None = None
    ) -> ShoppingItem:
        if not section_id:
            section_id = self._categorize_item(calendar_id, name)
        return self.repo.create_item(calendar_id, name, section_id)

    def add_multiple(self, calendar_id: str, text: str) -> dict:
        items_text = re.split(r"[,\n]+", text)
        names = [t.strip() for t in items_text if t.strip()]

        created: list[ShoppingItem] = []
        uncategorized_names: list[str] = []
        for name in names:
            section_id = self._categorize_item(calendar_id, name)
            item = self.repo.create_item(calendar_id, name, section_id)
            created.append(item)
            if not section_id:
                uncategorized_names.append(name)

        return {
            "items": [
                {"id": i.id, "name": i.name, "section_id": i.section_id}
                for i in created
            ],
            "uncategorized_names": uncategorized_names,
        }

    def update_item(self, item_id: str, data: dict) -> ShoppingItem | None:
        return self.repo.update_item(item_id, data)

    def delete_item(self, item_id: str) -> bool:
        return self.repo.delete_item(item_id)

    # ── Keyword learning ─────────────────────────────────────────────────

    def learn_keyword(
        self, calendar_id: str, item_name: str, section_id: str
    ) -> None:
        normalized = _normalize(item_name)
        self.repo.upsert_override(calendar_id, normalized, section_id)

    # ── Auto-categorization ──────────────────────────────────────────────

    def _categorize_item(self, calendar_id: str, item_name: str) -> str | None:
        norm = _normalize(item_name)
        sections = self.ensure_sections(calendar_id)
        section_by_name = {s.name: s.id for s in sections}

        # 1. Check user overrides first (learned keywords take priority)
        overrides = self.repo.get_overrides(calendar_id)
        for ovr in overrides:
            if ovr.keyword in norm or norm in ovr.keyword:
                return ovr.section_id

        # 2. Check built-in keyword map (using pre-normalized for performance)
        for section_name, norm_keywords in NORMALIZED_SECTION_KEYWORDS.items():
            if section_name not in section_by_name:
                continue
            for norm_kw in norm_keywords:
                if norm_kw in norm:
                    return section_by_name[section_name]
                # Reverse match for short item names
                if len(norm) >= 3 and norm in norm_kw:
                    return section_by_name[section_name]

        return None
