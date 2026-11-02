# 🤖 Telegram UserBot (Shaxsiy Avtojavobchi va Bildirishnoma Boti)

Ushbu loyiha sizning shaxsiy Telegram akkauntingiz orqali ishlaydi:
1. Sizga shaxsiy xabar (PM) yozgan yangi foydalanuvchilarga avtomatik tarzda oldindan belgilangan javob xabarini yuboradi (faqat 1 marta).
2. Yangi yozgan odam va uning xabari haqida sizning **"Saqlangan xabarlar" (Saved Messages)**ingizga darhol xabarnoma jo'natadi.
3. Botni to'g'ridan-to'g'ri Telegram chatidan maxsus buyruqlar orqali boshqarish mumkin (`.status`, `.settext`, `.toggle`, `.help`, `.send`).
4. **Google Cloud Platform (GCP)** yoki boshqa Linux VPS serverlarda 24/7 ishlashga to'liq moslashtirilgan.

---

## 📁 Loyiha Tuzilishi

- `main.py` — Botning asosiy kodi (xabarlarni qabul qilish, avtojavob va buyruqlar)
- `login.py` — Telegram hisobingizga kirish va xavfsiz `STRING_SESSION` olish skripti
- `database.py` — SQLite ma'lumotlar bazasi (kimga javob berilganini eslab qoladi)
- `config.py` — Sozlamalar va `.env` faylini yuklash
- `.env` — Sizning Telegram API kalitlaringiz va sozlamalaringiz
- `Dockerfile` & `docker-compose.yml` — Serverda konteynerda ishlatish uchun
- `userbot.service` — Linux (Google Cloud VM) da fon xizmati (systemd) sifatida ishlatish uchun

---

## 🛠 1-Qadam: Telegram API kalitlarini olish

1. Kompyuter yoki telefonda brauzer orqali [my.telegram.org](https://my.telegram.org) saytiga kiring.
2. Telegram akkauntingiz telefon raqamini kiriting va Telegramga kelgan tasdiqlash kodini yozing.
3. **"API development tools"** bo'limiga kiring.
4. Har qanday nom yozib yangi ilova yarating (masalan: `MyUserBot`).
5. Sayt sizga quyidagilarni beradi:
   - **`api_id`** (raqamlardan iborat, masalan: `28374921`)
   - **`api_hash`** (harf va raqamlar, masalan: `a3b8...9f1`)
6. Ushbu ma'lumotlarni nusxalab oling.

---

## 🔑 2-Qadam: Lokal kompyuterda bir marta kirish (Sessiya olish)

Google Cloud yoki serverda SMS kodini kiritish qiyin bo'lmasligi uchun, avval o'z kompyuteringizda 1 marta kirib sessiya kodini olasiz:

1. Terminalda qaramliklarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
2. `.env` faylini oching va `API_ID` hamda `API_HASH` ni kiriting.
3. Kirish skriptini ishga tushiring:
   ```bash
   python login.py
   ```
4. Telefon raqamingizni kiriting (masalan: `+998901234567`).
5. Telegramga kelgan 5 xonali kodni kiriting (agar 2-bosqichli parolingiz bo'lsa, parolingizni ham kiriting).
6. Skript sizga uzun **STRING_SESSION** kodini chiqarib beradi va uni avtomatik `.env` fayliga yozib qo'yadi!

Endi siz botni xohlasangiz kompyuteringizda:
```bash
python main.py
```
orqali sinab ko'rishingiz mumkin!

---

## ☁️ 3-Qadam: Google Cloud (GCP) Serveriga O'rnatish (24/7 ishlashi uchun)

Google Cloud bepul hisob (yoki bepul `e2-micro` VM) beradi. Quyidagi amallarni bajaring:

### A) Google Cloud da Virtual Mashina (VM) yaratish
1. [Google Cloud Console](https://console.cloud.google.com/) ga kiring.
2. Chap menyudan **Compute Engine -> VM instances** bo'limiga o'ting.
3. **"Create Instance"** tugmasini bosing:
   - **Name:** `telegram-userbot`
   - **Region:** istalgan arzon hudud (masalan: `us-central1` yoki `europe-west1`)
   - **Machine configuration:** `E2` -> `e2-micro` (2 vCPU, 1 GB RAM yetarli)
   - **Boot disk:** `Ubuntu 22.04 LTS` yoki `Debian 12`
   - **Create** tugmasini bosing.

### B) Serverga ulanish va botni o'rnatish
VM tayyor bo'lgach, uning yonidagi **"SSH"** tugmasini bosing. Brauzerda qora terminal oynasi ochiladi.

Server terminaliga quyidagi buyruqlarni ketma-ket nusxalab tashlang:

```bash
# 1. Tizimni yangilash va kerakli paketlarni o'rnatish
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# 2. Loyiha papkasini yaratish va unga o'tish
mkdir telegram_userbot && cd telegram_userbot

# 3. Virtual muhit (venv) yaratish
python3 -m venv venv
source venv/bin/activate
```

Endi kompyuteringizdagi fayllarni serverga qo'ying (yoki `git clone` qiling). Yoki eng oson yo'li — fayllarni to'g'ridan-to'g'ri yaratish:

```bash
# requirements.txt
cat << 'EOF' > requirements.txt
telethon>=1.36.0
python-dotenv>=1.0.0
EOF

pip install -r requirements.txt
```

Loyihadagi `config.py`, `database.py`, `main.py` fayllarini serverga joylang.
So'ng `.env` faylini yarating:
```bash
nano .env
```
Va kompyuteringizda olgan tayyor `.env` mazmunini (ayniqsa `API_ID`, `API_HASH` va `STRING_SESSION`) joylashtiring (`Ctrl+O`, `Enter`, `Ctrl+X` orqali saqlang).

### C) Botni 24/7 uzluksiz fonda ishlatish (systemd)

Bot server qayta yoqilsa ham avtomatik ishlab turishi uchun tizim xizmatiga qo'shamiz:

```bash
sudo nano /etc/systemd/system/userbot.service
```
Quyidagilarni yozing (foydalanuvchi nomingizga moslang, masalan `root`):
```ini
[Unit]
Description=Telegram Userbot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram_userbot
ExecStart=/root/telegram_userbot/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Xizmatni ishga tushirish:
```bash
sudo systemctl daemon-reload
sudo systemctl enable userbot
sudo systemctl start userbot
```

Botning holatini tekshirish:
```bash
sudo systemctl status userbot
```
Loglarni jonli ko'rish:
```bash
journalctl -u userbot -f
```

Endi brauzer terminalini yopsangiz ham botingiz Google Cloud serverida 24/7 tinimsiz ishlayveradi!

---

## 🎮 Telegramdan Boshqarish Buyruqlari

O'zingizning hisobingizdan (istalgan chatda yoki "Saqlangan xabarlar" da) quyidagi buyruqlarni yuborishingiz mumkin:

| Buyruq | Vazifasi |
|---|---|
| `.status` | Bot holati, statistikasi va hozirgi avtojavob matnini ko'rsatish |
| `.toggle` | Avtojavobni yoqish yoki vaqtincha o'chirib qo'yish |
| `.gettext` | Hozirgi o'rnatilgan avtojavob matnini ko'rish |
| `.settext <yangi matn>` | Avtojavob matnini shu zahoti o'zgartirish |
| `.notify` | "Saqlangan xabarlar"ga bildirishnoma yuborishni yoqish / o'chirish |
| `.reset` | Baza xotirasini tozalash (foydalanuvchilar yana avtojavob olishi uchun) |
| `.send @username matn` | Boshqa foydalanuvchiga xabar jo'natish |
| `.ping` | Bot serverining tezligini (kechikishini) tekshirish |
| `.help` | Barcha buyruqlar bo'yicha yordam |
