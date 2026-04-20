import sys
import asyncio
from create_bot import bot
from handlers.start import start_router
from handlers.work_with_db import bd_router
from handlers.menu import menu_router
import handlers.main
import handlers.notion
import ml_models.models


def main():
    bot.labeler.load(start_router.labeler)
    bot.labeler.load(bd_router.labeler)
    bot.labeler.load(menu_router.labeler)
    print("Бот запущен")
    bot.run_forever()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
