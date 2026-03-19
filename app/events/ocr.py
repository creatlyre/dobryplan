from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.events.nlp import NLPService


@dataclass
class OCRParseResult:
    title: str = ""
    start_at: datetime | None = None
    end_at: datetime | None = None
    timezone: str = "UTC"
    confidence_title: float = 0.0
    confidence_date: float = 0.0
    confidence_raw: float = 0.0
    raw_text: str = ""
    errors: list[str] = field(default_factory=list)


class OCRService:
    """Extract OCR text with EasyOCR (if installed) and parse it into event fields."""

    def __init__(self, reader: Any | None = None) -> None:
        self._reader = reader

    def _get_reader(self, locale: str = "en") -> Any:
        if self._reader is not None:
            return self._reader

        try:
            import easyocr  # type: ignore
        except Exception as exc:  # pragma: no cover - exercised in environments without easyocr
            raise RuntimeError("EasyOCR is not installed") from exc

        langs = ["pl", "en"] if locale == "pl" else ["en"]
        self._reader = easyocr.Reader(langs, gpu=False)
        return self._reader

    @staticmethod
    def _normalize_read_result(result: Any) -> tuple[list[str], list[float]]:
        texts: list[str] = []
        confidences: list[float] = []

        if not isinstance(result, list):
            return texts, confidences

        for item in result:
            if not isinstance(item, (list, tuple)) or len(item) < 3:
                continue
            text = str(item[1]).strip()
            conf = float(item[2])
            if text:
                texts.append(text)
                confidences.append(max(0.0, min(conf, 1.0)))

        return texts, confidences

    def parse_image(self, image_bytes: bytes, timezone: str, context_date: datetime | None = None, locale: str = "en") -> OCRParseResult:
        if not image_bytes:
            return OCRParseResult(timezone=timezone, errors=["No image data provided"])

        try:
            reader = self._get_reader(locale)
            read_result = reader.readtext(image_bytes)
        except Exception as exc:
            return OCRParseResult(timezone=timezone, errors=[f"OCR unavailable: {exc}"])

        texts, confidences = self._normalize_read_result(read_result)
        raw_text = " ".join(texts).strip()
        if not raw_text:
            return OCRParseResult(timezone=timezone, errors=["Could not extract readable text from image"], raw_text="")

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        nlp = NLPService()
        parsed = nlp.parse(raw_text, timezone, context_date, locale=locale)

        end_at = parsed.end_at
        if parsed.start_at and end_at is None:
            end_at = parsed.start_at + timedelta(hours=1)

        return OCRParseResult(
            title=parsed.title,
            start_at=parsed.start_at,
            end_at=end_at,
            timezone=timezone,
            confidence_title=min(parsed.confidence_title, avg_conf) if parsed.title else 0.0,
            confidence_date=min(parsed.confidence_date, avg_conf) if parsed.start_at else 0.0,
            confidence_raw=avg_conf,
            raw_text=raw_text,
            errors=parsed.errors,
        )