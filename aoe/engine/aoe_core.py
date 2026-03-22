"""Minimal AOE core scaffold.

This file is a starting point for implementing the LLM+DB resolver described
in the architecture doc. Keep this light — it should expose a simple API like
`create_object` and `resolve_action` used by the rest of the system.
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class MaterialData:
    composition: Dict[str, float]
    properties: Dict[str, Any]


class AOEEngine:
    """Core resolver for material composition and derived properties."""

    def __init__(self, chemistry_db=None, llm_client=None):
        self.chemistry_db = chemistry_db
        self.llm_client = llm_client

    def create_object(self, description: str) -> MaterialData:
        """Resolve a natural language `description` to MaterialData.

        This should call an LLM (or rule-based resolver) plus the chemistry DB
        to produce `composition` and `properties`.
        """
        # placeholder: real implementation will query LLM and chemistry DB
        composition = {"iron": 1.0} if "iron" in description else {"unknown": 1.0}
        properties = {"density": 7.8}  # example
        return MaterialData(composition=composition, properties=properties)

    def resolve_action(self, action: str, subject: Any, **kwargs) -> MaterialData:
        """Resolve an action (heat/combine/strike) into new MaterialData.

        This is where AOE applies transformations (e.g., Fe + C + heat -> steel).
        """
        # placeholder behavior
        return self.create_object(subject if isinstance(subject, str) else str(subject))
