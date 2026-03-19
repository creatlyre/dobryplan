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
    ambiguous: bool = False          # True when year is uncertain (month/day without year)
    year_candidates: list[int] = field(default_factory=list)


class NLPService:
    """Parse natural language event descriptions into structured event data."""

    # Recurrence keywords (locale-keyed)
    FREQ_KEYWORDS = {
        "en": {
            r"\bdaily\b": "DAILY",
            r"\bevery\s+day\b": "DAILY",
            r"\bweekly\b": "WEEKLY",
            r"\bevery\s+week\b": "WEEKLY",
            r"\bmonthly\b": "MONTHLY",
            r"\bevery\s+month\b": "MONTHLY",
            r"\byearly\b": "YEARLY",
            r"\bevery\s+year\b": "YEARLY",
            r"\bfortnightly\b": "WEEKLY",
        },
        "pl": {
            r"\bcodziennie\b": "DAILY",
            r"\bco\s+dzie[\u0144n]\b": "DAILY",
            r"\bco\s+tydzie[\u0144n]\b": "WEEKLY",
            r"\btygodniowo\b": "WEEKLY",
            r"\bco\s+miesi[\u0105a]c\b": "MONTHLY",
            r"\bmiesi[\u0119e]cznie\b": "MONTHLY",
            r"\bco\s+rok\b": "YEARLY",
            r"\brocznie\b": "YEARLY",
        },
    }

    # Time keywords without explicit times (locale-keyed)
    TIME_DEFAULTS = {
        "en": {
            r"\bmorning\b": (9, 0),
            r"\bafternoon\b": (14, 0),
            r"\bevening\b": (18, 0),
            r"\bnight\b": (20, 0),
        },
        "pl": {
            r"\brano\b": (9, 0),
            r"\bpo\s+po[\u0142l]udniu\b": (14, 0),
            r"\bwiecz[o\u00f3]r(em)?\b": (18, 0),
            r"\bw\s+nocy\b": (20, 0),
        },
    }

    # Relative date keywords: word -> day offset from context_date
    RELATIVE_KEYWORDS = {
        "en": {"tomorrow": 1, "today": 0, "yesterday": -1},
        "pl": {"jutro": 1, "dzisiaj": 0, "dzi\u015b": 0, "dzis": 0, "wczoraj": -1},
    }

    # Weekday names: name -> weekday number (0=Monday)
    WEEKDAY_NAMES = {
        "en": {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        },
        "pl": {
            "poniedzia\u0142ek": 0, "poniedzialek": 0,
            "wtorek": 1,
            "\u015broda": 2, "sroda": 2, "\u015brod\u0119": 2, "srode": 2,
            "czwartek": 3,
            "pi\u0105tek": 4, "piatek": 4,
            "sobota": 5, "sobot\u0119": 5, "sobote": 5,
            "niedziela": 6, "niedziel\u0119": 6, "niedziele": 6,
        },
    }

    # Month names: name -> month number
    MONTH_NAMES = {
        "en": {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        },
        "pl": {
            "stycze\u0144": 1, "styczen": 1, "stycznia": 1,
            "luty": 2, "lutego": 2,
            "marzec": 3, "marca": 3,
            "kwiecie\u0144": 4, "kwiecien": 4, "kwietnia": 4,
            "maj": 5, "maja": 5,
            "czerwiec": 6, "czerwca": 6,
            "lipiec": 7, "lipca": 7,
            "sierpie\u0144": 8, "sierpien": 8, "sierpnia": 8,
            "wrzesie\u0144": 9, "wrzesien": 9, "wrze\u015bnia": 9,
            "pa\u017adziernik": 10, "pazdziernik": 10, "pa\u017adziernika": 10, "pazdziernika": 10,
            "listopad": 11, "listopada": 11,
            "grudzie\u0144": 12, "grudzien": 12, "grudnia": 12,
        },
    }

    # Modifier words (next/this/last)
    MODIFIER_WORDS = {
        "en": {"next": "next", "this": "this", "last": "last"},
        "pl": {
            "nast\u0119pny": "next", "nast\u0119pna": "next", "nast\u0119pne": "next",
            "nastepny": "next", "nastepna": "next", "nastepne": "next",
            "przysz\u0142y": "next", "przysz\u0142a": "next", "przysz\u0142e": "next",
            "przyszly": "next", "przyszla": "next", "przyszle": "next",
            "ten": "this", "ta": "this", "to": "this",
            "ostatni": "last", "ostatnia": "last", "ostatnie": "last",
            "poprzedni": "last", "poprzednia": "last",
        },
    }

    @staticmethod
    def _normalize_locale(locale: str) -> str:
        """Normalize locale string to supported parser locale."""
        loc = locale.lower().split("-")[0].split("_")[0]
        return loc if loc in ("pl", "en") else "en"

    def parse(
        self,
        text: str,
        user_timezone: str,
        context_date: Optional[datetime] = None,
        locale: str = "en",
    ) -> ParseResult:
        """
        Parse natural language text into structured event data.

        Args:
            text: Natural language event description
            user_timezone: User's timezone (e.g., "America/New_York")
            context_date: Reference date for relative parsing (defaults to today)
            locale: Language locale for keyword matching ("en" or "pl")

        Returns:
            ParseResult with title, dates, confidence scores, and any errors
        """
        locale = self._normalize_locale(locale)
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
        title = self._extract_title(text, locale)
        if not title:
            result.errors.append("No event title found in input")
            result.confidence_title = 0.0
            return result

        result.title = title

        recurrence = self._parse_recurrence(text, locale)

        # Parse dates and times
        parsed_dates = self._parse_dates(text, context_date, user_timezone, locale)

        if not parsed_dates.get("start_at"):
            # Allow recurrence-only input by anchoring to context date.
            if recurrence:
                hour, minute = self._extract_time_from_text(text, locale)
                start_at = context_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if start_at < context_date:
                    start_at = start_at + timedelta(days=1)
                parsed_dates = {
                    "start_at": start_at,
                    "end_at": start_at + timedelta(hours=1),
                    "confidence": 0.7,
                }
            else:
                if parsed_dates.get("error"):
                    result.errors.append(parsed_dates["error"])
                else:
                    result.errors.append("No date found in input")
                result.confidence_date = 0.0
                return result

        result.start_at = parsed_dates["start_at"]
        result.end_at = parsed_dates.get("end_at")
        result.confidence_date = parsed_dates.get("confidence", 1.0)
        result.ambiguous = parsed_dates.get("ambiguous", False)
        result.year_candidates = parsed_dates.get("year_candidates", [])

        # Parse recurrence
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

    def _extract_title(self, text: str, locale: str = "en") -> str:
        """Extract event title from text (first meaningful words)."""
        cleaned = text
        # Remove common date/time patterns to isolate title
        cleaned = re.sub(r"\b\d{4}-\d{1,2}-\d{1,2}\b", " ", cleaned)
        cleaned = re.sub(r"\b\d{1,2}/\d{1,2}/\d{4}\b", " ", cleaned)
        # Remove English filler words
        cleaned = re.sub(
            r"\b(at|on|in|this|next|last|tomorrow|today|yesterday)\b",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        # Remove Polish filler words
        if locale == "pl":
            cleaned = re.sub(
                r"\b(jutro|dzisiaj|dzi\u015b|dzis|wczoraj|o|w|na|za|co)\b",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            # Remove Polish modifiers
            pl_mods = "|".join(re.escape(m) for m in self.MODIFIER_WORDS["pl"])
            cleaned = re.sub(rf"\b({pl_mods})\b", "", cleaned, flags=re.IGNORECASE)
        # Remove time patterns
        cleaned = re.sub(
            r"\b(\d{1,2}(am|pm|AM|PM)?|\d{1,2}:\d{2}|morning|afternoon|evening|night)\b",
            "",
            cleaned,
        )
        if locale == "pl":
            cleaned = re.sub(
                r"\b(rano|wiecz[o\u00f3]r(em)?)\b|\bpo\s+po[\u0142l]udniu\b|\bw\s+nocy\b",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
        # Remove English month/weekday abbreviations
        cleaned = re.sub(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*\b", "", cleaned, flags=re.IGNORECASE)
        # Remove Polish month/weekday names
        if locale == "pl":
            pl_months = "|".join(re.escape(m) for m in self.MONTH_NAMES["pl"])
            cleaned = re.sub(rf"\b({pl_months})\b", "", cleaned, flags=re.IGNORECASE)
            pl_weekdays = "|".join(re.escape(w) for w in self.WEEKDAY_NAMES["pl"])
            cleaned = re.sub(rf"\b({pl_weekdays})\b", "", cleaned, flags=re.IGNORECASE)
            # Remove Polish recurrence keywords
            cleaned = re.sub(
                r"\b(codziennie|tygodniowo|miesi[\u0119e]cznie|rocznie)\b",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
        cleaned = re.sub(r"\b\d+\b", " ", cleaned)
        # Remove non-letter/non-space characters (Unicode-safe)
        cleaned = re.sub(r"[^\w\s]", " ", cleaned)
        cleaned = re.sub(r"[\d_]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Take first 1-3 words
        words = [w for w in cleaned.split() if w.strip()]
        title = " ".join(words[:3]).strip()

        return title if title else ""

    def _parse_dates(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
        locale: str = "en",
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
        result = self._parse_explicit_date(text, context_date, user_timezone, locale)
        if result.get("start_at"):
            return result
        if result.get("error"):
            return result

        # Try relative dates (tomorrow, next Friday, etc.)
        result = self._parse_relative_date(text, context_date, user_timezone, locale)
        if result.get("start_at"):
            return result
        if result.get("error"):
            return result

        # Try month/day patterns (March 15, December 25)
        result = self._parse_month_day(text, context_date, user_timezone, locale)
        if result.get("start_at"):
            return result
        if result.get("error"):
            return result

        # No date found
        return {"error": "No date found in input", "start_at": None}

    def _parse_explicit_date(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
        locale: str = "en",
    ) -> dict:
        """Parse explicit dates like '2026-04-10' or '15/03/2026'."""
        # Try ISO format
        iso_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
        if iso_match:
            try:
                year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                hour, minute = self._extract_time_from_text(text)
                start_at = datetime(year, month, day, hour, minute)
                if start_at < context_date.replace(hour=0, minute=0, second=0, microsecond=0):
                    return {
                        "error": f"Date is in the past: {start_at.date()}",
                        "start_at": None,
                    }
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
                hour, minute = self._extract_time_from_text(text)
                start_at = datetime(year, month, day, hour, minute)
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
        languages = [locale] if locale == "en" else [locale, "en"]
        parsed = dateparser.parse(
            text,
            languages=languages,
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
        locale: str = "en",
    ) -> dict:
        """Parse relative dates like 'tomorrow', 'next Friday', 'in 3 days'."""
        text_lower = text.lower()

        # Check relative keywords (tomorrow/today/yesterday and locale equivalents)
        merged_rel = {**self.RELATIVE_KEYWORDS.get("en", {}), **self.RELATIVE_KEYWORDS.get(locale, {})}
        for keyword, offset in merged_rel.items():
            if keyword in text_lower:
                if offset < 0:
                    target = context_date + timedelta(days=offset)
                    if target < context_date.replace(hour=0, minute=0, second=0, microsecond=0):
                        return {"error": "Date is in the past", "start_at": None}
                    return self._build_date_result(target, text, context_date, locale)
                target = context_date + timedelta(days=offset)
                return self._build_date_result(target, text, context_date, locale)

        # Modifier + weekday (next Monday / następny poniedziałek)
        weekdays = {**self.WEEKDAY_NAMES.get("en", {}), **self.WEEKDAY_NAMES.get(locale, {})}
        modifiers = {**self.MODIFIER_WORDS.get("en", {}), **self.MODIFIER_WORDS.get(locale, {})}
        modifier_pattern = "|".join(re.escape(m) for m in modifiers)
        weekday_pattern = "|".join(re.escape(w) for w in weekdays)

        day_match = re.search(
            rf"\b({modifier_pattern})\s+({weekday_pattern})\b",
            text_lower,
        )
        if day_match:
            mod_word = day_match.group(1)
            day_name = day_match.group(2)
            modifier = modifiers[mod_word]
            target_date = self._find_day_of_week(context_date, day_name, modifier, locale)
            return self._build_date_result(target_date, text, context_date, locale)

        # Plain weekday name
        plain_day_match = re.search(
            rf"\b({weekday_pattern})\b",
            text_lower,
        )
        if plain_day_match:
            day_name = plain_day_match.group(1)
            target_date = self._find_day_of_week(context_date, day_name, "this", locale)
            return self._build_date_result(target_date, text, context_date, locale)

        # "in N days" / "za N dni"
        in_days_match = re.search(r"\bza\s+(\d+)\s+dn", text_lower) or re.search(r"\bin\s+(\d+)\s+day", text_lower)
        if in_days_match:
            days = int(in_days_match.group(1))
            target_date = context_date + timedelta(days=days)
            return self._build_date_result(target_date, text, context_date, locale)

        return {}

    def _parse_month_day(
        self,
        text: str,
        context_date: datetime,
        user_timezone: str,
        locale: str = "en",
    ) -> dict:
        """Parse month/day patterns like 'March 15' or '15 marca'."""
        months = {**self.MONTH_NAMES.get("en", {}), **self.MONTH_NAMES.get(locale, {})}
        text_lower = text.lower()

        for month_name, month_num in months.items():
            escaped = re.escape(month_name)
            # "Month DD" pattern (English-style)
            match = re.search(rf"\b{escaped}\s+(\d{{1,2}})\b", text_lower)
            if not match:
                # "DD Month" pattern (Polish-style: 15 marca)
                match = re.search(rf"\b(\d{{1,2}})\s+{escaped}\b", text_lower)
            if match:
                day = int(match.group(1))
                try:
                    current_year_date = datetime(context_date.year, month_num, day, 9, 0)
                    if current_year_date >= context_date:
                        return {
                            "start_at": current_year_date,
                            "end_at": current_year_date + timedelta(hours=1),
                            "confidence": 0.85,
                            "ambiguous": True,
                            "year_candidates": [context_date.year, context_date.year + 1],
                        }
                    else:
                        next_year_date = datetime(context_date.year + 1, month_num, day, 9, 0)
                        return {
                            "start_at": next_year_date,
                            "end_at": next_year_date + timedelta(hours=1),
                            "confidence": 0.85,
                        }
                except ValueError:
                    return {"error": f"Invalid day for {month_name}: {day}", "start_at": None}
        return {}

    def _find_day_of_week(
        self,
        context_date: datetime,
        day_name: str,
        modifier: str,
        locale: str = "en",
    ) -> datetime:
        """Find the next/this/last occurrence of a day of week."""
        days_of_week = {**self.WEEKDAY_NAMES.get("en", {}), **self.WEEKDAY_NAMES.get(locale, {})}

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
        locale: str = "en",
    ) -> dict:
        """Build a date result with extracted time."""
        hour, minute = self._extract_time_from_text(text, locale)

        start_at = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Check if past
        if start_at < context_date:
            return {"error": f"Date is in the past: {start_at.date()}", "start_at": None}

        end_at = start_at + timedelta(hours=1)
        return {"start_at": start_at, "end_at": end_at, "confidence": 0.95}

    def _extract_time_from_text(self, text: str, locale: str = "en") -> tuple[int, int]:
        """Extract explicit clock time; return default 09:00 when no explicit time exists."""
        hour, minute = 9, 0

        # Prefer explicit HH:MM time first.
        colon_match = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", text, re.IGNORECASE)
        if colon_match:
            hour = int(colon_match.group(1))
            minute = int(colon_match.group(2))
            am_pm = colon_match.group(3)
            if am_pm and am_pm.lower() == "pm" and hour < 12:
                hour += 12
            elif am_pm and am_pm.lower() == "am" and hour == 12:
                hour = 0
            return hour, minute

        # Only treat bare hour as time when am/pm is present.
        ampm_match = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text, re.IGNORECASE)
        if ampm_match:
            hour = int(ampm_match.group(1))
            am_pm = ampm_match.group(2)
            if am_pm.lower() == "pm" and hour < 12:
                hour += 12
            elif am_pm.lower() == "am" and hour == 12:
                hour = 0
            return hour, minute

        # Polish "o HH" pattern (e.g., "o 14" = at 14:00)
        if locale == "pl":
            o_match = re.search(r"\bo\s+(\d{1,2})\b", text.lower())
            if o_match:
                h = int(o_match.group(1))
                if 0 <= h <= 23:
                    return h, 0

        # Semantic time keywords (locale-keyed, merged with English fallback)
        text_lower = text.lower()
        merged_time = {**self.TIME_DEFAULTS.get("en", {}), **self.TIME_DEFAULTS.get(locale, {})}
        for pattern, (keyword_hour, keyword_minute) in merged_time.items():
            if re.search(pattern, text_lower):
                return keyword_hour, keyword_minute

        return hour, minute

    def _parse_recurrence(self, text: str, locale: str = "en") -> Optional[dict]:
        """Parse recurrence patterns like 'every Friday' or 'daily for 10 times'."""
        text_lower = text.lower()

        # Interval pattern: "every N weeks" / "co N tygodni"
        interval_match = re.search(r"\bco\s+(\d+)\s+(dn|tydz|miesi[\u0105a]c|rok|lat)", text_lower) or \
                         re.search(r"every\s+(\d+)\s+(week|day|month|year)[s]?", text_lower)
        if interval_match:
            interval = int(interval_match.group(1))
            freq_word = interval_match.group(2)
            freq_map = {"dn": "DAILY", "tydz": "WEEKLY", "miesi": "MONTHLY",
                        "miesi\u0105": "MONTHLY", "rok": "YEARLY", "lat": "YEARLY",
                        "day": "DAILY", "week": "WEEKLY", "month": "MONTHLY", "year": "YEARLY"}
            matched_freq = None
            for key, val in freq_map.items():
                if freq_word.startswith(key):
                    matched_freq = val
                    break
            if matched_freq:
                recurrence = {"freq": matched_freq}
                if interval > 1:
                    recurrence["interval"] = interval
                return recurrence

        # "every weekday" / "co poniedzia\u0142ek"
        weekdays = {**self.WEEKDAY_NAMES.get("en", {}), **self.WEEKDAY_NAMES.get(locale, {})}
        weekday_pattern = "|".join(re.escape(w) for w in weekdays)
        weekday_every_match = re.search(
            rf"\bco\s+({weekday_pattern})\b|\bka\u017cd[y\u0105a]\s+({weekday_pattern})\b|\bkazd[yaa]\s+({weekday_pattern})\b|\bevery\s+({weekday_pattern})\b",
            text_lower,
        )
        if weekday_every_match:
            return {"freq": "WEEKLY"}

        # Check for frequency keywords (both locale and English)
        freq = None
        merged_freq = {**self.FREQ_KEYWORDS.get("en", {}), **self.FREQ_KEYWORDS.get(locale, {})}
        for pattern, freq_value in merged_freq.items():
            if re.search(pattern, text_lower):
                freq = freq_value
                break

        if not freq:
            return None

        # Extract COUNT if present
        count = None
        count_match = re.search(r"\b(\d+)\s+(raz[y\u00f3w]*|powt\u00f3rze[\u0144n])", text_lower) or \
                      re.search(r"\b(\d+)\s+(times|occasions)\b", text_lower)
        if count_match:
            count = int(count_match.group(1))

        result = {"freq": freq}
        if count:
            result["count"] = count

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
