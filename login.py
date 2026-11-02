import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import config


async def main():
    print("=" * 60)
    print("   TELEGRAM USERBOT - KIRISH VA SESSIYA OLISH")
    print("=" * 60)

    api_id = config.API_ID
    api_hash = config.API_HASH

    if not api_id or not api_hash:
        print("\n[!] DIQQAT: .env faylida API_ID yoki API_HASH topilmadi!")
        api_id_input = input("API_ID kiriting: ").strip()
        api_hash_input = input("API_HASH kiriting: ").strip()
        if not api_id_input or not api_hash_input:
            print("Xatolik: API_ID va API_HASH kiritilishi shart.")
            sys.exit(1)
        api_id = int(api_id_input)
        api_hash = api_hash_input

    print("\nSiz uchun qaysi turdagi sessiya qulay?")
    print("1) StringSession (Google Cloud / Server uchun tavsiya etiladi)")
    print("2) Standart .session fayl (Kompyuterda qoldirish uchun)")
    choice = input("Tanlang (1 yoki 2, standart: 1): ").strip()

    use_string = choice != "2"
    if use_string:
        str_session_obj = StringSession()
        client = TelegramClient(str_session_obj, api_id, api_hash)
    else:
        str_session_obj = None
        client = TelegramClient(config.SESSION_NAME, api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        print("\n" + "-" * 60)
        print("Siz o'z shaxsiy akkauntingiz (Userbot) orqali kirmakdasiz.")
        print("Bot token KERAK EMAS! Telegram ochilgan telefon raqamingizni kiriting.")
        print("-" * 60)
        phone_number = input("Telefon raqamingiz (masalan: +998901234567): ").strip()

        print(f"\n[+] {phone_number} raqamiga tasdiqlash kodi yuborilmoqda...")
        await client.send_code_request(phone_number)

        code = input("\nTelegram ilovangizga kelgan 5 xonali kodni kiriting: ").strip()
        try:
            await client.sign_in(phone=phone_number, code=code)
        except SessionPasswordNeededError:
            print("\n[!] Akkauntingizda 2 bosqichli parol (2FA) o'rnatilgan.")
            password = input("Ikki bosqichli parolingizni kiriting: ").strip()
            await client.sign_in(password=password)

    me = await client.get_me()
    first_name = getattr(me, "first_name", "") or ""
    username = getattr(me, "username", "") or "username yo'q"
    user_id = getattr(me, "id", 0)

    print("\n" + "=" * 60)
    print(f"Muvaffaqiyatli kirdingiz! Akkaunt: {first_name} (@{username}, ID: {user_id})")
    print("=" * 60)

    if use_string and str_session_obj is not None:
        str_session = str_session_obj.save()
        print("\n>>> SIZNING STRING_SESSION KODINGIZ:")
        print("-" * 60)
        print(str_session)
        print("-" * 60)

        # .env fayliga avtomatik yozish
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        content = ""
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                content = f.read()

        lines = content.splitlines()
        found_str = False
        new_lines = []

        for line in lines:
            if line.startswith("STRING_SESSION="):
                new_lines.append(f"STRING_SESSION={str_session}")
                found_str = True
            else:
                new_lines.append(line)

        if not found_str:
            new_lines.append(f"STRING_SESSION={str_session}")

        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
        print("\n[✓] STRING_SESSION kodi avtomatik .env fayliga saqlandi!")
    else:
        print(f"\n[✓] Sessiya fayli saqlandi: {config.SESSION_NAME}.session")

    await client.disconnect()
    print("\n[✓] Tayyor! Endi `python main.py` orqali botni ishlatishingiz mumkin.")


if __name__ == "__main__":
    asyncio.run(main())
