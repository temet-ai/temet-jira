"""Tests for ADF text extraction."""


from jira_tool.document.adf import extract_text_from_adf


class TestExtractTextFromAdf:
    """Test suite for extract_text_from_adf function."""

    def test_string_passthrough(self) -> None:
        """Plain strings are returned unchanged."""
        assert extract_text_from_adf("Hello world") == "Hello world"

    def test_non_doc_dict_returns_str(self) -> None:
        """Non-doc dicts are converted to string."""
        result = extract_text_from_adf({"type": "other", "value": "test"})
        assert "other" in result

    def test_empty_doc(self) -> None:
        """Empty doc returns empty string."""
        doc = {"type": "doc", "version": 1, "content": []}
        assert extract_text_from_adf(doc) == ""

    def test_paragraph_with_text(self) -> None:
        """Paragraphs extract text content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Hello world"}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "Hello world" in result

    def test_heading_level_1(self) -> None:
        """Heading level 1 prefixes with single #."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Title"}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "# Title" in result

    def test_heading_level_3(self) -> None:
        """Heading level 3 prefixes with ###."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 3},
                    "content": [{"type": "text", "text": "Subsection"}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "### Subsection" in result

    def test_bullet_list(self) -> None:
        """Bullet lists use bullet character."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 1"}],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Item 2"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "• Item 1" in result
        assert "• Item 2" in result

    def test_ordered_list(self) -> None:
        """Ordered lists use numbered format."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "orderedList",
                    "attrs": {"order": 1},
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "First"}],
                                }
                            ],
                        },
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Second"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "1. First" in result
        assert "2. Second" in result

    def test_code_block(self) -> None:
        """Code blocks are wrapped in triple backticks."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "codeBlock",
                    "attrs": {"language": "python"},
                    "content": [{"type": "text", "text": "print('hello')"}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "```python" in result
        assert "print('hello')" in result
        assert "```" in result

    def test_panel(self) -> None:
        """Panels show type label."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "panel",
                    "attrs": {"panelType": "warning"},
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Warning message"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[WARNING]" in result
        assert "Warning message" in result

    def test_emoji_with_text(self) -> None:
        """Emoji nodes extract text attribute."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "emoji", "attrs": {"text": "👍", "shortName": ":+1:"}}
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "👍" in result

    def test_emoji_without_text_uses_shortname(self) -> None:
        """Emoji falls back to shortName when text missing."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "emoji", "attrs": {"shortName": ":smile:"}}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert ":smile:" in result

    def test_complex_document(self) -> None:
        """Complex document with multiple node types."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "heading",
                    "attrs": {"level": 1},
                    "content": [{"type": "text", "text": "Main Title"}],
                },
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Introduction text."}],
                },
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Point one"}],
                                }
                            ],
                        }
                    ],
                },
            ],
        }
        result = extract_text_from_adf(doc)
        assert "# Main Title" in result
        assert "Introduction text" in result
        assert "• Point one" in result


class TestExtractTextFromAdfEdgeCases:
    """Edge case tests for extract_text_from_adf."""

    def test_missing_content(self) -> None:
        """Nodes without content are handled gracefully."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph"}],
        }
        result = extract_text_from_adf(doc)
        assert result == ""

    def test_unknown_node_type_with_content(self) -> None:
        """Unknown node types with content are traversed."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "unknownNode",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Nested text"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "Nested text" in result

    def test_empty_text_node(self) -> None:
        """Empty text nodes don't cause errors."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": ""}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert result == ""

    def test_code_block_without_language(self) -> None:
        """Code blocks without language default to empty."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "codeBlock",
                    "attrs": {},
                    "content": [{"type": "text", "text": "code here"}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "```\n" in result or "```" in result
        assert "code here" in result

    def test_panel_without_type(self) -> None:
        """Panel without type defaults to INFO."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "panel",
                    "attrs": {},
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Info message"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[INFO]" in result

    def test_ordered_list_custom_start(self) -> None:
        """Ordered lists can start from custom number."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "orderedList",
                    "attrs": {"order": 5},
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "Fifth item"}],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "5. Fifth item" in result


class TestExtractTextInlineHandlers:
    """Tests for newly added inline node handlers."""

    def test_hard_break_produces_newline(self) -> None:
        """hardBreak node should produce a newline character."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Line one"},
                        {"type": "hardBreak"},
                        {"type": "text", "text": "Line two"},
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "Line one\nLine two" in result

    def test_mention_with_text(self) -> None:
        """mention node with attrs.text shows @Name."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "mention",
                            "attrs": {"id": "abc123", "text": "John Doe"},
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "@John Doe" in result

    def test_mention_with_at_prefix_not_doubled(self) -> None:
        """mention whose text already starts with @ should not double-prefix."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "mention", "attrs": {"text": "@Alice"}}
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "@Alice" in result
        assert "@@Alice" not in result

    def test_mention_missing_text(self) -> None:
        """mention without attrs.text shows @unknown."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "mention", "attrs": {"id": "abc123"}}
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "@unknown" in result

    def test_date_timestamp_to_yyyy_mm_dd(self) -> None:
        """date node converts millis timestamp to YYYY-MM-DD."""
        # 1700000000000 ms = 2023-11-14 UTC
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "date", "attrs": {"timestamp": "1700000000000"}}
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "2023-11-14" in result

    def test_date_missing_timestamp(self) -> None:
        """date node without timestamp shows placeholder."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "date", "attrs": {}}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "(no date)" in result

    def test_status_wraps_in_brackets(self) -> None:
        """status node wraps attrs.text in square brackets."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "status", "attrs": {"text": "IN PROGRESS", "color": "blue"}}
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[IN PROGRESS]" in result

    def test_status_missing_text(self) -> None:
        """status without text shows [status] fallback."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "status", "attrs": {}}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[status]" in result

    def test_inline_card_renders_url(self) -> None:
        """inlineCard renders the attrs.url."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "inlineCard",
                            "attrs": {"url": "https://example.com/page"},
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "https://example.com/page" in result

    def test_inline_card_missing_url(self) -> None:
        """inlineCard without url shows (link) fallback."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "inlineCard", "attrs": {}}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "(link)" in result


class TestExtractTextBlockHandlers:
    """Tests for newly added block node handlers."""

    def test_blockquote_prefixes_with_gt(self) -> None:
        """blockquote child content is prefixed with '> '."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "blockquote",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Quoted text"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "> Quoted text" in result

    def test_rule_renders_triple_dash(self) -> None:
        """rule node renders as ---."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Above"}],
                },
                {"type": "rule"},
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Below"}],
                },
            ],
        }
        result = extract_text_from_adf(doc)
        assert "---" in result
        assert "Above" in result
        assert "Below" in result

    def test_expand_shows_title_and_content(self) -> None:
        """expand node shows [title] and child content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "expand",
                    "attrs": {"title": "Click to expand"},
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Hidden content"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[Click to expand]" in result
        assert "Hidden content" in result

    def test_nested_expand_same_as_expand(self) -> None:
        """nestedExpand uses the same handler as expand."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "nestedExpand",
                    "attrs": {"title": "Nested section"},
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "Inner text"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[Nested section]" in result
        assert "Inner text" in result

    def test_table_rows_with_pipe_separators(self) -> None:
        """table renders rows with | separators."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "table",
                    "attrs": {"layout": "default"},
                    "content": [
                        {
                            "type": "tableRow",
                            "content": [
                                {
                                    "type": "tableHeader",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Name"}],
                                        }
                                    ],
                                },
                                {
                                    "type": "tableHeader",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Value"}],
                                        }
                                    ],
                                },
                            ],
                        },
                        {
                            "type": "tableRow",
                            "content": [
                                {
                                    "type": "tableCell",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Foo"}],
                                        }
                                    ],
                                },
                                {
                                    "type": "tableCell",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Bar"}],
                                        }
                                    ],
                                },
                            ],
                        },
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "| Name | Value |" in result
        assert "| Foo | Bar |" in result

    def test_media_single_with_alt_text(self) -> None:
        """mediaSingle with alt text shows [image: alt]."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "mediaSingle",
                    "attrs": {"layout": "center"},
                    "content": [
                        {
                            "type": "media",
                            "attrs": {
                                "type": "file",
                                "id": "abc-123",
                                "alt": "screenshot",
                            },
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[image: screenshot]" in result

    def test_media_group_without_alt(self) -> None:
        """mediaGroup without alt shows [attachment]."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "mediaGroup",
                    "content": [
                        {
                            "type": "media",
                            "attrs": {"type": "file", "id": "xyz-789"},
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[attachment]" in result


class TestExtractTextBugFixesAndFallbacks:
    """Tests for bug fixes and unknown leaf fallback behaviour."""

    def test_list_item_with_mention_and_text(self) -> None:
        """List item paragraph with text AND mention extracts both.

        This tests the bug fix where the old code only extracted direct text
        children of list items, missing inline nodes like mentions and links.
        """
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "Assigned to "},
                                        {
                                            "type": "mention",
                                            "attrs": {"id": "u1", "text": "Bob"},
                                        },
                                        {"type": "text", "text": " for review"},
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "Assigned to" in result
        assert "@Bob" in result
        assert "for review" in result

    def test_unknown_node_with_attrs_text(self) -> None:
        """Unknown leaf node with attrs.text extracts that text."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "someNewInlineType", "attrs": {"text": "custom text"}}
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "custom text" in result

    def test_unknown_node_with_attrs_url(self) -> None:
        """Unknown leaf node with attrs.url extracts the URL."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "futureCardType",
                            "attrs": {"url": "https://new.example.com"},
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "https://new.example.com" in result

    def test_unknown_node_no_attrs_does_not_crash(self) -> None:
        """Unknown leaf node with no attrs returns empty without crashing."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "totallyUnknown"}],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        # Should not raise; result may be empty or just whitespace
        assert isinstance(result, str)


class TestRemainingAdfNodeHandlers:
    """Tests for remaining ADF spec node handlers."""

    def test_list_item_standalone(self) -> None:
        """listItem outside a list context still extracts content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "listItem",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "standalone item"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "standalone item" in result

    def test_media_standalone_with_alt(self) -> None:
        """Standalone media node with alt text."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "media",
                    "attrs": {"type": "file", "id": "abc", "alt": "screenshot"},
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[image: screenshot]" in result

    def test_media_standalone_without_alt(self) -> None:
        """Standalone media node without alt text."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "media",
                    "attrs": {"type": "file", "id": "abc"},
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[attachment]" in result

    def test_media_inline_with_alt(self) -> None:
        """Inline media with alt text."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "see "},
                        {
                            "type": "mediaInline",
                            "attrs": {
                                "type": "file",
                                "id": "abc",
                                "alt": "diagram.png",
                            },
                        },
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "diagram.png" in result

    def test_media_inline_without_alt(self) -> None:
        """Inline media without alt shows [attachment]."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "mediaInline",
                            "attrs": {"type": "file", "id": "abc"},
                        },
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "[attachment]" in result

    def test_table_row_standalone(self) -> None:
        """tableRow outside table context still renders cells."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "tableRow",
                    "content": [
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "A"}],
                                }
                            ],
                        },
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": "B"}],
                                }
                            ],
                        },
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "A" in result
        assert "B" in result
        assert "|" in result

    def test_table_cell_standalone(self) -> None:
        """tableCell outside table extracts content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "tableCell",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "cell content"}],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "cell content" in result

    def test_table_header_standalone(self) -> None:
        """tableHeader outside table extracts content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "tableHeader",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "header content"}
                            ],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "header content" in result

    def test_multi_bodied_extension_with_key(self) -> None:
        """multiBodiedExtension shows extensionKey and recurses content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "multiBodiedExtension",
                    "attrs": {"extensionKey": "tabs"},
                    "content": [
                        {
                            "type": "extensionFrame",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {"type": "text", "text": "tab content"}
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "tabs" in result
        assert "tab content" in result

    def test_multi_bodied_extension_without_key(self) -> None:
        """multiBodiedExtension without key still extracts content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "multiBodiedExtension",
                    "attrs": {},
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "ext content"}
                            ],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "ext content" in result

    def test_extension_frame(self) -> None:
        """extensionFrame recurses content."""
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "extensionFrame",
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "frame text"}
                            ],
                        }
                    ],
                }
            ],
        }
        result = extract_text_from_adf(doc)
        assert "frame text" in result
