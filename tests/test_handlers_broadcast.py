"""Tests for broadcast command handlers."""

from unittest.mock import (
    AsyncMock,
    MagicMock,
    Mock,
)

import pytest
from telegram import (
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
)
from telegram.ext import CallbackContext, ConversationHandler

from src import handlers, messages
from src.config import settings


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

    # Check that preview was sent with the real confirmation keyboard
    args = update_mock.message.reply_text.call_args
    assert "Предпросмотр рассылки" in args[0][0]
    assert "2" in args[0][0]  # 2 recipients
    assert "Test broadcast message" in args[0][0]
    assert args[1]["parse_mode"] == "HTML"
    reply_markup = args[1]["reply_markup"]
    assert isinstance(reply_markup, InlineKeyboardMarkup)
    button_datas = [btn.callback_data for row in reply_markup.inline_keyboard for btn in row]
    assert button_datas == ["broadcast_confirm", "broadcast_cancel"]

    # Check that text was saved
    assert context_mock.chat_data["broadcast_text"] == "Test broadcast message"
    assert result == settings.WAITING_FOR_BROADCAST_CONFIRM


@pytest.mark.asyncio
async def test_broadcast_confirm_cancel(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Test cancelling the broadcast."""
    from unittest.mock import MagicMock

    update_mock.effective_user.id = developer_id
    update_mock.callback_query = MagicMock()
    update_mock.callback_query.from_user.id = developer_id
    update_mock.callback_query.data = "broadcast_cancel"
    update_mock.callback_query.answer = AsyncMock()
    update_mock.callback_query.edit_message_text = AsyncMock()
    context_mock.chat_data = {"broadcast_text": "Test message"}

    result = await handlers.broadcast_confirm(update_mock, context_mock)

    update_mock.callback_query.answer.assert_called_once()
    update_mock.callback_query.edit_message_text.assert_called_once_with(messages.BROADCAST_CANCELLED)
    assert context_mock.chat_data == {}
    assert result == ConversationHandler.END


@pytest.mark.asyncio
async def test_broadcast_confirm_success(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Test successful broadcast confirmation."""
    from unittest.mock import AsyncMock, MagicMock, patch

    update_mock.effective_user.id = developer_id
    update_mock.callback_query = MagicMock()
    update_mock.callback_query.from_user.id = developer_id
    update_mock.callback_query.data = "broadcast_confirm"
    update_mock.callback_query.answer = AsyncMock()
    update_mock.callback_query.edit_message_text = AsyncMock()
    update_mock.callback_query.bot = MagicMock()
    context_mock.chat_data = {"broadcast_text": "Test message"}

    # Mock the send_broadcast function
    mock_result = {"sent": 2, "failed": 0, "blocked": 0}
    with patch("src.handlers._send_broadcast", new=AsyncMock(return_value=mock_result)):
        result = await handlers.broadcast_confirm(update_mock, context_mock)

    update_mock.callback_query.answer.assert_called_once()
    args = update_mock.callback_query.edit_message_text.call_args
    assert "Рассылка завершена" in args[0][0]
    assert "Отправлено: 2" in args[0][0]
    assert context_mock.chat_data == {}
    assert result == ConversationHandler.END


@pytest.mark.asyncio
async def test_send_broadcast_all_success(mock_db_users: list) -> None:
    """Test sending broadcast to all users successfully."""
    from unittest.mock import MagicMock, patch

    # Mock bot.send_message to succeed
    async def mock_send_message(*args: object, **kwargs: object) -> MagicMock:
        return MagicMock()

    # Mock asyncio.sleep to avoid delay
    async def mock_sleep(seconds: float) -> None:
        pass

    mock_bot = MagicMock()
    mock_bot.send_message = mock_send_message

    with patch("asyncio.sleep", new=mock_sleep):
        result = await handlers._send_broadcast("Test message", mock_bot, mock_db_users)

    assert result["sent"] == 2
    assert result["failed"] == 0
    assert result["blocked"] == 0


@pytest.mark.asyncio
async def test_send_broadcast_with_blocked_user(mock_db_users: list) -> None:
    """Test sending broadcast when one user blocked the bot."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from telegram.error import Forbidden

    # Mock bot.send_message to raise Forbidden for first user
    call_count = 0

    async def mock_send_message(chat_id: int, *args: object, **kwargs: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Forbidden("User is deactivated")
        return MagicMock()

    async def mock_sleep(seconds: float) -> None:
        pass

    mock_bot = MagicMock()
    mock_bot.send_message = mock_send_message

    # Mock db.delete_user
    with patch("asyncio.sleep", new=mock_sleep), patch(
        "src.handlers.db.delete_user", new=AsyncMock(return_value=True)
    ) as mock_delete:
        result = await handlers._send_broadcast("Test message", mock_bot, mock_db_users)

    # Check that user was deleted
    mock_delete.assert_called_once_with(111)
    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["blocked"] == 1


@pytest.mark.asyncio
async def test_send_broadcast_with_network_error(mock_db_users: list) -> None:
    """Test sending broadcast when network error occurs."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from telegram.error import NetworkError

    # Mock bot.send_message to raise NetworkError for first user
    call_count = 0

    async def mock_send_message(chat_id: int, *args: object, **kwargs: object) -> MagicMock:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise NetworkError("Network error")
        return MagicMock()

    async def mock_sleep(seconds: float) -> None:
        pass

    mock_bot = MagicMock()
    mock_bot.send_message = mock_send_message

    with patch("asyncio.sleep", new=mock_sleep), patch(
        "src.handlers.db.delete_user", new=AsyncMock(return_value=True)
    ) as mock_delete:
        result = await handlers._send_broadcast("Test message", mock_bot, mock_db_users)

    # User should NOT be deleted for network errors
    mock_delete.assert_not_called()
    assert result["sent"] == 1
    assert result["failed"] == 1
    assert result["blocked"] == 0

