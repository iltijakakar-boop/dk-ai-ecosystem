import os
from typing import Any


class PromptTemplate:
    """
    Handles prompt templates, supporting loading from strings/files and formatting placeholders.
    """

    def __init__(self, template: str):
        self.template = template

    @classmethod
    def from_file(cls, filepath: str) -> "PromptTemplate":
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt template file not found: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return cls(content)

    def render(self, **kwargs: Any) -> str:
        """
        Safely renders the prompt template by substituting {variable_name} placeholders.
        """
        rendered = self.template
        for key, val in kwargs.items():
            rendered = rendered.replace(f"{{{key}}}", str(val))
        return rendered
