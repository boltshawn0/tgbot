# start_only_bot.py
# Clean + robust: no Public, Crypto buttons on /private and /other, /start guarded,
# file_id first (instant), safe fallback to GitHub URL if file_id missing/invalid.
import os, sys, textwrap, time, traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,      
    ChatMemberHandler,   # listen for joins
    filters,
)

# ====== ENV / LINKS ======
BOT_TOKEN = os.environ["BOT_TOKEN"]
INVITE_PRIVATE = "https://t.me/+58QPoYPAYKo5ZDdh"   # Private (vault)
INVITE_OTHER   = "https://t.me/+UHH0jKOrMm5hOTcx"   # Candids/Spycams

# Secret DM target for join pings (your numeric Telegram ID stored in env as FILES_ID)
FILES_ID = int((os.environ.get("FILES_ID") or "0").strip() or "0")

# ====== MEDIA ======
VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"                        
PRIVATE_VIDEO_URL = "https://github.com/boltshawn0/tgbot/releases/download/asset/promo.mp4"  
OTHER_VIDEO_LOCAL = "teaser2.mp4"                          

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

📂 /other - Candids & Spycams
🗂 /models — Browse Models list
""")

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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📂 Candids & Spycams", callback_data="show_other_preview")]
    ])

# ====== Helpers ======
def _get_file_id() -> str:
    return (os.environ.get(VIDEO_FILE_ID_ENV) or "").strip().strip('"').strip("'")

async def _send_private_video(msg, caption: str):
    file_id = _get_file_id()
    if file_id:
        try:
            return await msg.reply_video(file_id, caption=caption, reply_markup=kb_private())
        except Exception as e:
            print(f"[private video] file_id failed: {e}", flush=True)
    try:
        return await msg.reply_video(PRIVATE_VIDEO_URL, caption=caption, reply_markup=kb_private())
    except Exception as e:
        print(f"[private video] URL fallback failed: {e}", flush=True)
        return await msg.reply_text("⚠️ Video temporarily unavailable. Please try again shortly.")

# ====== COMMANDS ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = time.time()
    last = context.user_data.get("last_start_ts", 0)
    if now - last < 5:
        return
    context.user_data["last_start_ts"] = now

    await _send_private_video(update.message, CAPTION_PRIVATE)
    await update.message.reply_text(START_FOLLOWUP, reply_markup=kb_start_options())

async def private_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_private_video(update.message, CAPTION_PRIVATE)

async def other_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(OTHER_VIDEO_LOCAL, "rb") as f:
            await update.message.reply_video(f, caption=CAPTION_OTHER, reply_markup=kb_other())
    except Exception as e:
        print(f"[other video] local send failed: {e}", flush=True)
        await update.message.reply_text("⚠️ Teaser unavailable right now. Please try again.")

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
        "After sending, DM *@TengokuGoon* with a screenshot to receive your 1 month invite link."
    )
    await q.message.reply_text(msg, disable_web_page_preview=True, parse_mode="Markdown")

async def show_other_preview_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    try:
        with open(OTHER_VIDEO_LOCAL, "rb") as f:
            await q.message.reply_video(f, caption=CAPTION_OTHER, reply_markup=kb_other())
    except Exception as e:
        print(f"[other preview] local send failed: {e}", flush=True)
        await q.message.reply_text("⚠️ Teaser unavailable right now. Please try again.")

# ====== JOIN PINGS (DM only to FILES_ID) ======
async def member_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FILES_ID:
        return

    cmu = update.chat_member
    old_status = cmu.old_chat_member.status
    new_status = cmu.new_chat_member.status
    user = cmu.from_user

    try:
        if old_status in ("left", "kicked") and new_status in ("member",):
            msg = f"✅ {user.mention_html()} just joined <b>{cmu.chat.title}</b>"
            await context.bot.send_message(chat_id=FILES_ID, text=msg, parse_mode="HTML")
    except Exception as e:
        print(f"[notify join failed] {e}", flush=True)

# ====== TEMP LOGGER ======
async def _log_video_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.video:
        print("[SAVE THIS] VIDEO_FILE_ID =", update.message.video.file_id, flush=True)

# ====== ERROR HANDLER ======
async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("=== EXCEPTION ===", flush=True)
    print("Update:", update, flush=True)
    print("Error:", repr(context.error), flush=True)
    traceback.print_exception(type(context.error), context.error, context.error.__traceback__)

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

    # Join notifications
    app.add_handler(ChatMemberHandler(member_update, chat_member_types=ChatMemberHandler.CHAT_MEMBER))

    # Temp file_id logger
    app.add_handler(MessageHandler(filters.VIDEO & private_only, _log_video_id))

    app.add_error_handler(on_error)

    print("Starting polling…", flush=True)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}", file=sys.stderr)
        raise
