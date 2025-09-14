# start_only_bot.py
# Sends your teaser video + caption + JOIN button when a user taps /start.

import os, asyncio
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# Bot token comes from Railway environment variable (keep secret, don’t hard-code!)
BOT_TOKEN   = os.environ["BOT_TOKEN"]

# Hard-coded invite link + video source
INVITE_LINK = "https://t.me/+pCkQCqhHoOFlZmMx"
VIDEO_SRC   = "https://www.dropbox.com/scl/fi/ivwazkb0dsuepz7au8mpm/teaser.mov?rlkey=eu90ygj5z3rs31x9awgj6hin4&st=px9dyq33&dl=1"

CAPTION = (
    "350+ Models | 100,000+ Media 🔒\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW DONT MISS OUT! 🚀\n\n"
    "🗓MONTHLY SUBSCRIPTION — 500 STARS / $5 USD\n"
    "⭐PAY WITH STARS HERE:\n\n"
    f"{INVITE_LINK}"
)

def join_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join / Pay with Stars", url=INVITE_LINK)]])

async def start_cmd(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_video(
        video=VIDEO_SRC,
        caption=CAPTION,
        reply_markup=join_keyboard(),
        parse_mode=ParseMode.HTML,
        supports_streaming=True,
    )

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    await app.initialize()
    await app.start()
    print("✅ Bot is running on Railway. Waiting for /start…")
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
