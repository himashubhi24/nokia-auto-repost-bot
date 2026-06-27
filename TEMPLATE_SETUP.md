# Reusable Auto Repost Bot

This template is a clean copy of the working bot. Runtime data, credentials,
Telegram sessions, downloaded media, logs, and MongoDB records are excluded.

## Included flow

- Multiple source and target channel pairs.
- Source-post Telegram deeplink detection and conversion.
- Userbot login and session storage from the admin panel.
- Source-bot force-sub button handling.
- Restricted video download and upload fallback.
- Single-file and multi-video batch deeplink generation.
- Original source media with converted caption in the target channel.
- Duplicate deeplink and duplicate target-post protection.
- Start from first post with priority 1.
- Start from latest post with priority 2.
- Per-pair 30-minute or 60-minute posting interval.
- Failed or timed-out source posts are skipped so the queue can continue.
- Admin controls for pairs, force-sub channels, status, backfill, and schedule.

## New server setup

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip mongodb
git clone YOUR_PRIVATE_REPOSITORY_URL botfather-repost
cd botfather-repost
./setup.sh
nano .env
```

Required `.env` values are `TG_BOT_TOKEN`, `APP_ID`, `API_HASH`, `OWNER_ID`,
`ADMINS`, `CHANNEL_ID`, `DATABASE_URL`, `DATABASE_NAME`, and
`VERIFICATION_SECRET`. Add the userbot through `/admin`, or set
`SESSION_STRING` directly.

## Test before systemd

```bash
set -a && source .env && set +a
venv/bin/python main.py
```

## Install systemd service

Adjust the user and paths in `deploy/botfather-repost.service.example`, then:

```bash
sudo cp deploy/botfather-repost.service.example /etc/systemd/system/botfather-repost.service
sudo systemctl daemon-reload
sudo systemctl enable --now botfather-repost.service
journalctl -u botfather-repost.service -f -l
```

## Configure reposting

Open `/admin`, add a source-target pair, add the userbot session, choose
`Start From First` or `Start From Latest`, then choose `Interval 30 Min` or
`Interval 1 Hour` for that pair.

Never commit `.env`, session files, logs, downloads, or database exports.
