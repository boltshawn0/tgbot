# start_only_bot.py
# Telegram bot with:
# - /start (intro menu + private promo)
# - /private (promo.mov promo)
# - /public  (photo + Join button)
# - /other   (teaser2.mp4 + Join button)
# - /models  (loads from models.txt, deduped + alphabetized)
# - "💳 Pay with Crypto" button -> shows your wallet addresses & DM instruction

import os, sys, textwrap
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ====== ENV / LINKS ======
BOT_TOKEN = os.environ["BOT_TOKEN"]

INVITE_PRIVATE = "https://t.me/+58QPoYPAYKo5ZDdh"   # Private (vault)
INVITE_OTHER   = "https://t.me/+UHH0jKOrMm5hOTcx"   # Other channel
INVITE_PUBLIC  = "https://t.me/+l0Tv1KBIXcs5MzFh"   # Public channel

# ====== MEDIA ======
PRIVATE_VIDEO_URL = "https://github.com/boltshawn0/tgbot/releases/download/asset/promo.mov"  # <-- promo.mov

OTHER_VIDEO_LOCAL = "teaser2.mp4"
PUBLIC_PHOTO_LOCAL = "photo1.jpg"

# ====== CAPTIONS ======
CAPTION_PRIVATE = (
    "🔒 400+ Models | 125,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW — DON'T MISS OUT CURRENTLY 25% OFF! 🚀\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $10 USD\n"
    f"⭐ PAY WITH STARS HERE:\n{INVITE_PRIVATE}"
)

CAPTION_OTHER = (
    "✨ Explore our Candids and Spycams channel ✨\n\n"
    "Exclusive extras and more content 🔥\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $10 USD\n"
    "DON'T MISS OUT CURRENTLY 25% OFF!"
)

CAPTION_PUBLIC = (
    "✨ TengokuHub – Public ✨\n"
    "This channel shares previews & teasers only 🔥\n\n"
    "The full collection (400+ models, 125K+ media) is inside the Private Vault.\n"
    f"⭐ Join here: {INVITE_PUBLIC}"
)

INTRO_MENU = textwrap.dedent("""\
               ✨ Welcome to TengokuHub Bot! ✨
Choose a command below to explore ⬇️

🔒 /private — Access the Private Vault (25% OFF SALE!)
📂 /other   — Check out our Candid and Spycam Channel (25% OFF SALE!)
📸 /public  — Join the Public Previews channel
🗂 /models  — Browse the Private Vault Models
""")

# ====== Keyboards ======
def kb_private():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join", url=INVITE_PRIVATE)]])
def kb_other():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join", url=INVITE_OTHER)]])
def kb_public():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join Public", url=INVITE_PUBLIC)]])

# ====== COMMANDS ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO_MENU)

async def private_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Always send promo.mov from GitHub
    await update.message.reply_video(PRIVATE_VIDEO_URL, caption=CAPTION_PRIVATE, reply_markup=kb_private())

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
    print("Starting polling…", flush=True)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}", file=sys.stderr)
        raise
