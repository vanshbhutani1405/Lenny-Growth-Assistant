import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from app.observability.tracing import traced

logger = logging.getLogger(__name__)


class Ship30ValidationArguments(BaseModel):
    draft: str = Field(min_length=1, max_length=30_000)
    redraft_attempt: int = Field(default=0, ge=0, le=1)


class Ship30Tool:
    """Validate one Ship 30 draft and enforce at most one corrective redraft."""

    name = "validate_ship30_draft"
    description = (
        "Validate a Ship 30 for 30 essay draft for length, structure, and style. "
        "Invoke after drafting and redraft at most once if validation fails."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "draft": {"type": "string", "minLength": 1, "maxLength": 30000},
            "redraft_attempt": {"type": "integer", "minimum": 0, "maximum": 1},
        },
        "required": ["draft"],
    }

    @traced("agent.tool.validate_ship30_draft", run_type="tool")
    async def validate(self, arguments: dict[str, Any]) -> dict:
        try:
            parsed = Ship30ValidationArguments.model_validate(arguments)
        except ValidationError as exc:
            logger.warning("Invalid Ship 30 validation arguments")
            return self._result({"error": "invalid_arguments", "details": exc.errors()})

        draft = parsed.draft.strip()
        words = re.findall(r"\b[\w’'-]+\b", draft)
        headings = re.findall(r"(?m)^#{1,6}\s+\S+", draft)
        bullets = re.findall(r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)", draft)
        bold = re.findall(r"\*\*[^*]+\*\*|__[^_]+__", draft)
        issues: list[str] = []
        if not 900 <= len(words) <= 1500:
            issues.append("word_count must be between 900 and 1500")
        if len(headings) < 2:
            issues.append("include at least two Markdown headings")
        if not bullets:
            issues.append("include at least one bullet list")
        if not bold:
            issues.append("include selective bold emphasis")
        if len(draft.split()) < 25:
            issues.append("include a clear opening hook")

        valid = not issues
        result = {
            "valid": valid,
            "word_count": len(words),
            "heading_count": len(headings),
            "bullet_count": len(bullets),
            "bold_emphasis_count": len(bold),
            "issues": issues,
            "redraft_attempt": parsed.redraft_attempt,
            "redraft_allowed": not valid and parsed.redraft_attempt == 0,
        }
        logger.info(
            "Ship 30 draft validated: valid=%s words=%d redraft_attempt=%d",
            valid,
            len(words),
            parsed.redraft_attempt,
        )
        return self._result(result)

    @staticmethod
    def _result(payload: dict) -> dict:
        import json

        return {"content": [{"type": "text", "text": json.dumps(payload)}]}
