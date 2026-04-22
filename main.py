import logging
from telegram.ext import Application
from config import BOT_TOKEN
from database.db import init_db
from bot.handlers import build_conversation_handler
from bot.commands import register_commands
from scheduler.scheduler import start_scheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(build_conversation_handler())
    register_commands(app)

    start_scheduler(app)

    logger.info("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
