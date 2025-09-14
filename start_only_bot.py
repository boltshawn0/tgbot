from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity

INVITE_LINK = "https://t.me/+pCkQCqhHoOFlZmMx"
VIDEO_SRC   = "teaser.mp4"   # local file in your repo

# 🔢 Custom emoji IDs you sent
LOCK_ID   = "5296369303661067030"
FIRE_ID   = "5289722755871162900"     # black fire
STAR_ID   = "5267500801240092311"
ROCKET_ID = "5188481279963715781"
CAL_ID    = "5472026645659401564"     # spiral calendar

# ✍️ Put normal emoji where you want the animated ones to appear.
CAPTION = (
    "🔒 350+ Models | 100,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    "JOIN UP BELOW DONT MISS OUT! 🚀\n\n"
    "🗓 MONTHLY SUBSCRIPTION — 500 STARS / $5 USD\n"
    "⭐ PAY WITH STARS HERE:\n\n"
    f"{INVITE_LINK}"
)

# Map each visible emoji in the text to your custom_emoji_id
EMOJI_ID_MAP = {
    "🔒": LOCK_ID,
    "🔥": FIRE_ID,
    "⭐": STAR_ID,
    "🚀": ROCKET_ID,
    "🗓": CAL_ID,
}

def build_custom_emoji_entities(text: str):
    """Create caption_entities so those emoji render as animated custom emoji."""
    entities = []
    i = 0
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

def join_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Join / Pay with Stars", url=INVITE_LINK)]])

async def start_cmd(update, context):
    caption_entities = build_custom_emoji_entities(CAPTION)
    try:
        with open(VIDEO_SRC, "rb") as f:
            await update.message.reply_video(
                video=f,
                caption=CAPTION,
                caption_entities=caption_entities,  # ← IMPORTANT
                reply_markup=join_keyboard(),
                supports_streaming=True,
            )
    except Exception as e:
        # Fallback if video send fails
        await update.message.reply_text(
            CAPTION,
            reply_markup=join_keyboard(),
            entities=caption_entities,  # still show animated emoji
        )
