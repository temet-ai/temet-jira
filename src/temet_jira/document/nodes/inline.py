"""ADF inline node types."""

from typing import Any, Literal

from temet_jira.document.nodes.base import InlineNode, Mark


class Text(InlineNode):
    """Text node with optional formatting marks."""

    def __init__(self, text: str, marks: list[Mark] | None = None) -> None:
        self.text = text
        self.marks = marks or []

    @property
    def type(self) -> str:
        return "text"

    def to_adf(self) -> dict[str, Any]:
        result: dict[str, Any] = {"type": self.type, "text": self.text}
        if self.marks:
            result["marks"] = [mark.to_adf() for mark in self.marks]
        return result


class HardBreak(InlineNode):
    """Line break within a paragraph."""

    @property
    def type(self) -> str:
        return "hardBreak"

    def to_adf(self) -> dict[str, Any]:
        return {"type": self.type}


class Emoji(InlineNode):
    """Emoji node."""

    def __init__(
        self,
        short_name: str,
        emoji_id: str | None = None,
        text: str | None = None,
    ) -> None:
        """Initialize emoji node.

        Args:
            short_name: Emoji shortname (e.g., ":smile:")
            emoji_id: Optional emoji ID for custom emojis
            text: Optional fallback text/unicode character
        """
        self.short_name = short_name
        self.emoji_id = emoji_id
        self.fallback_text = text

    @property
    def type(self) -> str:
        return "emoji"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"shortName": self.short_name}
        if self.emoji_id:
            attrs["id"] = self.emoji_id
        if self.fallback_text:
            attrs["text"] = self.fallback_text
        return {"type": self.type, "attrs": attrs}


class Mention(InlineNode):
    """User or team mention node."""

    def __init__(
        self,
        account_id: str,
        text: str,
        access_level: Literal["NONE", "SITE", "APPLICATION", "CONTAINER"] = "CONTAINER",
        user_type: Literal["DEFAULT", "SPECIAL", "APP"] = "DEFAULT",
    ) -> None:
        """Initialize mention node.

        Args:
            account_id: Account ID of the user/team
            text: Display text (usually @username)
            access_level: Access level for the mention
            user_type: Type of user being mentioned
        """
        self.account_id = account_id
        self.text = text
        self.access_level = access_level
        self.user_type = user_type

    @property
    def type(self) -> str:
        return "mention"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {
                "id": self.account_id,
                "text": self.text,
                "accessLevel": self.access_level,
                "userType": self.user_type,
            },
        }


class Date(InlineNode):
    """Date node for displaying dates."""

    def __init__(self, timestamp: str) -> None:
        """Initialize date node.

        Args:
            timestamp: ISO 8601 date string or Unix timestamp in milliseconds
        """
        self.timestamp = timestamp

    @property
    def type(self) -> str:
        return "date"

    def to_adf(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "attrs": {"timestamp": self.timestamp},
        }


class Status(InlineNode):
    """Status lozenge node."""

    def __init__(
        self,
        text: str,
        color: Literal["neutral", "purple", "blue", "red", "yellow", "green"],
        style: Literal["bold", "subtle"] = "bold",
        local_id: str | None = None,
    ) -> None:
        """Initialize status node.

        Args:
            text: Status text to display
            color: Status color (neutral, purple, blue, red, yellow, green)
            style: Display style (bold or subtle)
            local_id: Optional local ID for the status
        """
        self.text = text
        self.color = color
        self.style = style
        self.local_id = local_id

    @property
    def type(self) -> str:
        return "status"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "text": self.text,
            "color": self.color,
            "style": self.style,
        }
        if self.local_id:
            attrs["localId"] = self.local_id
        return {"type": self.type, "attrs": attrs}


class InlineCard(InlineNode):
    """Inline smart link/card node."""

    def __init__(
        self,
        url: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize inline card node.

        Args:
            url: URL for the smart link
            data: Optional resolved data for the card
        """
        self.url = url
        self.data = data

    @property
    def type(self) -> str:
        return "inlineCard"

    def to_adf(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"url": self.url}
        if self.data:
            attrs["data"] = self.data
        return {"type": self.type, "attrs": attrs}
