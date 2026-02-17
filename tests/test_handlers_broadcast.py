"""Tests for broadcast command handlers."""

import sys
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from telegram import Message, Update, User
from telegram.ext import CallbackContext, ConversationHandler

# Mock keyboards module before any imports
sys.modules["src.keyboards"] = MagicMock()

from src import handlers, messages  # noqa: E402
from src.config import settings  # noqa: E402


@pytest.fixture
def developer_id() -> int:
    """Return the developer ID from settings."""
    return settings.DEVELOPER_TG_ID


@pytest.fixture
def update_mock() -> Mock:
    """Create a mock Update object."""
    update = Mock(spec=Update)
    user = Mock(spec=User)
    user.id = 12345
    update.effective_user = user

    message = Mock(spec=Message)
    message.reply_text = AsyncMock()
    update.message = message

    return update


@pytest.fixture
def context_mock() -> Mock:
    """Create a mock Context object."""
    context = Mock(spec=CallbackContext)
    context.chat_data = {}
    context.user_data = {}
    return context


@pytest.mark.asyncio
async def test_broadcast_unauthorized_user(update_mock: Mock, context_mock: Mock) -> None:
    """Test that unauthorized users cannot access broadcast command."""
    # Mock a non-developer user
    update_mock.effective_user.id = 12345  # Not the developer
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast(update_mock, context_mock)

    # Should send forbidden message and end conversation
    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_FORBIDDEN)
    assert result == ConversationHandler.END


@pytest.mark.asyncio
async def test_broadcast_authorized_user(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Test that authorized developer can access broadcast command."""
    # Mock the developer user
    update_mock.effective_user.id = developer_id
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast(update_mock, context_mock)

    # Should prompt for text and wait
    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_TEXT)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT

