# start_only_bot.py
# Sends your teaser + promo with animated custom emoji and caches file_id for speed.

import os, sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import Application, CommandHandler
from telegram.constants import MessageEntityType  # <-- important for custom emoji

# 🔐 Token from Railway → Service → Variables
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 🎯 Links / assets
INVITE_LINK = "https://t.me/+pCkQCqhHoOFlZmMx"
VIDEO_SRC   = "teaser.mp4"      # keep under ~20 MB for bot upload
FILE_ID_CACHE = "video_id.txt"  # caches Telegram file_id after first upload

# 🧩 Your custom_emoji_id values
LOCK_ID   = "5296369303661067030"   # 🔒
FIRE_ID   = "5289722755871162900"   # black fire 🔥
STAR_ID   = "5267500801240092311"   # ⭐
ROCKET_ID = "5188481279963715781"   # 🚀
CAL_ID    = "5472026645659401564"   # 🗓

# ✍️ Caption (use normal emoji; we’ll map them to animated)
CAPTION = (
    "🔒 350+ Models | 100,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW DONT MISS OUT! 🚀\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $5 USD\n"
    "⭐ PAY WITH STARS HERE:\n\n"
    f"{INVITE_LINK}"
)

EMOJI_ID_MAP = {
    "🔒": LOCK_ID,
    "🔥": FIRE_ID,
    "⭐": STAR_ID,
    "🚀": ROCKET_ID,
    "🗓": CAL_ID,
}

def build_custom_emoji_entities(text: str) -> list[MessageEntity]:
    ents: list[MessageEntity] = []
    for i, ch in enumerate(text):
        if ch in EMOJI_ID_MAP:
            ents.append(MessageEntity(
                type=MessageEntityType.CUSTOM_EMOJI,
                offset=i, length=1,
                custom_emoji_id=EMOJI_ID_MAP[ch],
            ))
    return ents

def join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⭐ Join / Pay with Stars", url=INVITE_LINK)]]
    )

# ---- file_id cache (makes replies instant after first upload) ----
def load_cached_file_id():
    try:
        with open(FILE_ID_CACHE, "r") as f:
            v = f.read().strip()
            return v or None
    except FileNotFoundError:
        return None

def save_cached_file_id(file_id: str):
    try:
        with open(FILE_ID_CACHE, "w") as f:
            f.write(file_id)
    except Exception as e:
        print(f"[cache] write failed: {e}", flush=True)

# ---- handlers ----
async def start_cmd(update, context):
    caption_entities = build_custom_emoji_entities(CAPTION)

    # 1) Try near-instant send using cached file_id
    file_id = load_cached_file_id()
    if file_id:
        try:
            await update.message.reply_video(
                video=file_id,
                caption=CAPTION,
                caption_entities=caption_entities,   # animated emoji
                reply_markup=join_keyboard(),
                supports_streaming=True,
            )
            return
        except Exception as e:
            print(f"[send by file_id] failed, fallback to upload: {e}", flush=True)

    # 2) First time: upload file, then cache the returned file_id
    try:
        with open(VIDEO_SRC, "rb") as f:
            msg = await update.message.reply_video(
                video=f,
                caption=CAPTION,
                caption_entities=caption_entities,   # animated emoji
                reply_markup=join_keyboard(),
                supports_streaming=True,
            )
        if msg and msg.video and msg.video.file_id:
            save_cached_file_id(msg.video.file_id)
    except Exception as e:
        print(f"[upload] failed: {e}", flush=True)
        # Fallback: still show caption with animated emoji
        await update.message.reply_text(
            CAPTION,
            entities=caption_entities,              # animated emoji in text
            reply_markup=join_keyboard(),
        )

def main():
    print("Booting bot…", flush=True)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    print("Starting polling…", flush=True)
    app.run_polling(drop_pending_updates=True)  # clears stale queue on restart

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}. Did you set BOT_TOKEN on Railway?", file=sys.stderr)
        raise
