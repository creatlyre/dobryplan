"""NLP Service for parsing natural language event descriptions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

import dateparser

from app.events.recurrence import validate_rrule


@dataclass
class ParseResult:
    """Result of parsing natural language event text."""

    title: str = ""
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    confidence_date: float = 1.0  # 0.0-1.0
    confidence_title: float = 1.0  # 0.0-1.0
    recurrence: Optional[dict] = None  # e.g., {"freq": "WEEKLY", "count": 10}
    errors: list[str] = field(default_factory=list)
    raw_text: str = ""


class NLPService:
    """Parse natural language event descriptions into structured event data."""

    # Recurrence keywords
    FREQ_KEYWORDS = {
        r"\bdaily\b": "DAILY",
        r"\bevery\s+day\b": "DAILY",
        r"\bweekly\b": "WEEKLY",
        r"\bevery\s+week\b": "WEEKLY",
        r"\bmonthly\b": "MONTHLY",
        r"\bevery\s+month\b": "MONTHLY",
        r"\byearly\b": "YEARLY",
        r"\bevery\s+year\b": "YEARLY",
        r"\bfortnightly\b": "WEEKLY",  # every 2 weeks
    }

    # Time keywords without explicit times
    TIME_DEFAULTS = {
        r"\bmorning\b": (9, 0),
        r"\bafternoon\b": (14, 0),
        r"\bevening\b": (18, 0),
        r"\bnight\b": (20, 0),
    }

    def parse(
        self,
        text: str,
        user_timezone: str,
        context_date: Optional[datetime] = None,
    ) -> ParseResult:
        """
        Parse natural language text into structured event data.

        Args:
            text: Natural language event description
            user_timezone: User's timezone (e.g., "America/New_York")
            context_date: Reference date for relative parsing (defaults to today)

        Returns:
            ParseResult with title, dates, confidence scores, and any errors
        """
        if not text or not text.strip():
            return ParseResult(
                raw_text=text,
                errors=["Input text is empty"],
            )

        text = text.strip()
        if context_date is None:
            context_date = datetime.now()

        # Initialize result
        result = ParseResult(raw_text=text)

        # Extract title (rough heuristic: first 2-3 words if no time components)
        title = self._extract_title(text)
        if not title:
            result.errors.append("No event title found in input")
            result.confidence_title = 0.0
            return result

        result.title = title

        # Parse dates and times
        parsed_dates = self._parse_dates(text, context_date, user_timezone)

        if not parsed_dates.get("start_at"):
            if parsed_dates.get("error"):
                result.errors.append(parsed_dates["error"])
            else:
                result.errors.append("No date found in input")
            result.confidence_date = 0.0
            return result

        result. start_at = parsed_dates["start_at"]
        result.end_at = parsed_dates.get("end_at")
        result.confidence_date = parsed_dates.get("confidence", 1.0)

        # Parse recurrence
        recurrence = self._parse_recurrence(text)
        if recurrence:
            result.recurrence = recurrence
            # Validate RRULE if we have a start_at
            if result.start_at:
                try:
                    rrule_str = self._build_rrule_string(
                        recurrence, result.start_at
                    )
                    validate_rrule(rrule_str, result.start_at)
                except ValueError as e:
                    result.errors.append(f"Invalid recurrence: {str(e)}")
                    result.recurrence = None

        return result

    def _extract_title(self, text: str) -> str:
        """Extract event title from text (first meaningful words)."""
        # Remove common date/time patterns to isolate title
        cleaned = text
        cleaned = re.sub(
            r"\b(at|on|in|this|next|last|tomorrow|today|yesterday)\b",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\b(\d{1,2}(am|pm|AM|PM)?|\d{1,2}:\d{2}|morning|afternoon|evening|night)\b",
            "",
            cleaned,
        )
        cleaned = re.sub(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b", "", cleaned, flags=re.IGNORECASE)

        # Take first 1-3 words
        words = [w for w in cleaned.split() if w.strip()]
        title = " ".join(words[:3]).strip()

        return title if title else ""

    def _parse_dates(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
    ) -> dict:
        """
        Parse date and time from text.

        Returns dict with:
            start_at: parsed start datetime or None
            end_at: parsed end datetime or None
            confidence: 0.0-1.0
            error: error message if parsing failed
        """
        # Try to extract explicit date patterns first
        result = self._parse_explicit_date(text, context_date, user_timezone)
        if result.get("start_at"):
            return result

        # Try relative dates (tomorrow, next Friday, etc.)
        result = self._parse_relative_date(text, context_date, user_timezone)
        if result.get("start_at"):
            return result

        # Try month/day patterns (March 15, December 25)
        result = self._parse_month_day(text, context_date, user_timezone)
        if result.get("start_at"):
            return result

        # No date found
        return {"error": "No date found in input", "start_at": None}

    def _parse_explicit_date(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
    ) -> dict:
        """Parse explicit dates like '2026-04-10' or '15/03/2026'."""
        # Try ISO format
        iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if iso_match:
            try:
                year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                start_at = datetime(year, month, day, 9, 0)  # Default 09:00
                end_at = start_at + timedelta(hours=1)
                return {
                    "start_at": start_at,
                    "end_at": end_at,
                    "confidence": 1.0,
                }
            except ValueError:
                pass

        # Try DD/MM/YYYY (fixed per CONTEXT decision)
        ddmmyyyy_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
        if ddmmyyyy_match:
            try:
                day, month, year = int(ddmmyyyy_match.group(1)), int(ddmmyyyy_match.group(2)), int(ddmmyyyy_match.group(3))
                start_at = datetime(year, month, day, 9, 0)  # Default 09:00
                # Check if past
                if start_at < context_date.replace(hour=0, minute=0, second=0, microsecond=0):
                    return {
                        "error": f"Date is in the past: {start_at.date()}",
                        "start_at": None,
                    }
                end_at = start_at + timedelta(hours=1)
                return {
                    "start_at": start_at,
                    "end_at": end_at,
                    "confidence": 0.95,  # Fixed DD/MM interpretation, slightly uncertain
                }
            except ValueError as e:
                return {"error": f"Invalid date format: {e}", "start_at": None}

        # Use dateparser for other formats
        parsed = dateparser.parse(
            text,
            settings={
                "TIMEZONE": user_timezone,
                "RETURN_AS_TIMEZONE_AWARE": False,
                "PREFER_DATES_FROM": "future",
            },
        )

        if parsed:
            # Check if in past
            if parsed < context_date:
                return {
                    "error": f"Date is in the past: {parsed.date()}",
                    "start_at": None,
                }
            end_at = parsed + timedelta(hours=1)
            return {"start_at": parsed, "end_at": end_at, "confidence": 0.9}

        return {}

    def _parse_relative_date(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
    ) -> dict:
        """Parse relative dates like 'tomorrow', 'next Friday', 'in 3 days'."""
        text_lower = text.lower()

        # Tomorrow
        if "tomorrow" in text_lower:
            tomorrow = context_date + timedelta(days=1)
            return self._build_date_result(tomorrow, text, context_date)

        # Today
        if "today" in text_lower:
            return self._build_date_result(context_date, text, context_date)

        # Yesterday (might be past)
        if "yesterday" in text_lower:
            yesterday = context_date - timedelta(days=1)
            if yesterday < context_date.replace(hour=0, minute=0, second=0, microsecond=0):
                return {"error": "Date is in the past", "start_at": None}
            return self._build_date_result(yesterday, text, context_date)

        # Next/This/Last + day of week
        day_match = re.search(
            r"\b(next|this|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
            text_lower,
        )
        if day_match:
            modifier = day_match.group(1)
            day_name = day_match.group(2)
            target_date = self._find_day_of_week(context_date, day_name, modifier)
            return self._build_date_result(target_date, text, context_date)

        # "in N days"
        in_days_match = re.search(r"\bin\s+(\d+)\s+day", text_lower)
        if in_days_match:
            days = int(in_days_match.group(1))
            target_date = context_date + timedelta(days=days)
            return self._build_date_result(target_date, text, context_date)

        return {}

    def _parse_month_day(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
    ) -> dict:
        """Parse month/day patterns like 'March 15' or 'December 25'."""
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        text_lower = text.lower()

        # Month + day pattern
        for month_name, month_num in months.items():
            month_pattern = rf"\b{month_name}\s+(\d{{1,2}})\b"
            match = re.search(month_pattern, text_lower)
            if match:
                day = int(match.group(1))
                try:
                    # Try current year first
                    target_date = datetime(context_date.year, month_num, day, 9, 0)
                    if target_date < context_date:
                        # Try next year
                        target_date = datetime(context_date.year + 1, month_num, day, 9, 0)
                    return {
                        "start_at": target_date,
                        "end_at": target_date + timedelta(hours=1),
                        "confidence": 0.85,  # Month/day without year is slightly uncertain
                    }
                except ValueError:
                    return {"error": f"Invalid day for {month_name}: {day}", "start_at": None}

        return {}

    def _find_day_of_week(
        self,
        context_date: datetime,
        day_name: str,
        modifier: str,
    ) -> datetime:
        """Find the next/this/last occurrence of a day of week."""
        days_of_week = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        target_dow = days_of_week.get(day_name, -1)
        if target_dow == -1:
            return context_date

        current_dow = context_date.weekday()
        days_ahead = (target_dow - current_dow) % 7

        if modifier == "next":
            if days_ahead == 0:
                days_ahead = 7  # Next occurrence, not today
        elif modifier == "last":
            if days_ahead == 0:
                days_ahead = 0  # Last occurrence was today
            else:
                days_ahead = days_ahead - 7  # Go back to previous week
        # "this" = use days_ahead as-is (could be 0 if today is that day)

        return context_date + timedelta(days=days_ahead)

    def _build_date_result(
        self,
        target_date: datetime,
        text: str,
        context_date: datetime,
    ) -> dict:
        """Build a date result with extracted time."""
        # Extract time if present
        time_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text, re.IGNORECASE)
        hour, minute = 9, 0  # Default time

        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            am_pm = time_match.group(3)

            if am_pm and am_pm.lower() == "pm" and hour < 12:
                hour += 12
            elif am_pm and am_pm.lower() == "am" and hour == 12:
                hour = 0

        start_at = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Check if past
        if start_at < context_date:
            return {"error": f"Date is in the past: {start_at.date()}", "start_at": None}

        end_at = start_at + timedelta(hours=1)
        return {"start_at": start_at, "end_at": end_at, "confidence": 0.95}

    def _parse_recurrence(self, text: str) -> Optional[dict]:
        """Parse recurrence patterns like 'every Friday' or 'daily for 10 times'."""
        text_lower = text.lower()

        # Check for frequency keywords
        freq = None
        for pattern, freq_value in self.FREQ_KEYWORDS.items():
            if re.search(pattern, text_lower):
                freq = freq_value
                break

        if not freq:
            return None

        # Extract COUNT if present (e.g., "10 times", "10 occasions")
        count = None
        count_match = re.search(r"\b(\d+)\s+(times|occasions)\b", text_lower)
        if count_match:
            count = int(count_match.group(1))

        # Extract interval (e.g., "every 2 weeks")
        interval = 1
        interval_match = re.search(r"every\s+(\d+)\s+(week|day|month|year)[s]?", text_lower)
        if interval_match:
            interval = int(interval_match.group(1))
            freq_word = interval_match.group(2)
            freq_map = {
                "day": "DAILY",
                "week": "WEEKLY",
                "month": "MONTHLY",
                "year": "YEARLY",
            }
            freq = freq_map.get(freq_word, freq)

        result = {"freq": freq}
        if count:
            result["count"] = count
        if interval > 1:
            result["interval"] = interval

        return result

    def _build_rrule_string(self, recurrence: dict, dtstart: datetime) -> str:
        """Build RFC5545 RRULE string from parsed recurrence dict."""
        parts = [f"DTSTART:{dtstart.isoformat()}", f"FREQ={recurrence['freq']}"]

        if recurrence.get("interval", 1) > 1:
            parts.append(f"INTERVAL={recurrence['interval']}")

        if recurrence.get("count"):
            parts.append(f"COUNT={recurrence['count']}")

        if recurrence.get("until"):
            parts.append(f"UNTIL={recurrence['until']}")

        return ";".join(parts[1:])  # Skip DTSTART for RRULE format
