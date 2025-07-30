#!/bin/bash

# Script Installer untuk Termux Bot
# Developer: SerpentSecHunter
# Version: 3.0 BETA

clear
echo "🚀 TERMUX BOT INSTALLER v3.0 BETA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Developer: SerpentSecHunter"
echo "GitHub: https://github.com/SerpentSecHunter"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cek apakah berjalan di Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo "❌ Script ini hanya bisa dijalankan di Termux!"
    exit 1
fi

echo "📦 Memperbarui paket Termux..."
pkg update -y && pkg upgrade -y

echo ""
echo "📦 Menginstall paket yang diperlukan..."

# Install paket dasar
packages=(
    "python"
    "python-pip"
    "git"  
    "curl"
    "wget"
    "termux-api"
    "openssh"
    "nano"
)

for package in "${packages[@]}"; do
    echo "📦 Installing $package..."
    pkg install -y "$package"
done

echo ""
echo "🐍 Menginstall Python libraries..."

# Install Python libraries
python_libs=(
    "pyTelegramBotAPI"
    "python-dotenv"
    "psutil" 
    "requests"
    "cryptography"
    "pathlib2"
    "google-generativeai"
)

for lib in "${python_libs[@]}"; do
    echo "📦 Installing $lib..."
    pip install "$lib"
done

echo ""
echo "📱 Setup Termux API permissions..."
echo "⚠️  PENTING: Install Termux:API dari F-Droid dan berikan semua permission!"
echo "Link: https://f-droid.org/packages/com.termux.api/"
echo ""
read -p "Apakah Anda sudah install Termux:API? (y/n): " api_installed

if [ "$api_installed" != "y" ]; then
    echo "❌ Silakan install Termux:API terlebih dahulu!"
    echo "1. Download dari F-Droid: https://f-droid.org/packages/com.termux.api/"
    echo "2. Install dan berikan semua permission"
    echo "3. Jalankan script ini lagi"
    exit 1
fi

echo ""
echo "📁 Membuat direktori bot..."
BOT_DIR="$HOME/termux_bot"
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

echo ""
echo "📝 Setup konfigurasi bot..."

# Cek apakah file .env sudah ada
if [ -f ".env" ]; then
    echo "⚠️  File .env sudah ada. Backup file lama..."
    mv .env .env.backup.$(date +%s)
fi

# Buat file .env
cat > .env << 'EOF'
# Konfigurasi Termux Bot
# Jangan share file ini ke orang lain!

# Bot Telegram Token
BOT_TOKEN=8384419176:AAGVyKuDiv-fBhfRV8freoWdbkspVwrowS0

# Chat ID Telegram Anda  
CHAT_ID=7089440829

# Gemini API Key untuk fitur AI
GEMINI_API_KEY=AIzaSyByVDkfC339f4OL0EqBCyu7hBKUFatoDU8
EOF

echo "✅ File .env berhasil dibuat!"

echo ""
echo "🔐 Setup permissions..."
chmod +x termux_bot.py 2>/dev/null || true
chmod 600 .env
termux-setup-storage

echo ""
echo "🔧 Membuat script startup..."

# Buat script untuk auto-start
cat > start_bot.sh << 'EOF'
#!/bin/bash
cd ~/termux_bot
echo "🚀 Starting Termux Bot..."
python termux_bot.py
EOF

chmod +x start_bot.sh

# Tambahkan ke .bashrc untuk auto-start (optional)
if ! grep -q "termux_bot" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Auto start Termux Bot (uncomment to enable)" >> ~/.bashrc  
    echo "# cd ~/termux_bot && python termux_bot.py &" >> ~/.bashrc
fi

echo ""
echo "🎯 Membuat shortcut..."

# Buat alias untuk menjalankan bot
if ! grep -q "alias tbot" ~/.bashrc; then
    echo "alias tbot='cd ~/termux_bot && python termux_bot.py'" >> ~/.bashrc
    echo "alias tbot-start='cd ~/termux_bot && ./start_bot.sh'" >> ~/.bashrc
    echo "alias tbot-stop='pkill -f termux_bot.py'" >> ~/.bashrc
fi

echo ""
echo "📊 Membuat script monitor..."

cat > monitor.sh << 'EOF'
#!/bin/bash

echo "📊 TERMUX BOT MONITOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cek status bot
if pgrep -f "termux_bot.py" > /dev/null; then
    echo "🟢 Status: Bot Running"
    echo "🆔 PID: $(pgrep -f termux_bot.py)"
else
    echo "🔴 Status: Bot Stopped"
fi

echo ""
echo "💾 Memory Usage:"
ps aux | grep termux_bot.py | grep -v grep | awk '{print "📊 CPU: "$3"% | RAM: "$4"%"}'

echo ""
echo "📁 Files:"
ls -la ~/termux_bot/

echo ""
echo "🔧 Commands:"
echo "  tbot        - Start bot"
echo "  tbot-stop   - Stop bot"  
echo "  tbot-start  - Start with log"
EOF

chmod +x monitor.sh

echo ""
echo "✅ INSTALASI SELESAI!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📂 Bot terinstall di: $BOT_DIR"
echo ""
echo "🚀 CARA MENJALANKAN BOT:"
echo "1. cd ~/termux_bot"
echo "2. python termux_bot.py"
echo ""
echo "🎛️  ATAU gunakan shortcut:"
echo "   tbot        - Jalankan bot"
echo "   tbot-stop   - Stop bot"
echo "   ./monitor.sh - Monitor status"
echo ""
echo "⚙️  KONFIGURASI:"
echo "- Edit file .env untuk mengubah token/API key"
echo "- Pastikan Termux:API sudah terinstall dan diberi permission"
echo ""
echo "📱 FITUR BOT:"
echo "✅ Install/Lihat Library"
echo "✅ Kontrol Termux penuh" 
echo "✅ Gallery Eyes (scan media)"
echo "✅ Kunci/buka file penting"
echo "✅ Cek package storage"
echo "✅ Remove & copy file"
echo "✅ WiFi control & info"
echo "✅ Getar device & senter"
echo "✅ Auto-plant bot"
echo "✅ System information"
echo ""
echo "🔐 KEAMANAN:"
echo "- Token dan API key tersimpan aman di .env"
echo "- File .env tidak bisa dibaca user lain"
echo "- Bot hanya merespon Chat ID yang terdaftar"
echo ""
echo "⚠️  PENTING:"
echo "1. Jangan share file .env ke orang lain!"
echo "2. Pastikan Termux:API terinstall dari F-Droid"
echo "3. Script harus dinamai 'termux_bot.py'"
echo ""
echo "🎉 Selamat! Bot siap digunakan!"
echo "Jalankan: cd ~/termux_bot && python termux_bot.py"
