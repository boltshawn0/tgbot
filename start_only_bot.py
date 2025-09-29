# start_only_bot.py
# Final clean version: uses VIDEO_FILE_ID (instant CDN), no logger, no URL fallback.
# Final version: VIDEO_FILE_ID (instant), /start guarded, Crypto button on /private and /other.

import os, sys, textwrap
import os, sys, textwrap, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# ====== ENV / LINKS ======
BOT_TOKEN = os.environ["BOT_TOKEN"]
@@ -13,9 +13,9 @@   # Public previews

# ====== MEDIA ======
VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"   # must be set in Railway
OTHER_VIDEO_LOCAL = "teaser2.mp4"     # make sure this file exists
PUBLIC_PHOTO_LOCAL = "photo1.jpg"     # make sure this file exists
VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"   # must be set in Railway (Telegram file_id)
OTHER_VIDEO_LOCAL = "teaser2.mp4"     # ensure exists in app dir
PUBLIC_PHOTO_LOCAL = "photo1.jpg"     # ensure exists in app dir

# ====== CAPTIONS ======
CAPTION_PRIVATE = (
@@ -45,11 +45,20 @@

# ====== Keyboards ======
def kb_private():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join", url=INVITE_PRIVATE)]])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Join via Stars", url=INVITE_PRIVATE)],
        [InlineKeyboardButton("💳 Pay with Crypto ($10)", callback_data="crypto_info")]
    ])

def kb_other():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join", url=INVITE_OTHER)]])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Join via Stars", url=INVITE_OTHER)],
        [InlineKeyboardButton("💳 Pay with Crypto ($10)", callback_data="crypto_info")]
    ])

def kb_public():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join Public", url=INVITE_PUBLIC)]])

def kb_start_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Public previews", url=INVITE_PUBLIC)],
@@ -58,11 +67,19 @@ def kb_start_options():

# ====== COMMANDS ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1) Private video first (instant from file_id)
    # Dedupe: ignore if /start ran in the last 5s for this user
    now = time.time()
    last = context.user_data.get("last_start_ts", 0)
    if now - last < 5:
        return
    context.user_data["last_start_ts"] = now

    file_id = os.environ.get(VIDEO_FILE_ID_ENV, "").strip()
    if not file_id:
        await update.message.reply_text("⚠️ VIDEO_FILE_ID is not set. Please set it in Railway env.")
        await update.message.reply_text("⚠️ VIDEO_FILE_ID is not set. Set it in Railway env.")
        return

    # 1) Private video first (with Stars + Crypto buttons)
    await update.message.reply_video(file_id, caption=CAPTION_PRIVATE, reply_markup=kb_private())
    # 2) Options (no “you’re in”)
    await update.message.reply_text(START_FOLLOWUP, reply_markup=kb_start_options())
@@ -113,13 +130,18 @@ async def show_other_preview_cb(update: Update, context: ContextTypes.DEFAULT_TY
def main():
    print("Booting bot…", flush=True)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("private", private_cmd))
    app.add_handler(CommandHandler("other", other_cmd))
    app.add_handler(CommandHandler("public", public_cmd))
    app.add_handler(CommandHandler("models", models_cmd))

    private_only = filters.ChatType.PRIVATE

    app.add_handler(CommandHandler("start", start_cmd, filters=private_only))
    app.add_handler(CommandHandler("private", private_cmd, filters=private_only))
    app.add_handler(CommandHandler("other", other_cmd, filters=private_only))
    app.add_handler(CommandHandler("public", public_cmd, filters=private_only))
    app.add_handler(CommandHandler("models", models_cmd, filters=private_only))

    app.add_handler(CallbackQueryHandler(crypto_info_cb, pattern=r"^crypto_info$"))
    app.add_handler(CallbackQueryHandler(show_other_preview_cb, pattern=r"^show_other_preview$"))

    print("Starting polling…", flush=True)
    app.run_polling(drop_pending_updates=True)
