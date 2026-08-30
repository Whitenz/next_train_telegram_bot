"""Tests for broadcast command handlers."""

from unittest.mock import (
    AsyncMock,
    MagicMock,
    Mock,
    patch,
)

import pytest
from src import handlers, messages
from src.config import settings
from src.models import BotUser
from telegram import (
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
)
from telegram.error import Forbidden, NetworkError
from telegram.ext import CallbackContext, ConversationHandler


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
async def test_broadcast_authorized_user(update_mock: Mock, context_mock: Mock, developer_id: int) -> None:
    """Test that authorized developer can access broadcast command."""
    # Mock the developer user
    update_mock.effective_user.id = developer_id
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast(update_mock, context_mock)

    # Should prompt for text and wait
    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_TEXT)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.fixture
def mock_db_users() -> list[BotUser]:
    """Create mock database users for testing."""
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
async def test_broadcast_receive_text_too_long(update_mock: Mock, context_mock: Mock, developer_id: int) -> None:
    """Test that too long text is rejected."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = "x" * 5000  # Too long
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast_receive_text(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_TOO_LONG)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.mark.asyncio
async def test_broadcast_receive_text_empty(update_mock: Mock, context_mock: Mock, developer_id: int) -> None:
    """Test that empty text is rejected."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = ""
    update_mock.message.reply_text.return_value = None

    result = await handlers.broadcast_receive_text(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_EMPTY)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.mark.asyncio
async def test_broadcast_receive_text_success(
    update_mock: Mock, context_mock: Mock, developer_id: int, mock_db_users: list[BotUser]
) -> None:
    """Test successful text reception and preview."""
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
async def test_broadcast_receive_text_rejects_text_filling_whole_limit(
    update_mock: Mock, context_mock: Mock, developer_id: int, mock_db_users: list[BotUser]
) -> None:
    """Текст ровно в 4096 символов отклоняется: превью добавляет служебную шапку."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = "a" * 4096
    update_mock.message.reply_text.return_value = None

    with patch("src.handlers.db.select_all_users", new=AsyncMock(return_value=mock_db_users)):
        result = await handlers.broadcast_receive_text(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_TOO_LONG)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.mark.asyncio
async def test_broadcast_receive_text_rejects_emoji_heavy_text(
    update_mock: Mock, context_mock: Mock, developer_id: int, mock_db_users: list[BotUser]
) -> None:
    """Эмодзи-текст отклоняется по UTF-16 лимиту, а не по числу code points."""
    update_mock.effective_user.id = developer_id
    # 2100 эмодзи = 2100 code points, но 4200 UTF-16 code units.
    update_mock.message.text = "😀" * 2100
    update_mock.message.reply_text.return_value = None

    with patch("src.handlers.db.select_all_users", new=AsyncMock(return_value=mock_db_users)):
        result = await handlers.broadcast_receive_text(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once_with(messages.BROADCAST_TOO_LONG)
    assert result == settings.WAITING_FOR_BROADCAST_TEXT


@pytest.mark.asyncio
async def test_broadcast_receive_text_escapes_html(
    update_mock: Mock, context_mock: Mock, developer_id: int, mock_db_users: list[BotUser]
) -> None:
    """Спецсимволы HTML в тексте рассылки экранируются в превью."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = "Скидка <50% для R&D"
    update_mock.message.reply_text.return_value = None

    with patch("src.handlers.db.select_all_users", new=AsyncMock(return_value=mock_db_users)):
        await handlers.broadcast_receive_text(update_mock, context_mock)

    args = update_mock.message.reply_text.call_args
    assert "Скидка &lt;50% для R&amp;D" in args[0][0]
    assert "<50%" not in args[0][0]
    # Оригинальный текст сохраняется без экранирования: доставка уходит как plain text.
    assert context_mock.chat_data["broadcast_text"] == "Скидка <50% для R&D"


@pytest.mark.asyncio
async def test_broadcast_confirm_cancel(update_mock: Mock, context_mock: Mock, developer_id: int) -> None:
    """Test cancelling the broadcast."""
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
async def test_broadcast_confirm_success(update_mock: Mock, context_mock: Mock, developer_id: int) -> None:
    """Test successful broadcast confirmation."""
    update_mock.effective_user.id = developer_id
    # spec=CallbackQuery не даст сфабриковать несуществующие атрибуты:
    # у CallbackQuery в PTB 20.x нет публичного .bot, есть только context.bot.
    callback_query = Mock(spec=CallbackQuery)
    callback_query.data = "broadcast_confirm"
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    update_mock.callback_query = callback_query
    context_mock.chat_data = {"broadcast_text": "Test message"}
    context_mock.bot = MagicMock()

    # Mock the send_broadcast function
    mock_result = {"sent": 2, "failed": 0, "blocked": 0}
    with patch("src.handlers._send_broadcast", new=AsyncMock(return_value=mock_result)):
        result = await handlers.broadcast_confirm(update_mock, context_mock)

    callback_query.answer.assert_called_once()
    args = callback_query.edit_message_text.call_args
    assert "Рассылка завершена" in args[0][0]
    assert "Отправлено: 2" in args[0][0]
    assert context_mock.chat_data == {}
    assert result == ConversationHandler.END


@pytest.mark.asyncio
async def test_broadcast_receive_text_saves_bot_message(
    update_mock: Mock, context_mock: Mock, developer_id: int, mock_db_users: list[BotUser]
) -> None:
    """Preview-сообщение сохраняется в chat_data для обработки таймаута диалога."""
    update_mock.effective_user.id = developer_id
    update_mock.message.text = "Test broadcast message"
    preview_message = MagicMock()
    update_mock.message.reply_text.return_value = preview_message

    with patch("src.handlers.db.select_all_users", new=AsyncMock(return_value=mock_db_users)):
        await handlers.broadcast_receive_text(update_mock, context_mock)

    assert context_mock.chat_data["bot_message"] is preview_message


@pytest.mark.asyncio
async def test_broadcast_timeout_edits_preview_and_clears_chat_data(context_mock: Mock) -> None:
    """Таймаут broadcast-диалога уведомляет разработчика и очищает chat_data."""
    bot_message = MagicMock()
    bot_message.edit_text = AsyncMock()
    context_mock.chat_data = {"broadcast_text": "Test", "bot_message": bot_message}

    await handlers.broadcast_timeout(MagicMock(), context_mock)

    bot_message.edit_text.assert_called_once_with(messages.BROADCAST_TIMEOUT)
    assert context_mock.chat_data == {}


@pytest.mark.asyncio
async def test_broadcast_confirm_ignores_foreign_callback(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Чужой callback_data (например, кнопка станции) не запускает рассылку."""
    update_mock.effective_user.id = developer_id
    callback_query = Mock(spec=CallbackQuery)
    callback_query.data = "1"  # кнопка выбора станции из другой клавиатуры
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    update_mock.callback_query = callback_query
    context_mock.chat_data = {"broadcast_text": "Test message"}
    context_mock.bot = MagicMock()

    with patch("src.handlers._send_broadcast", new=AsyncMock()) as mock_send:
        result = await handlers.broadcast_confirm(update_mock, context_mock)

    mock_send.assert_not_called()
    assert result == settings.WAITING_FOR_BROADCAST_CONFIRM


@pytest.mark.asyncio
async def test_broadcast_confirm_fails_fast_without_saved_text(
    update_mock: Mock, context_mock: Mock, developer_id: int
) -> None:
    """Отсутствие сохранённого текста — явный сбой, а не тихая пустая рассылка."""
    update_mock.effective_user.id = developer_id
    callback_query = Mock(spec=CallbackQuery)
    callback_query.data = "broadcast_confirm"
    callback_query.answer = AsyncMock()
    callback_query.edit_message_text = AsyncMock()
    update_mock.callback_query = callback_query
    context_mock.chat_data = {}
    context_mock.bot = MagicMock()

    with pytest.raises(KeyError):
        await handlers.broadcast_confirm(update_mock, context_mock)


@pytest.mark.asyncio
async def test_send_broadcast_all_success(mock_db_users: list[BotUser]) -> None:
    """Test sending broadcast to all users successfully."""

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
async def test_send_broadcast_with_blocked_user(mock_db_users: list[BotUser]) -> None:
    """Test sending broadcast when one user blocked the bot."""
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

    # Заблокировавшие удаляются одним batch-запросом после цикла отправки
    with (
        patch("asyncio.sleep", new=mock_sleep),
        patch("src.handlers.db.delete_users", new=AsyncMock(return_value=1)) as mock_delete,
    ):
        result = await handlers._send_broadcast("Test message", mock_bot, mock_db_users)

    # Check that blocked users were deleted in a single batch
    mock_delete.assert_called_once_with([111])
    assert result["sent"] == 1
    assert result["failed"] == 0
    assert result["blocked"] == 1


@pytest.mark.asyncio
async def test_send_broadcast_survives_delete_users_failure(mock_db_users: list[BotUser]) -> None:
    """Сбой batch-удаления заблокировавших не прерывает рассылку."""
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

    with (
        patch("asyncio.sleep", new=mock_sleep),
        patch("src.handlers.db.delete_users", new=AsyncMock(side_effect=Exception("db down"))),
    ):
        result = await handlers._send_broadcast("Test message", mock_bot, mock_db_users)

    # Рассылка дошла до конца и вернула отчёт, несмотря на сбой удаления
    assert result["sent"] == 1
    assert result["blocked"] == 1
    assert result["failed"] == 0


@pytest.mark.asyncio
async def test_send_broadcast_with_network_error(mock_db_users: list[BotUser]) -> None:
    """Test sending broadcast when network error occurs."""
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

    with (
        patch("asyncio.sleep", new=mock_sleep),
        patch("src.handlers.db.delete_users", new=AsyncMock(return_value=0)) as mock_delete,
    ):
        result = await handlers._send_broadcast("Test message", mock_bot, mock_db_users)

    # User should NOT be deleted for network errors
    mock_delete.assert_not_called()
    assert result["sent"] == 1
    assert result["failed"] == 1
    assert result["blocked"] == 0
