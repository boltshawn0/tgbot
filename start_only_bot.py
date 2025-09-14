# start_only_bot.py
# Telegram bot: sends your teaser video + promo caption + JOIN button on /start.
# - Uses local file "teaser.mp4" (keep it < ~20 MB for bot upload)
# - Replaces specific emoji in the caption with Telegram *animated custom emojis*
# - Works great on Railway with Start Command: `python -u start_only_bot.py`

import os
import sys
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode

# 🔐 Get your token from Railway Service → Variables (BOT_TOKEN)
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 🎯 Links / assets
INVITE_LINK = "https://t.me/+pCkQCqhHoOFlZmMx"
VIDEO_SRC   = "teaser.mp4"  # local file in your repo (keep under ~20 MB)

# 🧩 Your custom_emoji_id values (from RawDataBot outputs you sent)
LOCK_ID   = "5296369303661067030"   # 🔒
FIRE_ID   = "5289722755871162900"   # black fire 🔥
STAR_ID   = "5267500801240092311"   # ⭐
ROCKET_ID = "5188481279963715781"   # 🚀
CAL_ID    = "5472026645659401564"   # 🗓 (spiral calendar)

# ✍️ Caption text — put normal emoji where you want animated ones
CAPTION = (
    "🔒 350+ Models | 100,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW DONT MISS OUT! 🚀\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $5 USD\n"
    "⭐ PAY WITH STARS HERE:\n\n"
    f"{INVITE_LINK}"
)

# Map the visible characters to their animated custom_emoji_id
EMOJI_ID_MAP = {
    "🔒": LOCK_ID,
    "🔥": FIRE_ID,
    "⭐": STAR_ID,
    "🚀": ROCKET_ID,
    "🗓": CAL_ID,
}

def build_custom_emoji_entities(text: str) -> list[MessageEntity]:
    """Attach custom_emoji IDs to each matching emoji in text."""
    entities: list[MessageEntity] = []
    i = 0
    # NOTE: This simple scan works because we only target single-codepoint emoji above.
    while i < len(text):
        ch = text[i]
        if ch in EMOJI_ID_MAP:
            entities.append(
                MessageEntity(
                    type="custom_emoji",
                    offset=i,
                    length=1,
                    custom_emoji_id=EMOJI_ID_MAP[ch],
                )
            )
        i += 1
    return entities

def join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⭐ Join / Pay with Stars", url=INVITE_LINK)]]
    )

async def start_cmd(update, context):
    caption_entities = build_custom_emoji_entities(CAPTION)
    try:
        # Send local file (bots must keep this under ~20 MB or Telegram will 413)
        with open(VIDEO_SRC, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption=CAPTION,
                caption_entities=caption_entities,   # <-- animated custom emoji
                reply_markup=join_keyboard(),
                parse_mode=ParseMode.HTML,
                supports_streaming=True,
            )
    except Exception as e:
        # Fallback: still send caption with animated emoji + button
        print(f"[send_video] failed: {e}", flush=True)
        await update.message.reply_text(
            CAPTION,
            reply_markup=join_keyboard(),
            entities=caption_entities,
            parse_mode=ParseMode.HTML,
        )

def main():
    print("Booting bot…", flush=True)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    print("Starting polling…", flush=True)
    # drop_pending_updates=True avoids old queue conflicts after restarts
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}. Did you set BOT_TOKEN on Railway?", file=sys.stderr)
        raise
