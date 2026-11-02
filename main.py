import html
import logging
import os
import time
from datetime import datetime
import aiohttp
from aiohttp import web
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import UserStatusOnline, UserStatusOffline
import config
import database

# Loglarni sozlash
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("UserBot")

# Ma'lumotlar bazasini ishga tushirish
database.init_db()

# Sessiyani aniqlash
if config.STRING_SESSION:
    session = StringSession(config.STRING_SESSION)
    logger.info("StringSession orqali ulanmoqda...")
else:
    session = config.SESSION_NAME
    logger.info(f"Fayl sessiyasi orqali ulanmoqda: {config.SESSION_NAME}.session")

client = TelegramClient(session, config.API_ID, config.API_HASH)

# Foydalanuvchi ma'lumotlari
my_user_id = None
last_owner_online_time = float(database.get_setting("last_owner_online_time", "0"))


def update_owner_online_time(ts: float = None):
    """
    Eganing online bo'lgan oxirgi vaqtini yangilash
    """
    global last_owner_online_time
    if ts is None:
        ts = time.time()
    if ts > last_owner_online_time:
        last_owner_online_time = ts
        database.set_setting("last_owner_online_time", str(ts))


async def is_owner_online() -> bool:
    """
    Ega hozir online ekanligini va oxirgi online vaqtini aniqlash
    """
    try:
        me = await client.get_entity('me')
        status = getattr(me, 'status', None)

        if isinstance(status, UserStatusOnline):
            update_owner_online_time(time.time())
            return True
        elif isinstance(status, UserStatusOffline) and getattr(status, 'was_online', None):
            update_owner_online_time(status.was_online.timestamp())
            return False
    except Exception as e:
        logger.warning(f"Online holatni tekshirishda xatolik: {e}")

    # Agar 60 soniya ichida harakat bo'lgan bo'lsa online deb hisoblaymiz
    if time.time() - last_owner_online_time < 60:
        return True

    return False


async def send_bot_notification(chat_id: int, sender_name: str, username: str, sender_id: int, message_text: str) -> bool:
    """
    Maxsus Telegram Bot orqali egasiga kelgan xabar haqida bildirishnoma jo'natish
    """
    if not config.BOT_TOKEN:
        return False

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"

    safe_name = html.escape(sender_name)
    safe_msg = html.escape(message_text)
    user_ref = f"@{username}" if username else f"ID: {sender_id}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    text = (
        f"📩 <b>Yangi xabar keldi va avtojavob berildi!</b>\n\n"
        f"👤 <b>Kimdan:</b> {safe_name} ({user_ref})\n"
        f"💬 <b>Xabari:</b>\n<i>{safe_msg}</i>\n\n"
        f"🕒 <b>Vaqti:</b> <code>{now_str}</code>"
    )

    profile_url = f"https://t.me/{username}" if username else f"tg://user?id={sender_id}"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "💬 Profilni ochish", "url": profile_url}]
            ]
        }
    }

    try:
        async with aiohttp.ClientSession() as http_session:
            async with http_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("ok"):
                    return True
                elif resp.status == 400 and "chat not found" in str(data.get("description", "")):
                    logger.warning("Bot sizga yozishi uchun iltimos o'sha botga kirib /start bosing!")
                else:
                    logger.warning(f"Botga yuborishda xatolik: {data.get('description')}")
    except Exception as e:
        logger.error(f"Bot orqali xabar yuborishda xatolik: {e}")

    return False


@client.on(events.UserUpdate)
async def handle_user_update(event):
    """
    Eganing online holati o'zgarganda (hatto 1 sekundga kirib chiqsa ham) eslab qolish
    """
    global my_user_id
    if my_user_id and event.user_id == my_user_id:
        if event.online:
            logger.info("🟢 Siz Telegramda online bo'ldingiz.")
            update_owner_online_time(time.time())
        elif event.last_seen:
            ts = event.last_seen.timestamp()
            logger.info("🔴 Siz Telegramdan chiqdingiz (offline).")
            update_owner_online_time(ts)


@client.on(events.NewMessage(outgoing=True))
async def handle_outgoing_message(event):
    """
    Ega xabar yozsa (harakat qilsa) uni online deb belgilash va buyruqlarni bajarish
    """
    global my_user_id
    update_owner_online_time(time.time())

    text = event.raw_text or ""
    prefix = config.CMD_PREFIX

    if not text.startswith(prefix):
        return

    parts = text.split(" ", 1)
    cmd = parts[0][len(prefix):].lower()
    args = parts[1] if len(parts) > 1 else ""

    # .help yoki .yordam
    if cmd in ("help", "yordam"):
        help_msg = (
            f"🤖 **UserBot Boshqaruv Paneli:**\n\n"
            f"▫️ `{prefix}status` — Bot holati va oxirgi online vaqti\n"
            f"▫️ `{prefix}toggle` — Avtojavobni yoqish / o'chirish\n"
            f"▫️ `{prefix}gettext` — Hozirgi avtojavob matnini ko'rish\n"
            f"▫️ `{prefix}settext <matn>` — Yangi avtojavob matnini o'rnatish\n"
            f"▫️ `{prefix}notify` — Bildirishnomalarni yoqish/o'chirish\n"
            f"▫️ `{prefix}reset` — Javob berilganlar ro'yxatini tozalash\n"
            f"▫️ `{prefix}send <username/ID> <xabar>` — Biror kishiga xabar jo'natish\n"
            f"▫️ `{prefix}ping` — Botning tezligini tekshirish"
        )
        await event.edit(help_msg)

    # .status
    elif cmd == "status":
        is_active = database.get_setting("is_active", "1") == "1"
        notify_me = database.get_setting("notify_me", "1" if config.NOTIFY_ME else "0") == "1"
        count = database.get_replied_count()
        current_text = database.get_setting("auto_reply_text", config.DEFAULT_AUTO_REPLY)
        notify_channel = "🤖 Telegram Bot orqali" if config.BOT_TOKEN else "📥 Saved Messages orqali"
        online_now = await is_owner_online()

        last_online_str = datetime.fromtimestamp(last_owner_online_time).strftime("%Y-%m-%d %H:%M:%S") if last_owner_online_time > 0 else "Hali qayd etilmagan"

        status_msg = (
            f"📊 **UserBot Holati:**\n\n"
            f"• **Holat:** {'🟢 Faol (Yoqilgan)' if is_active else '🔴 O\'chirilgan'}\n"
            f"• **Sizning holatingiz:** {'🟢 Online' if online_now else '🔴 Offline'}\n"
            f"• **Oxirgi online vaqti:** `{last_online_str}`\n"
            f"• **Javob olgan foydalanuvchilar:** `{count} ta`\n"
            f"• **Avtojavob qoidasi:** Faqat offline bo'lganda (har bir offline sessiyasida 1 marta)\n"
            f"• **Bildirishnoma yuborish:** {'✅ ' + notify_channel if notify_me else '❌ O\'chirilgan'}\n\n"
            f"📝 **Hozirgi avtojavob matni:**\n_{current_text}_"
        )
        await event.edit(status_msg)

    # .toggle (on/off)
    elif cmd == "toggle":
        is_active = database.get_setting("is_active", "1") == "1"
        new_state = "0" if is_active else "1"
        database.set_setting("is_active", new_state)
        state_str = "🟢 **Yoqildi**" if new_state == "1" else "🔴 **O'chirildi**"
        await event.edit(f"Avtojavob holati: {state_str}")

    # .notify (toggle notification)
    elif cmd == "notify":
        notify_me = database.get_setting("notify_me", "1" if config.NOTIFY_ME else "0") == "1"
        new_state = "0" if notify_me else "1"
        database.set_setting("notify_me", new_state)
        state_str = "✅ **Yoqildi**" if new_state == "1" else "❌ **O'chirildi**"
        await event.edit(f"Bildirishnoma yuborish: {state_str}")

    # .settext
    elif cmd == "settext":
        if not args:
            await event.edit(f"❌ Xatolik! Foydalanish: `{prefix}settext Yangi matn`")
            return
        database.set_setting("auto_reply_text", args)
        await event.edit(f"✅ **Yangi avtojavob matni saqlandi:**\n\n_{args}_")

    # .gettext
    elif cmd == "gettext":
        current_text = database.get_setting("auto_reply_text", config.DEFAULT_AUTO_REPLY)
        await event.edit(f"📝 **Hozirgi avtojavob matni:**\n\n_{current_text}_")

    # .reset
    elif cmd == "reset":
        database.reset_replies()
        await event.edit("🔄 **Foydalanuvchilar ro'yxati tozalandi!** Endi yozganlar yana avtojavob olishadi.")

    # .send <target> <xabar>
    elif cmd == "send":
        parts_send = args.split(" ", 1)
        if len(parts_send) < 2:
            await event.edit(f"❌ Xatolik! Foydalanish: `{prefix}send @username yoki ID Xabar matni`")
            return
        target, message_to_send = parts_send[0].strip(), parts_send[1].strip()
        try:
            if target.isdigit():
                target = int(target)
            await client.send_message(target, message_to_send)
            await event.edit(f"✅ Xabar muvaffaqiyatli jo'natildi: `{target}`")
        except Exception as e:
            await event.edit(f"❌ Xabar jo'natishda xatolik: {e}")

    # .ping
    elif cmd == "ping":
        start = datetime.now()
        await event.edit("🏓 Pong...")
        end = datetime.now()
        ms = (end - start).microseconds // 1000
        await event.edit(f"🏓 **Pong!** `{ms} ms`")


@client.on(events.NewMessage(incoming=True))
async def handle_incoming_private(event):
    """
    Shaxsiy xabarlarga avtojavob berish
    """
    global my_user_id

    # Faqat shaxsiy (PM) chatlardan kelgan xabarlarga javob beramiz
    if not event.is_private:
        return

    sender = await event.get_sender()

    # Agar botdan kelgan bo'lsa yoki o'zimizdan bo'lsa javob bermaymiz
    if not sender or getattr(sender, "bot", False):
        return

    sender_id = event.sender_id

    if my_user_id is None:
        me = await client.get_me()
        my_user_id = me.id

    if sender_id == my_user_id:
        return

    # Botning umumiy faolligini tekshirish
    is_active = database.get_setting("is_active", "1") == "1"
    if not is_active:
        return

    # 1. Ega hozir online-mi?
    owner_online = await is_owner_online()
    if owner_online:
        logger.info(f"Siz hozir ONLINESIZ. {getattr(sender, 'first_name', '')} xabariga avtojavob berilmadi.")
        return

    # 2. Ushbu foydalanuvchiga oxirgi javob berilgan vaqt
    user_last_reply = database.get_user_last_reply_time(sender_id)

    # Agar oxirgi online bo'lganingizdan keyin ushbu foydalanuvchiga allaqachon javob berilgan bo'lsa:
    if user_last_reply > 0 and user_last_reply >= last_owner_online_time:
        logger.info(f"Ushbu offline sessiyada {getattr(sender, 'first_name', '')} ga allaqachon javob berilgan.")
        return

    # Avtojavob matnini olish
    reply_text = database.get_setting("auto_reply_text", config.DEFAULT_AUTO_REPLY)
    sender_name = getattr(sender, "first_name", "") or "Foydalanuvchi"
    username = getattr(sender, "username", "") or ""

    try:
        # Xabarga javob qaytarish
        await event.reply(reply_text)

        # Bazaga vaqt tamg'asi bilan yozish
        current_ts = time.time()
        database.record_reply_ts(sender_id, sender_name, username, current_ts)
        logger.info(f"✅ Avtojavob muvaffaqiyatli yuborildi: {sender_name} (@{username} | ID: {sender_id})")

        # Egasi (o'zingiz) ga bildirishnoma jo'natish
        notify_me = database.get_setting("notify_me", "1" if config.NOTIFY_ME else "0") == "1"
        if notify_me:
            user_msg = event.raw_text or "[Ovozli/Rasm/Media xabar]"

            # Telegram bot orqali jo'natamiz
            sent_via_bot = False
            if config.BOT_TOKEN and my_user_id:
                sent_via_bot = await send_bot_notification(
                    chat_id=my_user_id,
                    sender_name=sender_name,
                    username=username,
                    sender_id=sender_id,
                    message_text=user_msg
                )

            # Agar bot orqali yetib bormasa, "Saved Messages" ga yuboramiz
            if not sent_via_bot:
                user_link = f"@{username}" if username else f"ID: {sender_id}"
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                notify_text = (
                    f"📩 **Yangi xabar keldi va avtojavob berildi!**\n\n"
                    f"👤 **Kimdan:** {sender_name} ({user_link})\n"
                    f"💬 **Xabari:**\n_{user_msg}_\n\n"
                    f"🕒 **Vaqti:** `{now_str}`"
                )
                await client.send_message("me", notify_text)

    except Exception as e:
        logger.error(f"Xatolik yuz berdi (avtojavob): {e}")


async def health_check_handler(request):
    """
    Bulutli serverlar (HuggingFace / Render) uchun status sahifasi
    """
    return web.Response(
        text="<h1>🟢 Telegram UserBot 24/7 faol ishlab turibdi!</h1><p>Status: Online</p>",
        content_type="text/html"
    )


async def start_web_server():
    """
    Bulutli platformalar salomatligini (Health Check) ta'minlash uchun kichik veb server
    """
    port = int(os.getenv("PORT", 7860))
    app = web.Application()
    app.router.add_get("/", health_check_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    try:
        await site.start()
        logger.info(f"Veb server {port}-portda ishga tushirildi.")
    except Exception as e:
        logger.warning(f"Veb serverni {port}-portda ishga tushirib bo'lmadi (lokal ishlayapti): {e}")


async def main():
    global my_user_id
    logger.info("Bot ishga tushmoqda...")
    await client.connect()
    if not await client.is_user_authorized():
        logger.error("Akkaunt avtorizatsiyadan o'tmagan! Avval `python login.py` orqali kiring.")
        return

    me = await client.get_me()
    my_user_id = me.id
    logger.info(f"Bot muvaffaqiyatli ulandi! Ega: {me.first_name} (@{me.username or 'yoq'}, ID: {me.id})")

    # Boshlang'ich online vaqtini olish
    await is_owner_online()

    # Bulutli serverlar uchun veb serverni fonda yoqish
    await start_web_server()

    logger.info("Bot shaxsiy xabarlarni tinglamoqda... (Faqat offline bo'lganingizda javob beradi)")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
