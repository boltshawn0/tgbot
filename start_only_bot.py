# start_only_bot.py
# Final clean version: uses VIDEO_FILE_ID (instant CDN), no logger, no URL fallback.

import os, sys, textwrap
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ====== ENV / LINKS ======
BOT_TOKEN = os.environ["BOT_TOKEN"]

INVITE_PRIVATE = "https://t.me/+58QPoYPAYKo5ZDdh"   # Private (vault)
INVITE_OTHER   = "https://t.me/+UHH0jKOrMm5hOTcx"   # Candids/Spycams
INVITE_PUBLIC  = "https://t.me/+l0Tv1KBIXcs5MzFh"   # Public previews

# ====== MEDIA ======
VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"   # must be set in Railway
OTHER_VIDEO_LOCAL = "teaser2.mp4"     # make sure this file exists
PUBLIC_PHOTO_LOCAL = "photo1.jpg"     # make sure this file exists

# ====== CAPTIONS ======
CAPTION_PRIVATE = (
    "🔒 400+ Models | 125,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $10 USD\n\n"
    f"⭐ Join here: {INVITE_PRIVATE}"
)
CAPTION_OTHER = (
    "✨ Candids & Spycams ✨\n\n"
    "Exclusive extras and more content 🔥\n\n"
    f"⭐ Join here: {INVITE_OTHER}"
)
CAPTION_PUBLIC = (
    "✨ TengokuHub – Public ✨\n"
    "Previews & teasers only. Full collection (400+ models, 125K+ media) in the Private Vault.\n\n"
    f"⭐ Join here: {INVITE_PUBLIC}"
)

START_FOLLOWUP = textwrap.dedent("""\
Choose what to check out next ⬇️

📸 Public previews
📂 Candids & Spycams
🗂 /models — Browse Models list
""")

# ====== Keyboards ======
def kb_private():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join", url=INVITE_PRIVATE)]])
def kb_other():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join", url=INVITE_OTHER)]])
def kb_public():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join Public", url=INVITE_PUBLIC)]])
def kb_start_options():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Public previews", url=INVITE_PUBLIC)],
        [InlineKeyboardButton("📂 Candids & Spycams (preview)", callback_data="show_other_preview")]
    ])

# ====== COMMANDS ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1) Private video first (instant from file_id)
    file_id = os.environ.get(VIDEO_FILE_ID_ENV, "").strip()
    if not file_id:
        await update.message.reply_text("⚠️ VIDEO_FILE_ID is not set. Please set it in Railway env.")
        return
    await update.message.reply_video(file_id, caption=CAPTION_PRIVATE, reply_markup=kb_private())
    # 2) Options (no “you’re in”)
    await update.message.reply_text(START_FOLLOWUP, reply_markup=kb_start_options())

async def private_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = os.environ.get(VIDEO_FILE_ID_ENV, "").strip()
    await update.message.reply_video(file_id, caption=CAPTION_PRIVATE, reply_markup=kb_private())

async def other_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(OTHER_VIDEO_LOCAL, "rb") as f:
        await update.message.reply_video(f, caption=CAPTION_OTHER, reply_markup=kb_other())

async def public_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(PUBLIC_PHOTO_LOCAL, "rb") as f:
        await update.message.reply_photo(f, caption=CAPTION_PUBLIC, reply_markup=kb_public())

async def models_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("models.txt", "r", encoding="utf-8") as f:
            models = [line.strip() for line in f if line.strip()]
        models = sorted(set(models), key=lambda s: s.lower())
        half = len(models) // 2
        await update.message.reply_text("📂 Private Vault Models (Part 1):\n" + ", ".join(models[:half]))
        await update.message.reply_text("📂 Private Vault Models (Part 2):\n" + ", ".join(models[half:]))
    except Exception as e:
        await update.message.reply_text(f"[models failed] {e}")

# ====== CALLBACKS ======
async def crypto_info_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    msg = (
        "💳 *Pay with Crypto ($10)*\n\n"
        "*BTC*: `bc1q4qwnx9dvxczm6kuk084z6dh0ae4c9we8lv6cs2`\n"
        "*ETH*: `0x8ae4799098dbf5dC637d3993E0ad66e977A158A7`\n"
        "*SOL*: `3wmTEKgEFEexCTbsHzKqbUAUePDw7Rcr2KR3TvTyxuCh`\n\n"
        "After sending, DM *@jordancarter005* with a screenshot to receive your 1 month invite link."
    )
    await q.message.reply_text(msg, disable_web_page_preview=True, parse_mode="Markdown")

async def show_other_preview_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    with open(OTHER_VIDEO_LOCAL, "rb") as f:
        await q.message.reply_video(f, caption=CAPTION_OTHER, reply_markup=kb_other())

# ====== MAIN ======
def main():
    print("Booting bot…", flush=True)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("private", private_cmd))
    app.add_handler(CommandHandler("other", other_cmd))
    app.add_handler(CommandHandler("public", public_cmd))
    app.add_handler(CommandHandler("models", models_cmd))
    app.add_handler(CallbackQueryHandler(crypto_info_cb, pattern=r"^crypto_info$"))
    app.add_handler(CallbackQueryHandler(show_other_preview_cb, pattern=r"^show_other_preview$"))
    print("Starting polling…", flush=True)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}", file=sys.stderr)
        raise
