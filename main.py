import asyncio

from pyrogram import idle

from auto_repost import AutoRepostWorker
from bot import Bot
from config import LOGGER, validate_config

logger = LOGGER(__name__)


async def main():
    validate_config()
    bot = Bot()
    worker = AutoRepostWorker(bot)
    await bot.start()
    await worker.start()
    try:
        await idle()
    finally:
        await worker.stop()
        await bot.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
