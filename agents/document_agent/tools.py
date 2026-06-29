from ai.tools.base_tool import BaseTool
from typing import Any, Dict


class DocumentParserTool(BaseTool):
    """
    Parses document raw text content.
    """

    @property
    def tool_id(self) -> str:
        return "document_parser"

    @property
    def name(self) -> str:
        return "document_parser"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Extracts metrics, summaries, word/character count, and info from document text."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Raw string text extracted from pdf/word document.",
                }
            },
            "required": ["text"],
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        text = kwargs.get("text", "")
        if not text:
            return {"valid": False, "error": "No text content provided."}

        word_count = len(text.split())
        summary = text[:100] + "..." if len(text) > 100 else text

        return {
            "success": True,
            "character_count": len(text),
            "word_count": word_count,
            "preview_summary": summary,
        }
