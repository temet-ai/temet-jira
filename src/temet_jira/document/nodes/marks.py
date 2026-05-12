"""ADF mark types for text formatting."""

from typing import Any, Literal

from temet_jira.document.nodes.base import Mark


class Strong(Mark):
    """Bold text formatting."""

    @property
    def type(self) -> str:
        return "strong"


class Em(Mark):
    """Italic/emphasis text formatting."""

    @property
    def type(self) -> str:
        return "em"


class Code(Mark):
    """Inline code formatting."""

    @property
    def type(self) -> str:
        return "code"


class Strike(Mark):
    """Strikethrough text formatting."""

    @property
    def type(self) -> str:
        return "strike"


class Underline(Mark):
    """Underlined text formatting."""

    @property
    def type(self) -> str:
        return "underline"


class Link(Mark):
    """Hyperlink mark."""

    def __init__(
        self,
        href: str,
        title: str | None = None,
    ) -> None:
        self.href = href
        self.title = title

    @property
    def type(self) -> str:
        return "link"

    def _get_attrs(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"href": self.href}
        if self.title:
            attrs["title"] = self.title
        return attrs


class TextColor(Mark):
    """Text color formatting."""

    def __init__(self, color: str) -> None:
        """Initialize text color mark.

        Args:
            color: Hex color code (e.g., "#ff0000")
        """
        if not color.startswith("#"):
            raise ValueError("Color must be a hex code starting with #")
        self.color = color

    @property
    def type(self) -> str:
        return "textColor"

    def _get_attrs(self) -> dict[str, Any]:
        return {"color": self.color}


class BackgroundColor(Mark):
    """Background color formatting."""

    def __init__(self, color: str) -> None:
        """Initialize background color mark.

        Args:
            color: Hex color code (e.g., "#ffff00")
        """
        if not color.startswith("#"):
            raise ValueError("Color must be a hex code starting with #")
        self.color = color

    @property
    def type(self) -> str:
        return "backgroundColor"

    def _get_attrs(self) -> dict[str, Any]:
        return {"color": self.color}


class Subsup(Mark):
    """Subscript or superscript text formatting."""

    def __init__(self, position: Literal["sub", "sup"]) -> None:
        """Initialize subscript/superscript mark.

        Args:
            position: Either "sub" for subscript or "sup" for superscript
        """
        if position not in ("sub", "sup"):
            raise ValueError("Position must be 'sub' or 'sup'")
        self.position = position

    @property
    def type(self) -> str:
        return "subsup"

    def _get_attrs(self) -> dict[str, Any]:
        return {"type": self.position}


# Convenience aliases
Bold = Strong
Italic = Em
Strikethrough = Strike
