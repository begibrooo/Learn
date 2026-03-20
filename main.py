import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.db import init_db, migrate_db
from middlewares.auth import AuthMiddleware
from middlewares.throttle import ThrottleMiddleware
from handlers import (
    start, menu, lessons, profile, search,
    promo, referral, leaderboard, support,
    admin_main, admin_content, admin_promo,
    admin_users, admin_broadcast, subscription,
    actions, checkin, quiz, notes, stats,
    rewards, reminders, feedback,
    admin_members, achievements, daily_challenge
)
from utils.scheduler import friday_reward_loop
from handlers.reminders import reminder_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting LearnBot...")
    await init_db()
    await migrate_db()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middlewares
    dp.message.middleware(ThrottleMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(menu.router)
    dp.include_router(lessons.router)
    dp.include_router(profile.router)
    dp.include_router(search.router)
    dp.include_router(promo.router)
    dp.include_router(referral.router)
    dp.include_router(leaderboard.router)
    dp.include_router(support.router)
    dp.include_router(admin_main.router)
    dp.include_router(admin_content.router)
    dp.include_router(admin_promo.router)
    dp.include_router(admin_users.router)
    dp.include_router(admin_broadcast.router)
    dp.include_router(actions.router)
    dp.include_router(checkin.router)
    dp.include_router(quiz.router)
    dp.include_router(notes.router)
    dp.include_router(stats.router)
    dp.include_router(rewards.router)
    dp.include_router(reminders.router)
    dp.include_router(feedback.router)
    dp.include_router(admin_members.router)
    dp.include_router(achievements.router)
    dp.include_router(daily_challenge.router)

    await bot.delete_webhook(drop_pending_updates=True)

    # Start Friday reward scheduler as background task
    asyncio.create_task(friday_reward_loop(bot))
    asyncio.create_task(reminder_loop(bot))
    logger.info("Schedulers started: friday rewards + reminders.")

    logger.info("Bot started. Polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
