# -*- coding: utf-8 -*-
# Telegram bot with Coinbase Commerce integration + access management
# - /start, /private, /public, /other, /models
# - "Pay $10 in Crypto" creates a hosted Coinbase charge per user/product
# - Webhook (aiohttp) verifies signature, grants channel access, schedules expiry
# - Notifies @jordancarter005 on every confirmed purchase (username + dates)
#
# Run on Railway with a Start Command:  python -u start_only_bot.py

import os, sys, json, hmac, hashlib, time, asyncio, sqlite3, textwrap, logging
from datetime import datetime, timedelta, timezone

from aiohttp import web, ClientSession

from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity, Update, ChatMemberRestricted,
)
from telegram.constants import MessageEntityType, ChatMemberStatus, ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ----------------- ENV -----------------
BOT_TOKEN = os.environ["BOT_TOKEN"]
PRIVATE_CHAT_ID = int(os.environ["PRIVATE_CHAT_ID"])
OTHER_CHAT_ID   = int(os.environ["OTHER_CHAT_ID"])
INVITE_PRIVATE  = os.environ.get("INVITE_PRIVATE", "")
INVITE_PUBLIC   = os.environ.get("INVITE_PUBLIC", "")
INVITE_OTHER    = os.environ.get("INVITE_OTHER", "")

CRYPTO_PRICE_PRIVATE_USD = float(os.environ.get("CRYPTO_PRICE_PRIVATE_USD", "10"))
CRYPTO_PRICE_OTHER_USD   = float(os.environ.get("CRYPTO_PRICE_OTHER_USD", "10"))

ACCESS_DAYS = int(os.environ.get("ACCESS_DAYS", "30"))
REMINDER_HOURS_BEFORE = int(os.environ.get("REMINDER_HOURS_BEFORE", "24"))

COINBASE_API_KEY = os.environ["COINBASE_API_KEY"]
COINBASE_WEBHOOK_SECRET = os.environ["COINBASE_WEBHOOK_SECRET"]

VIDEO_FILE_ID  = os.environ.get("VIDEO_FILE_ID", "").strip()
VIDEO2_FILE_ID = os.environ.get("VIDEO2_FILE_ID", "").strip()
PHOTO1_FILE_ID = os.environ.get("PHOTO1_FILE_ID", "").strip()

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@jordancarter005").strip()

PORT = int(os.environ.get("PORT", "8080"))  # Railway

# ----------------- TEXT / UI -----------------
INTRO_MENU = textwrap.dedent("""\
✨ Welcome to TengokuHub Bot! ✨

Use the commands below:
🔒 /private — Access the Private Vault
🌐 /public  — Visit our Public Channel
📂 /other   — Candid & Spycam Channel
🗂 /models  — Browse models list
""")

CAPTION_PRIVATE = (
    "🔒 400+ Models | 125,000+ Media 📁\n"
    "ALL FULLY POSTED IN PRIVATE TELEGRAM VAULT 🔥🔥🔥🔥🔥\n\n"
    f"⭐ Pay with Stars: {INVITE_PRIVATE}\n"
    "…or use crypto below ⬇️"
)

CAPTION_PUBLIC = (
    "🌐 Public Channel\n"
    "Free Previews, Updates & Announcements.\n"
    "Tap JOIN below."
)

CAPTION_OTHER = (
    "✨ Candids & Spycams\n\n"
    f"⭐ Pay with Stars: {INVITE_OTHER}\n"
    "…or use crypto below ⬇️"
)

# Optional animated emoji mapping (safe if empty)
LOCK_ID   = "5296369303661067030"
FIRE_ID   = "5289722755871162900"
STAR_ID   = "5267500801240092311"
ROCKET_ID = "5188481279963715781"
CAL_ID    = "5472026645659401564"
EMOJI_ID_MAP = {"🔒": LOCK_ID, "🔥": FIRE_ID, "⭐": STAR_ID, "🚀": ROCKET_ID, "🗓": CAL_ID}

def build_custom_emoji_entities_utf16(text: str):
    ents = []
    off = 0
    for ch in text:
        units = len(ch.encode("utf-16-le")) // 2
        if ch in EMOJI_ID_MAP:
            ents.append(MessageEntity(
                type=MessageEntityType.CUSTOM_EMOJI,
                offset=off, length=units, custom_emoji_id=EMOJI_ID_MAP[ch]
            ))
        off += units
    return ents

def kb_join(url: str, label: str="⭐ Join"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, url=url)]])

def kb_with_crypto(product: str, usd_price: float, join_url: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ Pay with Stars", url=join_url)],
        [InlineKeyboardButton(f"💳 Pay ${usd_price:.0f} in Crypto", callback_data=f"crypto:{product}")]
    ])

# ----------------- DB -----------------
DB_PATH = "bot.db"
def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS charges(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        charge_id TEXT UNIQUE,
        user_id INTEGER,
        username TEXT,
        product TEXT,
        status TEXT,
        hosted_url TEXT,
        created_at INTEGER
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS access(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product TEXT,
        chat_id INTEGER,
        granted_at INTEGER,
        expires_at INTEGER
    )""")
    return conn

# ----------------- Coinbase helpers -----------------
COINBASE_BASE = "https://api.commerce.coinbase.com"

async def coinbase_create_charge(session: ClientSession, user_id: int, username: str, product: str, usd_price: float):
    headers = {
        "X-CC-Api-Key": COINBASE_API_KEY,
        "X-CC-Version": "2018-03-22",
        "Content-Type": "application/json",
    }
    name = "TengokuHub - Private Vault" if product=="private" else "TengokuHub - Candids"
    desc = f"Monthly access for @{username or user_id} ({product})"
    payload = {
        "name": name,
        "description": desc,
        "pricing_type": "fixed_price",
        "local_price": {"amount": f"{usd_price:.2f}", "currency": "USD"},
        # No redirect required; user returns to bot manually after payment.
        # Webhook will confirm.
    }
    async with session.post(f"{COINBASE_BASE}/charges", headers=headers, json=payload) as r:
        data = await r.json()
        if r.status >= 300:
            raise RuntimeError(f"coinbase create failed {r.status}: {data}")
        charge = data["data"]
        return charge["id"], charge["hosted_url"]

def verify_cb_signature(secret: str, body: bytes, sig_header: str) -> bool:
    # Coinbase Commerce: HMAC SHA256 of body using shared secret
    try:
        computed = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        # header looks like: t=..., s=computed
        parts = {kv.split("=")[0]: kv.split("=")[1] for kv in sig_header.split(",")}
        s = parts.get("s") or parts.get("signature")
        return hmac.compare_digest(computed, s)
    except Exception:
        return False

# ----------------- Access helpers -----------------
async def resolve_admin_chat_id(app: Application) -> int:
    try:
        chat = await app.bot.get_chat(ADMIN_USERNAME)
        return chat.id
    except Exception:
        # fallback: try to parse @ off
        return 0

async def add_user_to_channel(app: Application, chat_id: int, user_id: int):
    try:
        # Unrestrict if previously restricted; else invite via addChatMember fails for channels.
        # For channels, bot must be admin with "Add Subscribers".
        await app.bot.invite_chat_member(chat_id, user_id)
    except Exception:
        # Some setups require export invite link; as fallback send nothing here.
        pass

async def remove_user_from_channel(app: Application, chat_id: int, user_id: int):
    try:
        await app.bot.ban_chat_member(chat_id, user_id)     # removes
        await app.bot.unban_chat_member(chat_id, user_id)   # allow rejoin later
    except Exception:
        pass

async def notify_admin(app: Application, text: str):
    admin_chat = await resolve_admin_chat_id(app)
    if admin_chat:
        try:
            await app.bot.send_message(admin_chat, text, disable_web_page_preview=True)
        except Exception:
            pass

# ----------------- Bot Handlers -----------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INTRO_MENU)

async def private_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = kb_with_crypto("private", CRYPTO_PRICE_PRIVATE_USD, INVITE_PRIVATE)
    entities = build_custom_emoji_entities_utf16(CAPTION_PRIVATE)
    if VIDEO_FILE_ID:
        await update.message.reply_video(VIDEO_FILE_ID, caption=CAPTION_PRIVATE,
                                         caption_entities=entities, reply_markup=kb, supports_streaming=True)
    else:
        await update.message.reply_text(CAPTION_PRIVATE, reply_markup=kb)

async def other_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = kb_with_crypto("other", CRYPTO_PRICE_OTHER_USD, INVITE_OTHER)
    if VIDEO2_FILE_ID:
        await update.message.reply_video(VIDEO2_FILE_ID, caption=CAPTION_OTHER,
                                         reply_markup=kb, supports_streaming=True)
    else:
        await update.message.reply_text(CAPTION_OTHER, reply_markup=kb)

async def public_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if PHOTO1_FILE_ID:
        await update.message.reply_photo(PHOTO1_FILE_ID, caption=CAPTION_PUBLIC,
                                         reply_markup=kb_join(INVITE_PUBLIC, "Join Public"))
    else:
        await update.message.reply_text(CAPTION_PUBLIC, reply_markup=kb_join(INVITE_PUBLIC, "Join Public"))

async def models_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("models.txt", "r", encoding="utf-8") as f:
            models = [ln.strip() for ln in f if ln.strip()]
        models = sorted(set(models), key=lambda s: s.lower())
        half = len(models)//2
        await update.message.reply_text("📂 Private Vault Models (Part 1):\n" + ", ".join(models[:half]))
        await update.message.reply_text("📂 Private Vault Models (Part 2):\n" + ", ".join(models[half:]))
    except Exception as e:
        await update.message.reply_text(f"[models failed] {e}")

# User tapped "Pay $10 in Crypto"
async def crypto_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product = query.data.split(":",1)[1]
    user = query.from_user
    price = CRYPTO_PRICE_PRIVATE_USD if product=="private" else CRYPTO_PRICE_OTHER_USD

    async with ClientSession() as s, db() as conn:
        try:
            charge_id, hosted = await coinbase_create_charge(s, user.id, user.username or "", product, price)
            conn.execute("INSERT OR IGNORE INTO charges(charge_id,user_id,username,product,status,hosted_url,created_at) VALUES(?,?,?,?,?,?,?)",
                         (charge_id, user.id, user.username or "", product, "pending", hosted, int(time.time())))
            conn.commit()
        except Exception as e:
            await query.message.reply_text(f"⚠️ Failed to create crypto payment: {e}")
            return

    await query.message.reply_text(
        "💳 Complete your crypto payment here:\n"
        f"{hosted}\n\n"
        "Once confirmed on-chain, access will be granted automatically. "
        "You’ll also get a reminder 1 day before expiry."
    )

# ----------------- Coinbase Webhook Server -----------------
async def coinbase_webhook(request: web.Request):
    app: Application = request.app["tg_app"]
    body = await request.read()
    sig = request.headers.get("X-CC-Webhook-Signature", "")
    if not verify_cb_signature(COINBASE_WEBHOOK_SECRET, body, sig):
        return web.Response(status=401, text="invalid signature")

    data = json.loads(body.decode())
    event = data.get("event", {})
    type_ = event.get("type", "")
    charge = event.get("data", {})
    charge_id = charge.get("id")

    # Update DB status
    with db() as conn:
        row = conn.execute("SELECT user_id, username, product FROM charges WHERE charge_id=?",
                           (charge_id,)).fetchone()
        if not row:
            return web.Response(status=200, text="ok")
        user_id, username, product = row

        if type_ in ("charge:confirmed", "charge:resolved"):
            conn.execute("UPDATE charges SET status=? WHERE charge_id=?", ("paid", charge_id))
            # Grant access record
            now = datetime.now(timezone.utc)
            expires = now + timedelta(days=ACCESS_DAYS)
            chat_id = PRIVATE_CHAT_ID if product=="private" else OTHER_CHAT_ID
            conn.execute("INSERT INTO access(user_id,product,chat_id,granted_at,expires_at) VALUES(?,?,?,?,?)",
                         (user_id, product, chat_id, int(now.timestamp()), int(expires.timestamp())))
            conn.commit()

    # Add to channel & notify admin (don’t await DB while calling Telegram)
    chat_id = PRIVATE_CHAT_ID if product=="private" else OTHER_CHAT_ID
    try:
        await add_user_to_channel(app, chat_id, user_id)
    except Exception:
        pass

    try:
        username_display = f"@{username}" if username else f"id:{user_id}"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=ACCESS_DAYS)
        text = (
            f"✅ **NEW PURCHASE**\n"
            f"User: {username_display}\n"
            f"Product: {product}\n"
            f"Purchased: {now.strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Expires:   {expires.strftime('%Y-%m-%d %H:%M UTC')}"
        )
        await notify_admin(app, text)
    except Exception:
        pass

    return web.Response(status=200, text="ok")

# ----------------- Scheduler: reminders & expirations -----------------
async def scheduler_task(app: Application):
    await asyncio.sleep(5)  # small delay after start
    while True:
        now_ts = int(time.time())
        try:
            with db() as conn:
                rows = conn.execute("SELECT id, user_id, product, chat_id, granted_at, expires_at FROM access").fetchall()
                for _id, user_id, product, chat_id, granted_at, expires_at in rows:
                    # reminder
                    if (expires_at - now_ts) <= REMINDER_HOURS_BEFORE*3600 and (expires_at - now_ts) > (REMINDER_HOURS_BEFORE-1)*3600:
                        try:
                            await app.bot.send_message(
                                user_id,
                                f"⏰ Your {product} access expires in ~{REMINDER_HOURS_BEFORE} hours.\n"
                                f"Renew anytime to extend your date."
                            )
                        except Exception:
                            pass
                    # expiry
                    if now_ts >= expires_at:
                        try:
                            await remove_user_from_channel(app, chat_id, user_id)
                        except Exception:
                            pass
                        conn.execute("DELETE FROM access WHERE id=?", (_id,))
                        conn.commit()
        except Exception as e:
            logging.exception(e)
        await asyncio.sleep(int(os.environ.get("SCHEDULER_INTERVAL_SECONDS","60")))

# ----------------- App boot -----------------
def make_web_app(tg_app: Application):
    app = web.Application()
    app["tg_app"] = tg_app
    app.router.add_post("/coinbase-webhook", coinbase_webhook)
    return app

def main():
    print("Booting bot…", flush=True)
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("private", private_cmd))
    application.add_handler(CommandHandler("public", public_cmd))
    application.add_handler(CommandHandler("other", other_cmd))
    application.add_handler(CommandHandler("models", models_cmd))
    application.add_handler(CallbackQueryHandler(crypto_cb, pattern=r"^crypto:"))

    # launch background scheduler
    application.job_queue.run_repeating(lambda ctx: None, interval=3600)  # keeps job_queue alive
    asyncio.get_event_loop().create_task(scheduler_task(application))

    # Start aiohttp server for Coinbase webhooks
    web_app = make_web_app(application)
    runner = web.AppRunner(web_app)

    async def run_all():
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Webhook server listening on :{PORT}/coinbase-webhook", flush=True)
        await application.initialize()
        await application.start()
        print("Starting polling…", flush=True)
        await application.bot.delete_webhook(drop_pending_updates=True)
        await application.updater.start_polling()
        # run forever
        await asyncio.Event().wait()

    asyncio.run(run_all())

if __name__ == "__main__":
    try:
        main()
    except KeyError as e:
        print(f"Missing env var: {e}", file=sys.stderr)
        raise
