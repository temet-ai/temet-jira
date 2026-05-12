"""Base classes for ADF nodes and marks."""

from abc import ABC, abstractmethod
from typing import Any


class Mark(ABC):
    """Base class for ADF text marks (formatting)."""

    @property
    @abstractmethod
    def type(self) -> str:
        """The mark type identifier."""
        ...

    def to_adf(self) -> dict[str, Any]:
        """Convert mark to ADF dictionary representation."""
        result: dict[str, Any] = {"type": self.type}
        attrs = self._get_attrs()
        if attrs:
            result["attrs"] = attrs
        return result

    def _get_attrs(self) -> dict[str, Any] | None:
        """Get mark attributes. Override in subclasses with attributes."""
        return None


class Node(ABC):
    """Base class for ADF nodes."""

    @property
    @abstractmethod
    def type(self) -> str:
        """The node type identifier."""
        ...

    @abstractmethod
    def to_adf(self) -> dict[str, Any]:
        """Convert node to ADF dictionary representation."""
        ...

    def _build_content(self, children: tuple[Any, ...]) -> list[dict[str, Any]]:
        """Build content array from child nodes."""
        content: list[dict[str, Any]] = []
        for child in children:
            if isinstance(child, Node):
                content.append(child.to_adf())
            elif isinstance(child, dict):
                content.append(child)
            elif isinstance(child, str):
                # Auto-wrap strings in Text nodes
                from temet_jira.document.nodes.inline import Text

                content.append(Text(child).to_adf())
        return content


class BlockNode(Node):
    """Base class for block-level nodes (paragraph, heading, etc.)."""

    pass


class InlineNode(Node):
    """Base class for inline nodes (text, emoji, mention, etc.)."""

    pass
