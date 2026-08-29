"""Интеграционные тесты регистрации обработчиков в приложении бота."""

import datetime as dt

import pytest
from telegram import (
    Bot,
    Chat,
    Message,
    MessageEntity,
    Update,
    User,
)
from telegram.ext import ApplicationBuilder

from src import bot, messages
from src.config import settings


def _make_message_update(text: str, user_id: int, bot: Bot) -> Update:
    """Собирает Update с текстовым сообщением от пользователя."""
    user = User(id=user_id, is_bot=False, first_name="Dev")
    entities = (
        [MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=len(text))]
        if text.startswith("/")
        else None
    )
    message = Message(
        message_id=1,
        date=dt.datetime.now(),
        chat=Chat(id=user_id, type=Chat.PRIVATE),
        from_user=user,
        text=text,
        entities=entities,
    )
    message.set_bot(bot)
    return Update(update_id=1, message=message)


async def test_broadcast_command_starts_conversation(monkeypatch: pytest.MonkeyPatch) -> None:
    """/broadcast запускает диалог рассылки, а не перехватывается одиночным CommandHandler."""
    application = ApplicationBuilder().token(settings.BOT_TOKEN).build()
    bot.register_handlers(application)

    replies: list[str] = []

    async def fake_reply_text(self: Message, text: str, *args: object, **kwargs: object) -> None:
        replies.append(text)

    async def fake_get_me(self: Bot, *args: object, **kwargs: object) -> User:
        # Настоящий get_me кэширует результат в _bot_user — фейк повторяет это поведение.
        self._bot_user = User(id=1, is_bot=True, first_name="Bot", username="test_bot")
        return self._bot_user

    monkeypatch.setattr(Message, "reply_text", fake_reply_text)
    monkeypatch.setattr(Bot, "get_me", fake_get_me)

    async with application:
        await application.process_update(
            _make_message_update("/broadcast", settings.DEVELOPER_TG_ID, application.bot),
        )
        await application.process_update(
            _make_message_update("Текст рассылки", settings.DEVELOPER_TG_ID, application.bot),
        )

    assert replies[0] == messages.BROADCAST_TEXT
    # Если состояние диалога не создано, текст уйдёт в wrong_command с сообщением WRONG.
    assert "Предпросмотр рассылки" in replies[1]
