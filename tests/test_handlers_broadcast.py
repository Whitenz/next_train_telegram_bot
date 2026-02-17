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


@pytest.fixture
def mock_db_users() -> list:
    """Create mock database users for testing."""
    from src.models import BotUser

    return [
        BotUser(
            bot_user_id=111,
            first_name="User1",
            last_name=None,
            username="user1",
            is_bot=False,
        ),
        BotUser(
            bot_user_id=222,
            first_name="User2",
            last_name=None,
            username="user2",
            is_bot=False,
        ),
    ]


@pytest.mark.asyncio
async def test_broadcast_receive_text_too_long(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Test that too long text is rejected."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = "x" * 5000  # Too long
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast_receive_text(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_TOO_LONG)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.mark.asyncio
async def test_broadcast_receive_text_empty(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Test that empty text is rejected."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = ""
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast_receive_text(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_EMPTY)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.mark.asyncio
async def test_broadcast_receive_text_success(
    update_mock: Mock, context_mock: Mock, developer_id: int, mock_db_users: list
) -> None:
    """Test successful text reception and preview."""
    from unittest.mock import patch

    update_mock.effective_user.id = developer_id
    update_mock.message.text = "Test broadcast message"
    update_mock.message.reply_text.return_value = None

    # Mock db.select_all_users to return some users
    with patch("src.handlers.db.select_all_users", new=AsyncMock(return_value=mock_db_users)):
        result = await handlers.broadcast_receive_text(update_mock, context_mock)

    # Check that preview was sent
    args = update_mock.message.reply_text.call_args
    assert "Предпросмотр рассылки" in args[0][0]
    assert "2" in args[0][0]  # 2 recipients
    assert "Test broadcast message" in args[0][0]
    assert args[1]["parse_mode"] == "HTML"
    assert args[1]["reply_markup"] is not None

    # Check that text was saved
    assert context_mock.chat_data["broadcast_text"] == "Test broadcast message"
    assert result == settings.WAITING_FOR_BROADCAST_CONFIRM

