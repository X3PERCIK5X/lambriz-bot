from __future__ import annotations

import logging
import os
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lambriz_bot")


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / "config.env"
LOGO_PATH = BASE_DIR / "logo.png"


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE from config.env without external deps."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_env_file(ENV_PATH)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError(
        "Не найден BOT_TOKEN. Создай config.env рядом с bot.py и добавь:\n"
        "BOT_TOKEN=123456:ABCDEF...\n"
    )

WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
if not WEBAPP_URL:
    logger.warning("WEBAPP_URL пустой. Кнопка мини-аппа не будет показана.")

WELCOME_TEXT = os.getenv(
    "WELCOME_TEXT",
    "ЛАМБРИЗ — оборудование и изделия из нержавеющей стали для бизнеса.\n"
    "Откройте каталог, чтобы выбрать нужные позиции.",
)


def main_keyboard() -> InlineKeyboardMarkup:
    rows = []
    if WEBAPP_URL:
        rows.append(
            [InlineKeyboardButton("Каталог", web_app=WebAppInfo(url=WEBAPP_URL))]
        )
    return InlineKeyboardMarkup(rows)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    if LOGO_PATH.exists():
        with LOGO_PATH.open("rb") as f:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=f,
                caption=WELCOME_TEXT,
                parse_mode=ParseMode.HTML,
                reply_markup=main_keyboard(),
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=WELCOME_TEXT,
            parse_mode=ParseMode.HTML,
            reply_markup=main_keyboard(),
        )


def main() -> None:
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    logger.info("Lambriz bot started (polling)")
    app.run_polling()


if __name__ == "__main__":
    main()
