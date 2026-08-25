import json
import logging
import re
from html import escape
from html.parser import HTMLParser
from typing import Any

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger(__name__)


class ArtifactArguments(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    format: str = Field(pattern="^(markdown|html)$")
    content: str = Field(min_length=1, max_length=100_000)


class _SafeHTMLParser(HTMLParser):
    allowed_tags = {
        "a", "article", "b", "blockquote", "body", "br", "code", "div", "em",
        "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "html", "i",
        "li", "main", "ol", "p", "pre", "section", "small", "span", "strong",
        "style", "title", "ul",
    }
    void_tags = {"br"}
    allowed_attributes = {"class", "id", "title", "aria-label", "href"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "iframe", "object", "embed", "form", "meta", "link"}:
            self.skip_depth += 1
            return
        if self.skip_depth or tag not in self.allowed_tags:
            return
        safe_attrs = []
        for name, value in attrs:
            name = name.lower()
            if name not in self.allowed_attributes or value is None:
                continue
            if name == "href" and not re.match(r"^(https?://|mailto:|#)", value, re.I):
                continue
            safe_attrs.append(f' {name}="{escape(value, quote=True)}"')
        self.output.append(f"<{tag}{''.join(safe_attrs)}>")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "iframe", "object", "embed", "form", "meta", "link"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if not self.skip_depth and tag in self.allowed_tags and tag not in self.void_tags:
            self.output.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.output and self.output[-1] == "<style>":
            data = re.sub(r"(?i)(url\s*\(|expression\s*\(|@import|javascript:)", "", data)
        self.output.append(data)


class ArtifactTool:
    """Create a frontend-ready Markdown or sanitized HTML artifact."""

    name = "create_artifact"
    description = (
        "Create a Markdown or safe HTML artifact from grounded conversation content. "
        "Use for documents or webpages; generated HTML is sanitized before return."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "format": {"type": "string", "enum": ["markdown", "html"]},
            "content": {"type": "string", "minLength": 1, "maxLength": 100000},
        },
        "required": ["title", "format", "content"],
    }

    async def create(self, arguments: dict[str, Any]) -> dict:
        try:
            parsed = ArtifactArguments.model_validate(arguments)
        except ValidationError as exc:
            logger.warning("Invalid artifact arguments")
            return self._result({"error": "invalid_arguments", "details": exc.errors()})

        if parsed.format == "markdown":
            artifact = parsed.content
            content_type = "text/markdown"
        else:
            artifact = self._sanitize_html(parsed.content)
            if "<html" not in artifact.lower():
                artifact = (
                    "<!doctype html><html><head><meta charset=\"utf-8\"></head>"
                    f"<body>{artifact}</body></html>"
                )
            content_type = "text/html"
        logger.info("Artifact created: format=%s chars=%d", parsed.format, len(artifact))
        return self._result({
            "title": parsed.title,
            "format": parsed.format,
            "content_type": content_type,
            "content": artifact,
            "safe_for_preview": parsed.format == "html",
        })

    @staticmethod
    def _sanitize_html(content: str) -> str:
        parser = _SafeHTMLParser()
        parser.feed(content)
        parser.close()
        return "".join(parser.output)

    @staticmethod
    def _result(payload: dict) -> dict:
        return {"content": [{"type": "text", "text": json.dumps(payload)}]}
