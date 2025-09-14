# start_only_bot.py
# Sends your teaser with animated custom emojis.
# Uses VIDEO_FILE_ID (env var) for instant sends; falls back to upload once and prints the file_id.

import os, sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import Application, CommandHandler
from telegram.constants import MessageEntityType

# ---- Config / Env ----
BOT_TOKEN = os.environ["BOT_TOKEN"]                       # set in Railway → Service → Variables
INVITE_LINK = "https://t.me/+pCkQCqhHoOFlZmMx"
VIDEO_SRC = "teaser.mp4"                                  # used only if we don't have VIDEO_FILE_ID yet
VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"                       # set this in Railway after first upload

# ---- Custom emoji IDs (from your RawDataBot dumps) ----
LOCK_ID   = "5296369303661067030"   # 🔒
FIRE_ID   = "5289722755871162900"   # 🔥 (black)
STAR_ID   = "5267500801240092311"   # ⭐
ROCKET_ID = "5188481279963715781"   # 🚀
CAL_ID    = "5472026645659401564"   # 🗓

# ---- Caption with normal emoji (we'll map them to animated) ----
CAPTION = (
    "🔒 350+ Models | 100,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW DONT MISS OUT! 🚀\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $5 USD\n"
    "⭐ PAY WITH STARS HERE:\n\n"
    f"{INVITE_LINK}"
)

EMOJI_ID_MAP = {"🔒": LOCK_ID, "🔥": FIRE_ID, "⭐": STAR_ID, "🚀": ROCKET_ID, "🗓": CAL_ID}

def build_custom_emoji_entities_utf16(text: str):
    """
    Build caption entities with correct UTF-16 offsets/lengths so Telegram
    accepts animated custom emojis (avoids 'utf-16 offset' errors).
    """
    ents = []
    offset_utf16 = 0
    for ch in text:
        ch_units = len(ch.encode("utf-16-le")) // 2  # number of UTF-16 code units
        if ch in EMOJI_ID_MAP:
            ents.append(
                MessageEntity(
                    type=MessageEntityType.CUSTOM_EMOJI,
                    offset=offset_utf16,
                    length=ch_units,  # often 2 for emoji (surrogate pair)
                    custom_emoji_id=EMOJI_ID_MAP[ch],
                )
            )
        offset_utf16 += ch_units
    return ents

def join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⭐ Join / Pay with Stars", url=INVITE_LINK)]]
    )

async def start_cmd(update, context):
    caption_entities = build_custom_emoji_entities_utf16(CAPTION)

    # 1) Try permanent VIDEO_FILE_ID first (instant for everyone; survives redeploys)
    file_id = os.environ.get(VIDEO_FILE_ID_ENV, "").strip()
    if file_id:
        try:
            await update.message.reply_video(
                video=file_id,
                caption=CAPTION,
                caption_entities=caption_entities,   # animated custom emojis
                reply_markup=join_keyboard(),
                supports_streaming=True,
            )
            return
        except Exception as e:
            print(f"[file_id send failed] {e} — falling back to upload", flush=True)

    # 2) Upload once, then print the file_id so you can store it in Railway
    try:
        with open(VIDEO_SRC, "rb") as f:
            msg = await update.message.reply_video(
                video=f,
                caption=CAPTION,
                caption_entities=caption_entities,
                reply_markup=join_keyboard(),
                supports_streaming=True,
            )
        if msg and msg.video and msg.video.file_id:
            fid = msg.video.file_id
            print(f"[SAVE THIS] Set {VIDEO_FILE_ID_ENV}={fid} in Railway → Service → Variables", flush=True)
    except Exception as e:
        print(f"[upload failed] {e}", flush=True)
        # Fallback: send text with animated emojis so CTA still shows
        try:
            await update.message.reply_text(
                CAPTION,
                entities=caption_entities,
                reply_markup=join_keyboard(),
            )
        except Exception as e2:
            print(f"[send_text failed] {e2}", flush=True)
            await update.message.reply_text(CAPTION, reply_markup=join_keyboard())

def main():
    print("Booting bot…", flush=True)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    print("Starting polling…", flush=True)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}. Did you set BOT_TOKEN on Railway?", file=sys.stderr)
        raise
