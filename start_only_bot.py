# start_only_bot.py
# Final clean version: uses VIDEO_FILE_ID (instant CDN), /start guarded, Crypto button on /private and /other.
import os, sys, textwrap, time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters

# ====== ENV / LINKS ======
BOT_TOKEN = os.environ["BOT_TOKEN"]

INVITE_PRIVATE = "https://t.me/+58QPoYPAYKo5ZDdh"   # Private (vault)
INVITE_OTHER   = "https://t.me/+UHH0jKOrMm5hOTcx"   # Candids/Spycams

# ====== MEDIA ======
VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"   # must be set in Railway (Telegram file_id)
OTHER_VIDEO_LOCAL = "teaser2.mp4"     # ensure exists in app dir

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

START_FOLLOWUP = textwrap.dedent("""\
Choose what to check out next ⬇️

📂 Candids & Spycams
🗂 /models — Browse Models list
""")


# 1) imports (top of file)
from telegram.ext import MessageHandler, filters

# 2) temp logger function (anywhere above main())
async def _log_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.video:
        print("[SAVE THIS] VIDEO_FILE_ID =", update.message.video.file_id, flush=True)

# 3) register it (inside main(), after other handlers)
app.add_handler(MessageHandler(filters.VIDEO, _log_video_id))


# ====== Keyboards ======
def kb_private():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Join via Stars", url=INVITE_PRIVATE)],
        [InlineKeyboardButton("💳 Pay with Crypto ($10)", callback_data="crypto_info")]
    ])

def kb_other():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Join via Stars", url=INVITE_OTHER)],
        [InlineKeyboardButton("💳 Pay with Crypto ($10)", callback_data="crypto_info")]
    ])

def kb_start_options():
    # Only Candids preview button (no public)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Candids & Spycams (preview)", callback_data="show_other_preview")]
    ])

# ====== COMMANDS ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Dedupe: ignore if /start ran in the last 5s for this user
    now = time.time()
    last = context.user_data.get("last_start_ts", 0)
    if now - last < 5:
        return
    context.user_data["last_start_ts"] = now

    file_id = os.environ.get(VIDEO_FILE_ID_ENV, "").strip()
    if not file_id:
        await update.message.reply_text("⚠️ VIDEO_FILE_ID is not set. Set it in Railway env.")
        return

    # 1) Private video first (with Stars + Crypto buttons)
    await update.message.reply_video(file_id, caption=CAPTION_PRIVATE, reply_markup=kb_private())
    # 2) Options (no public)
    await update.message.reply_text(START_FOLLOWUP, reply_markup=kb_start_options())

async def private_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = os.environ.get(VIDEO_FILE_ID_ENV, "").strip()
    await update.message.reply_video(file_id, caption=CAPTION_PRIVATE, reply_markup=kb_private())

async def other_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open(OTHER_VIDEO_LOCAL, "rb") as f:
        await update.message.reply_video(f, caption=CAPTION_OTHER, reply_markup=kb_other())

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

    private_only = filters.ChatType.PRIVATE

    app.add_handler(CommandHandler("start", start_cmd, filters=private_only))
    app.add_handler(CommandHandler("private", private_cmd, filters=private_only))
    app.add_handler(CommandHandler("other", other_cmd, filters=private_only))
    app.add_handler(CommandHandler("models", models_cmd, filters=private_only))

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
