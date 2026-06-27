from pyrogram import Client

api_id = 25674626
api_hash = "28e65eaa64a572e5a955b0bb17a15204"

with Client("userbot_session", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    print("\nSESSION_STRING:\n")
    print(app.export_session_string())
