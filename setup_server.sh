#!/bin/bash
set -e

echo "=========================================="
echo "  Telegram UserBot - Google Cloud O'rnatish"
echo "=========================================="

# Paketlarni yangilash
echo "[1/4] Tizim yangilanmoqda va kerakli paketlar o'rnatilmoqda..."
sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv git

# Virtual muhit yaratish
echo "[2/4] Python virtual muhiti sozlanmoqda..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Paketlarni o'rnatish
echo "[3/4] Kutubxonalar o'rnatilmoqda..."
pip install --upgrade pip
pip install -r requirements.txt

# Systemd xizmatini sozlash
echo "[4/4] 24/7 avtomatik ishlash xizmati sozlanmoqda..."
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

cat << EOF | sudo tee /etc/systemd/system/userbot.service
[Unit]
Description=Telegram UserBot Service
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python3 $CURRENT_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable userbot
sudo systemctl restart userbot

echo "=========================================="
echo "✅ UserBot muvaffaqiyatli ishga tushirildi!"
echo "Holatni tekshirish uchun: sudo systemctl status userbot"
echo "Loglarni jonli ko'rish uchun: journalctl -u userbot -f"
echo "=========================================="

