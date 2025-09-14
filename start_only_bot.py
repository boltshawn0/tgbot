# start_only_bot.py
# Telegram bot: sends your teaser video + promo caption + JOIN button on /start.
# Works as a Railway "Worker" service.

import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# 🔐 Set BOT_TOKEN in Railway → Service → Variables (do NOT hard-code it here)
BOT_TOKEN = os.environ["BOT_TOKEN"]

# 🎯 Your links
INVITE_LINK = "https://t.me/+pCkQCqhHoOFlZmMx"
VIDEO_SRC   = "teaser.mp4"

CAPTION = (
    "350+ Models | 100,000+ Media 🔒\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW DONT MISS OUT! 🚀\n\n"
    "🗓MONTHLY SUBSCRIPTION — 500 STARS / $5 USD\n"
    "⭐PAY WITH STARS HERE:\n\n"
    f"{INVITE_LINK}"
)

def join_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join / Pay with Stars", url=INVITE_LINK)]])

async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_video(
        video=VIDEO_SRC,                 # Direct URL to your Dropbox file (dl=1)
        caption=CAPTION,
        reply_markup=join_keyboard(),
        parse_mode=ParseMode.HTML,
        supports_streaming=True,
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    # Simple, blocking loop (no updater.idle needed)
    app.run_polling(allowed_updates=None)

if __name__ == "__main__":
    main()
