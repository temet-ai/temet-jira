"""Shared test fixtures for temet-jira tests."""

from unittest.mock import MagicMock, patch

import pytest

from temet_jira.client import JiraClient

# Test configuration constants - change these in one place for all tests
TEST_JIRA_BASE_URL = "https://test.atlassian.net"
TEST_JIRA_USERNAME = "test@example.com"
TEST_JIRA_API_TOKEN = "test-token"


@pytest.fixture
def jira_client():
    """Create a Jira client with mocked credentials."""
    with patch.dict(
        "os.environ",
        {
            "JIRA_BASE_URL": TEST_JIRA_BASE_URL,
            "JIRA_USERNAME": TEST_JIRA_USERNAME,
            "JIRA_API_TOKEN": TEST_JIRA_API_TOKEN,
        },
    ):
        return JiraClient()


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.json.return_value = {
        "issues": [{"key": "TEST-1", "fields": {"summary": "Test Issue"}}]
    }
    response.raise_for_status = MagicMock()
    return response
