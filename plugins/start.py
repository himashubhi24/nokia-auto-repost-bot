#(©)CodeXBotz




import os
import asyncio
import json
import urllib.request
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, WEBAPP_URL, WEBAPP_API_SECRET, VERIFY_MSG
from helper_func import subscribed, encode, decode, get_messages
from database.database import (
    add_user,
    del_user,
    full_userbase,
    get_batch,
    get_file,
    list_force_sub_channels,
    increment_downloads,
    is_user_verified,
    mark_user_verified,
    present_user,
)

async def auto_delete_message(msg, delay=60):
    try:
        await asyncio.sleep(delay)
        await msg.delete()
    except:
        pass


async def send_saved_file(client, chat_id, file_doc):
    caption = file_doc.get("file_name") or ""
    file_type = file_doc.get("file_type")
    file_id = file_doc.get("file_id")
    if file_type == "photo":
        return await client.send_photo(chat_id, file_id, caption=caption, protect_content=PROTECT_CONTENT)
    if file_type == "video":
        return await client.send_video(chat_id, file_id, caption=caption, protect_content=PROTECT_CONTENT)
    if file_type == "audio":
        return await client.send_audio(chat_id, file_id, caption=caption, protect_content=PROTECT_CONTENT)
    if file_type == "animation":
        return await client.send_animation(chat_id, file_id, caption=caption, protect_content=PROTECT_CONTENT)
    return await client.send_document(chat_id, file_id, caption=caption, protect_content=PROTECT_CONTENT)


async def get_client_username(client):
    username = getattr(client, "username", None)
    if username:
        return username
    me = await client.get_me()
    username = me.username
    try:
        client.username = username
    except Exception:
        pass
    return username


async def send_verification_prompt(client, message, payload):
    user_id = message.from_user.id
    if not WEBAPP_URL:
        await message.reply_text("Verification web app is not configured. Ask admin to set WEBAPP_URL.")
        return
    verify_url = f"{WEBAPP_URL.rstrip('/')}/?file_id={payload}"
    bot_username = await get_client_username(client)
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Verify Access", web_app=WebAppInfo(url=verify_url))],
            [InlineKeyboardButton("Try Again After Verify", url=f"https://t.me/{bot_username}?start={payload}")],
        ]
    )
    try:
        await message.reply_text(VERIFY_MSG, reply_markup=markup, disable_web_page_preview=True)
    except Exception:
        await message.reply_text(
            VERIFY_MSG,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Verify Access", url=verify_url)],
                    [InlineKeyboardButton("Try Again After Verify", url=f"https://t.me/{bot_username}?start={payload}")],
                ]
            ),
            disable_web_page_preview=True,
        )


async def external_webapp_verified(user_id, payload):
    if not WEBAPP_URL or not WEBAPP_API_SECRET:
        return False

    def check():
        data = json.dumps({"user_id": int(user_id), "file_id": payload}).encode("utf-8")
        req = urllib.request.Request(
            f"{WEBAPP_URL.rstrip('/')}/api/check",
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Secret": WEBAPP_API_SECRET,
            },
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))

    try:
        result = await asyncio.to_thread(check)
    except Exception:
        return False
    return bool(result.get("clicked") or result.get("verified"))





@Bot.on_message(filters.command('start') & filters.private & subscribed)
async def start_command(client: Client, message: Message):
    asyncio.create_task(auto_delete_message(message, 60))
    id = message.from_user.id
    if not await present_user(id):
        try:
            await add_user(id, message.from_user.username, message.from_user.first_name)
        except:
            pass
    text = message.text
    if len(text)>7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        verified = await is_user_verified(id)
        if not verified and await external_webapp_verified(id, base64_string):
            await mark_user_verified(id)
            verified = True
        if not verified:
            await send_verification_prompt(client, message, base64_string)
            return
        if base64_string == "verify":
            await message.reply_text("Verification active for 4 hours. Open any file link now.")
            return
        string = await decode(base64_string)
        if string.startswith("batch-"):
            batch = await get_batch(string.split("-", 1)[1])
            if not batch:
                await message.reply_text("Batch not found or expired.")
                return
            temp_msg = await message.reply("Please wait...")
            for file_doc in batch.get("files", []):
                try:
                    sent_media = await send_saved_file(client, message.from_user.id, file_doc)
                    asyncio.create_task(auto_delete_message(sent_media, 120))
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                except Exception:
                    pass
            await increment_downloads(id, len(batch.get("files", [])))
            await temp_msg.delete()
            return
        if string.startswith("file-"):
            file_doc = await get_file(string.split("-", 1)[1])
            if not file_doc:
                await message.reply_text("File not found or expired.")
                return
            sent_media = await send_saved_file(client, message.from_user.id, file_doc)
            asyncio.create_task(auto_delete_message(sent_media, 120))
            await increment_downloads(id, 1)
            return
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start,end+1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return
        temp_msg = await message.reply("Please wait...")
        asyncio.create_task(auto_delete_message(temp_msg, 60))
        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        for msg in messages:

            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption = "" if not msg.caption else msg.caption.html, filename = msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                sent_media = await msg.copy(chat_id=message.from_user.id, caption = caption, parse_mode = ParseMode.HTML, reply_markup = reply_markup, protect_content=PROTECT_CONTENT)
                asyncio.create_task(auto_delete_message(sent_media, 120))
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                sent_media = await msg.copy(chat_id=message.from_user.id, caption = caption, parse_mode = ParseMode.HTML, reply_markup = reply_markup, protect_content=PROTECT_CONTENT)
                asyncio.create_task(auto_delete_message(sent_media, 120))
            except:
                pass
        await increment_downloads(id, len(messages))
        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data = "about"),
                    InlineKeyboardButton("🔒 Close", callback_data = "close")
                ]
            ]
        )
        start_msg = await message.reply_text(
            text = START_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
            reply_markup = reply_markup,
            disable_web_page_preview = True,
            quote = True
        )
        asyncio.create_task(auto_delete_message(start_msg, 60))
        return

    
#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

#=====================================================================================##

    
    
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    asyncio.create_task(auto_delete_message(message, 60))
    buttons = [[InlineKeyboardButton(data["title"], url=data["link"])] for data in getattr(client, "force_sub_links", {}).values()]
    for item in await list_force_sub_channels():
        try:
            chat = await client.get_chat(item["channel_id"])
            link = chat.invite_link or await client.export_chat_invite_link(item["channel_id"])
            buttons.append([InlineKeyboardButton(chat.title or str(item["channel_id"]), url=link)])
        except Exception:
            pass
    if not buttons and getattr(client, "invitelink", None):
        buttons = [[InlineKeyboardButton("Join Channel", url=client.invitelink)]]
    bot_username = await get_client_username(client)
    try:
        retry_url = f"https://t.me/{bot_username}?start={message.command[1]}"
    except IndexError:
        retry_url = f"https://t.me/{bot_username}?start=verify"
    buttons.append(
        [
            InlineKeyboardButton(
                text='Try Again',
                url=retry_url,
            )
        ]
    )

    join_msg = await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )
    asyncio.create_task(auto_delete_message(join_msg, 60))

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
