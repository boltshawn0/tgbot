# start_only_bot.py
# Telegram bot with:
# - /start (intro menu + private promo)
# - /private (private promo)
# - /public  (photo + Join button)
# - /other   (teaser2.mp4 + Join button)
# - /models  (loads from models.txt, deduped + alphabetized)
# - "💳 Pay with Crypto" button -> shows your wallet addresses & DM instruction

import os, sys, textwrap
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import MessageEntityType

# ====== ENV / LINKS ======
BOT_TOKEN = os.environ["BOT_TOKEN"]

INVITE_PRIVATE = "https://t.me/+pCkQCqhHoOFlZmMx"   # Private (vault)
INVITE_PUBLIC  = "https://t.me/+hmJ_yiDtJhdjM2Qx"   # Public channel
INVITE_OTHER   = "https://t.me/+UHH0jKOrMm5hOTcx"   # Other channel

# ====== MEDIA (local fallbacks) + optional file_id envs ======
PRIVATE_VIDEO_LOCAL = "teaser.mp4"
PRIVATE_VIDEO_FILE_ID_ENV = "VIDEO_FILE_ID"

OTHER_VIDEO_LOCAL = "teaser2.mp4"
OTHER_VIDEO_FILE_ID_ENV = "VIDEO2_FILE_ID"

PUBLIC_PHOTO_LOCAL = "photo1.jpg"
PUBLIC_PHOTO_FILE_ID_ENV = "PHOTO1_FILE_ID"

# ====== CAPTIONS ======
CAPTION_PRIVATE = (
    "🔒 400+ Models | 125,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW — DON'T MISS OUT CURRENTLY 25% OFF! 🚀\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $10 USD\n"
    "⭐ PAY WITH STARS HERE:\n"
    f"{INVITE_PRIVATE}"
)

CAPTION_OTHER = (
    "✨ Explore our Candids and Spycams channel ✨\n\n"
    "Exclusive extras and more content 🔥\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $10 USD\n"
    "DON'T MISS OUT CURRENTLY 25% OFF!"
)

CAPTION_PUBLIC = (
    "🌐 Public Channel\n"
    "Free Previews, Updates & Announcements. Tap JOIN below. 👇"
)

INTRO_MENU = textwrap.dedent("""\
               ✨ Welcome to TengokuHub Bot! ✨
Choose a command below to explore ⬇️

🔒 /private — Access the Private Vault (25% OFF SALE!)
🌐 /public  — Visit our Public Channel
📂 /other   — Check out our Candid and Spycam Channel (25% OFF SALE!)
🗂 /models  — Browse the Private Vault Models
""")

# ====== Custom emoji IDs (for animated emojis in CAPTION_PRIVATE) ======
LOCK_ID   = "5296369303661067030"   # 🔒
FIRE_ID   = "5289722755871162900"   # 🔥
STAR_ID   = "5267500801240092311"   # ⭐
ROCKET_ID = "5188481279963715781"   # 🚀
CAL_ID    = "5472026645659401564"   # 🗓
EMOJI_ID_MAP = {"🔒": LOCK_ID, "🔥": FIRE_ID, "⭐": STAR_ID, "🚀": ROCKET_ID, "🗓": CAL_ID}

def build_custom_emoji_entities_utf16(text: str):
    ents = []
    offset_utf16 = 0
    for ch in text:
        ch_units = len(ch.encode("utf-16-le")) // 2
        if ch in EMOJI_ID_MAP:
            ents.append(
                MessageEntity(
                    type=MessageEntityType.CUSTOM_EMOJI,
                    offset=offset_utf16,
                    length=ch_units,
                    custom_emoji_id=EMOJI_ID_MAP[ch],
                )
            )
        offset_utf16 += ch_units
    return ents

def kb_join(url: str, label: str = "⭐ Join"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, url=url)]])

def kb_private():
    # Stars + Crypto-info buttons
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Join via Stars", url=INVITE_PRIVATE)],
        [InlineKeyboardButton("💳 Pay with Crypto ($10)", callback_data="crypto_info")]
    ])

def kb_other():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Join via Stars", url=INVITE_OTHER)],
        [InlineKeyboardButton("💳 Pay with Crypto ($10)", callback_data="crypto_info")]
    ])

def kb_public():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Join Public", url=INVITE_PUBLIC)]])

# ====== HELPERS ======
async def send_media(update: Update, caption, file_env, local_path, kind="video", markup=None):
    caption_entities = build_custom_emoji_entities_utf16(caption)
    file_id = os.environ.get(file_env, "").strip()
    try:
        if file_id:
            if kind == "video":
                return await update.message.reply_video(
                    video=file_id, caption=caption,
                    caption_entities=caption_entities,
                    reply_markup=markup,
                    supports_streaming=True,
                )
            elif kind == "photo":
                return await update.message.reply_photo(
                    photo=file_id, caption=caption,
                    reply_markup=markup,
                )
    except Exception as e:
        print(f"[{kind} file_id failed] {e}", flush=True)

    try:
        with open(local_path, "rb") as f:
            if kind == "video":
                msg = await update.message.reply_video(
                    video=f, caption=caption,
                    caption_entities=caption_entities,
                    reply_markup=markup,
                    supports_streaming=True,
                )
            else:
                msg = await update.message.reply_photo(
                    photo=f, caption=caption,
                    reply_markup=markup,
                )
        if msg and getattr(msg, kind, None) and getattr(msg, kind).file_id:
            fid = getattr(msg, kind).file_id
            print(f"[SAVE THIS] Set {file_env}={fid}", flush=True)
    except Exception as e:
        print(f"[{kind} upload failed] {e}", flush=True)

# ====== COMMANDS ======
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO_MENU)

async def private_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_media(update, CAPTION_PRIVATE, PRIVATE_VIDEO_FILE_ID_ENV, PRIVATE_VIDEO_LOCAL, "video", kb_private())

async def other_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_media(update, CAPTION_OTHER, OTHER_VIDEO_FILE_ID_ENV, OTHER_VIDEO_LOCAL, "video", kb_other())

async def public_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_media(update, CAPTION_PUBLIC, PUBLIC_PHOTO_FILE_ID_ENV, PUBLIC_PHOTO_LOCAL, "photo", kb_public())

async def models_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("models.txt", "r", encoding="utf-8") as f:
            models = [line.strip() for line in f if line.strip()]
        models = sorted(set(models), key=lambda s: s.lower())
        half = len(models) // 2
        part1, part2 = models[:half], models[half:]
        await update.message.reply_text("📂 Private Vault Models (Part 1):\n" + ", ".join(part1))
        await update.message.reply_text("📂 Private Vault Models (Part 2):\n" + ", ".join(part2))
    except Exception as e:
        await update.message.reply_text(f"[models failed] {e}")

# ====== CALLBACKS ======
async def crypto_info_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    # Your 3 addresses + DM instruction
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
