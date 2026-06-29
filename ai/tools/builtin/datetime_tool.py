from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List
import re
from ai.tools.base_tool import BaseTool


class DateTimeTool(BaseTool):
    """
    Built-in tool for date, time, and timezone utilities.
    """

    @property
    def tool_id(self) -> str:
        return "datetime"

    @property
    def name(self) -> str:
        return "Date & Time Utility"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Provides the current date, current time, and handles timezone offset conversions."

    @property
    def category(self) -> str:
        return "utility"

    @property
    def tags(self) -> List[str]:
        return ["time", "date", "timezone"]

    @property
    def permissions(self) -> List[str]:
        return []

    @property
    def timeout(self) -> int:
        return 2

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["current_time", "convert_timezone"],
                    "description": "The date-time operation.",
                },
                "timezone_offset": {
                    "type": "string",
                    "description": "UTC offset string, e.g. '+05:30' or '-08:00' (default is '+00:00').",
                },
                "datetime_str": {
                    "type": "string",
                    "description": "ISO datetime string (e.g. '2026-06-29T22:00:00') required for conversion.",
                },
                "target_offset": {
                    "type": "string",
                    "description": "Target UTC offset string, e.g. '+05:30' or '-08:00' (required for conversion).",
                },
            },
            "required": ["action"],
        }

    def _parse_offset(self, offset_str: str) -> timedelta:
        """Parses offsets like +05:30 or -08:00 into timedelta."""
        match = re.match(r"^([+-])(\d{2}):(\d{2})$", offset_str.strip())
        if not match:
            raise ValueError(
                f"Invalid timezone offset format: '{offset_str}'. Use '+HH:MM' or '-HH:MM'."
            )

        sign, hours, minutes = match.groups()
        total_minutes = int(hours) * 60 + int(minutes)
        if sign == "-":
            total_minutes = -total_minutes
        return timedelta(minutes=total_minutes)

    def execute(self, **kwargs) -> Dict[str, Any]:
        action = kwargs.get("action")
        offset_str = kwargs.get("timezone_offset", "+00:00")
        datetime_str = kwargs.get("datetime_str", "")
        target_offset_str = kwargs.get("target_offset", "")

        try:
            if action == "current_time":
                offset = self._parse_offset(offset_str)
                tz = timezone(offset)
                now = datetime.now(tz)
                return {
                    "success": True,
                    "formatted": now.strftime("%Y-%m-%d %H:%M:%S %z"),
                    "iso": now.isoformat(),
                    "date": now.strftime("%Y-%m-%d"),
                    "time": now.strftime("%H:%M:%S"),
                }

            elif action == "convert_timezone":
                if not datetime_str or not target_offset_str:
                    return {
                        "success": False,
                        "error": "Parameters 'datetime_str' and 'target_offset' are required for conversion.",
                    }

                # Parse inputs
                source_offset = self._parse_offset(offset_str)
                source_tz = timezone(source_offset)

                # Try parsing standard ISO strings
                try:
                    dt = datetime.fromisoformat(datetime_str)
                except ValueError:
                    # Try fallback formats
                    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")

                # If naive, attach source timezone
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=source_tz)

                target_offset = self._parse_offset(target_offset_str)
                target_tz = timezone(target_offset)
                converted_dt = dt.astimezone(target_tz)

                return {
                    "success": True,
                    "original": dt.isoformat(),
                    "converted_iso": converted_dt.isoformat(),
                    "converted_formatted": converted_dt.strftime(
                        "%Y-%m-%d %H:%M:%S %z"
                    ),
                }
            else:
                return {"success": False, "error": f"Invalid action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
