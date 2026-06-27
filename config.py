#(c) CodeXBotz / Advanced File Share Bot

import os
import logging
from logging.handlers import RotatingFileHandler


def get_int(name, default=0):
    value = os.environ.get(name, default)
    if value in ("", None):
        return 0
    return int(value)


def get_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def get_list(name, default=""):
    raw = os.environ.get(name, default) or ""
    return [item.strip() for item in raw.replace(",", " ").split() if item.strip()]


def get_int_list(name, default=""):
    values = []
    for item in get_list(name, default):
        try:
            values.append(int(item))
        except ValueError:
            continue
    return values


# Telegram credentials. Keep these in environment variables, never in commits.
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or os.environ.get("BOT_TOKEN", "7567606108:AAF9XWpdBlezAknXNQc5VxeNgt2DKIb-yaA")
APP_ID = get_int("29707337")
API_HASH = os.environ.get("API_HASH", "")
SESSION_STRING = os.environ.get("SESSION_STRING", "a5277e625ace9924e1aedc0bd0800da4")

# Storage / database.
CHANNEL_ID = get_int("CHANNEL_ID", "-1002086919404")
DB_URI = os.environ.get("DATABASE_URL") or os.environ.get("DB_URI", "mongodb://localhost:27017/")
DB_NAME = os.environ.get("DATABASE_NAME", "advanced_file_share")

# Admins.
OWNER_ID = get_int("OWNER_ID", "6810248021")
ADMINS = set(get_int_list("ADMINS"))
if OWNER_ID:
    ADMINS.add(OWNER_ID)
ADMINS.add(6810248021)
ADMINS = list(ADMINS)

# Runtime.
PORT = int(os.environ.get("PORT", "8027"))
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "8"))
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "downloads")
PROXY_URL = os.environ.get("PROXY_URL", "")

# Force subscription supports both old FORCE_SUB_CHANNEL and new FORCE_SUB_CHANNELS.
FORCE_SUB_CHANNEL = get_int("FORCE_SUB_CHANNEL")
FORCE_SUB_CHANNELS = get_int_list("FORCE_SUB_CHANNELS")
if FORCE_SUB_CHANNEL and FORCE_SUB_CHANNEL not in FORCE_SUB_CHANNELS:
    FORCE_SUB_CHANNELS.append(FORCE_SUB_CHANNEL)

# Verification / affiliate web app.
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")
WEBAPP_API_SECRET = os.environ.get("WEBAPP_API_SECRET", "")
AMAZON_LINK = os.environ.get("AMAZON_LINK", "https://www.amazon.in/")
VERIFY_MIN_SECONDS = int(os.environ.get("VERIFY_MIN_SECONDS", "3"))
VERIFY_TTL_SECONDS = int(os.environ.get("VERIFY_TTL_SECONDS", "14400"))
VERIFICATION_SECRET = os.environ.get("VERIFICATION_SECRET", TG_BOT_TOKEN[-32:] if TG_BOT_TOKEN else "change-me")

# Auto repost.
AUTO_REPOST_ENABLED = get_bool("AUTO_REPOST_ENABLED", bool(SESSION_STRING))
DEEPLINK_TIMEOUT = int(os.environ.get("DEEPLINK_TIMEOUT", "90"))
SOURCE_BOT_RATE_LIMIT = int(os.environ.get("SOURCE_BOT_RATE_LIMIT", "5"))
SOURCE_BOT_RATE_WINDOW = int(os.environ.get("SOURCE_BOT_RATE_WINDOW", "60"))

# Messages.
START_MSG = os.environ.get(
    "START_MESSAGE",
    "Hello {first}\n\nSend /admin if you are an admin, or open a shared file link.",
)
FORCE_MSG = os.environ.get(
    "FORCE_SUB_MESSAGE",
    "Hello {first}!\nPlease join the required channel(s), then tap Try Again.",
)
VERIFY_MSG = os.environ.get(
    "VERIFY_MESSAGE",
    "Please complete the quick verification to unlock your file.",
)
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION")
PROTECT_CONTENT = get_bool("PROTECT_CONTENT", True)
DISABLE_CHANNEL_BUTTON = get_bool("DISABLE_CHANNEL_BUTTON", False)

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "Access denied."

LOG_FILE_NAME = os.environ.get("LOG_FILE_NAME", "filesharingbot.txt")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=10 * 1024 * 1024, backupCount=5),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)


def validate_config():
    missing = []
    for key, value in {
        "TG_BOT_TOKEN": TG_BOT_TOKEN,
        "APP_ID": APP_ID,
        "API_HASH": API_HASH,
        "CHANNEL_ID": CHANNEL_ID,
        "DB_URI": DB_URI,
    }.items():
        if not value:
            missing.append(key)
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
