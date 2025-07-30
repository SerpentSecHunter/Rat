#!/usr/bin/env python3
# termux_bot.py - Fixed Version

import os
import subprocess
import time
import shutil
import re
import json
import threading
from datetime import datetime
from pathlib import Path
import telebot
from telebot import types
import socket
import platform
import requests
import psutil

# ======================== KONFIGURASI ========================
# Masukkan token dan chat ID Anda di sini
BOT_TOKEN =8384419176:AAGVyKuDiv-fBhfRV8freoWdbkspVwrowS0  # Ganti dengan token bot Anda
CHAT_ID = "7089440829"      # Ganti dengan chat ID Anda

# Atau gunakan environment variables (lebih aman)
if os.getenv('BOT_TOKEN'):
    BOT_TOKEN = os.getenv('BOT_TOKEN')
if os.getenv('CHAT_ID'):
    CHAT_ID = os.getenv('CHAT_ID')

bot = telebot.TeleBot(BOT_TOKEN)

# Informasi bot
BOT_NAME = "🤖 Termux Advanced Controller"
DEVELOPER = "SerpentSecHunter"
GITHUB = "https://github.com/SerpentSecHunter"
VERSION = "4.0 ULTRA"
RELEASE_DATE = datetime.now().strftime("%A, %d %B %Y")

# ======================== FUNGSI UTILITAS ========================
def run_command(command, timeout=10):
    """Menjalankan perintah dengan timeout dan error handling yang lebih baik"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        if result.returncode == 0:
            return result.stdout.strip() if result.stdout.strip() else "✅ Perintah berhasil dijalankan"
        else:
            return f"❌ Error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "⏰ Timeout: Perintah memakan waktu terlalu lama"
    except Exception as e:
        return f"❌ Exception: {str(e)}"

def check_termux_api():
    """Cek apakah Termux API terinstall"""
    try:
        result = subprocess.run(['which', 'termux-wifi-enable'], capture_output=True)
        return result.returncode == 0
    except:
        return False

def install_termux_api():
    """Install Termux API jika belum ada"""
    try:
        commands = [
            'pkg update -y',
            'pkg install -y termux-api',
            'pkg install -y android-tools'
        ]
        
        results = []
        for cmd in commands:
            result = run_command(cmd, timeout=60)
            results.append(f"• {cmd}: {result}")
            
        return "\n".join(results)
    except Exception as e:
        return f"❌ Gagal install Termux API: {str(e)}"

# ======================== FUNGSI SISTEM ========================
def get_system_info():
    """Mendapatkan informasi sistem lengkap"""
    try:
        info = {}
        
        # Basic info
        info['username'] = run_command('whoami')
        info['hostname'] = socket.gethostname()
        
        # Network info
        try:
            info['ip_local'] = socket.gethostbyname(socket.gethostname())
        except:
            info['ip_local'] = "Tidak dapat dideteksi"
            
        try:
            info['ip_public'] = requests.get('https://api.ipify.org', timeout=5).text
        except:
            info['ip_public'] = "Tidak dapat dideteksi"
        
        # Memory info
        try:
            mem = psutil.virtual_memory()
            info['ram_total'] = f"{mem.total / (1024**3):.2f} GB"
            info['ram_used'] = f"{mem.used / (1024**3):.2f} GB"
            info['ram_free'] = f"{mem.available / (1024**3):.2f} GB"
            info['ram_percent'] = f"{mem.percent}%"
        except:
            info['ram_total'] = "N/A"
            info['ram_used'] = "N/A"
            info['ram_free'] = "N/A"
            info['ram_percent'] = "N/A"
        
        # Storage info
        try:
            disk = psutil.disk_usage('/')
            info['storage_total'] = f"{disk.total / (1024**3):.2f} GB"
            info['storage_used'] = f"{disk.used / (1024**3):.2f} GB"
            info['storage_free'] = f"{disk.free / (1024**3):.2f} GB"
            info['storage_percent'] = f"{(disk.used/disk.total)*100:.1f}%"
        except:
            info['storage_total'] = "N/A"
            info['storage_used'] = "N/A"
            info['storage_free'] = "N/A"
            info['storage_percent'] = "N/A"
        
        # OS info
        os_info = platform.uname()
        info['os_system'] = os_info.system
        info['os_release'] = os_info.release
        info['os_version'] = os_info.version
        info['machine'] = os_info.machine
        info['processor'] = os_info.processor
        
        # Battery info
        info['battery'] = run_command('termux-battery-status') or "N/A"
        
        # CPU info
        try:
            info['cpu_count'] = psutil.cpu_count()
            info['cpu_percent'] = f"{psutil.cpu_percent(interval=1)}%"
        except:
            info['cpu_count'] = "N/A"
            info['cpu_percent'] = "N/A"
        
        # Termux info
        info['termux_version'] = run_command('pkg list-installed | grep "^termux/"') or "N/A"
        info['api_status'] = "✅ Terinstall" if check_termux_api() else "❌ Tidak terinstall"
        
        message = f"""🖥️ *INFORMASI SISTEM LENGKAP*

👤 *User & Network*
├─ Username: `{info['username']}`
├─ Hostname: `{info['hostname']}`
├─ IP Lokal: `{info['ip_local']}`
└─ IP Publik: `{info['ip_public']}`

💾 *Memory (RAM)*
├─ Total: `{info['ram_total']}`
├─ Digunakan: `{info['ram_used']}`
├─ Tersedia: `{info['ram_free']}`
└─ Persentase: `{info['ram_percent']}`

💿 *Storage*
├─ Total: `{info['storage_total']}`
├─ Digunakan: `{info['storage_used']}`
├─ Tersedia: `{info['storage_free']}`
└─ Persentase: `{info['storage_percent']}`

🔧 *Prosesor*
├─ Jumlah Core: `{info['cpu_count']}`
├─ Penggunaan CPU: `{info['cpu_percent']}`
├─ Arsitektur: `{info['machine']}`
└─ Prosesor: `{info['processor']}`

📱 *Sistem Operasi*
├─ Sistem: `{info['os_system']}`
├─ Release: `{info['os_release']}`
└─ Versi: `{info['os_version']}`

🔋 *Status Device*
└─ Battery: `{info['battery']}`

🛠️ *Termux*
├─ API Status: {info['api_status']}
└─ Versi: `{info['termux_version']}`"""
        
        return message
        
    except Exception as e:
        return f"⚠️ Gagal mendapatkan info sistem: {str(e)}"

# ======================== FUNGSI KONTROL WIFI ========================
def wifi_control(action):
    """Kontrol WiFi dengan berbagai aksi"""
    if not check_termux_api():
        return "❌ Termux API belum terinstall. Gunakan /install_api"
    
    try:
        if action == "on":
            result = run_command('termux-wifi-enable true')
            return "📶 ✅ WiFi berhasil dihidupkan"
            
        elif action == "off":
            result = run_command('termux-wifi-enable false')
            return "📶 ❌ WiFi berhasil dimatikan"
            
        elif action == "info":
            # Get WiFi connection info
            wifi_info = run_command('termux-wifi-connectioninfo')
            wifi_scan = run_command('termux-wifi-scaninfo')
            
            message = f"📶 *INFORMASI WIFI*\n\n"
            message += f"🔗 *Koneksi Saat Ini*:\n`{wifi_info}`\n\n"
            
            if wifi_scan and len(wifi_scan) < 3000:
                message += f"🔍 *WiFi Terdeteksi*:\n`{wifi_scan}`"
            else:
                message += f"🔍 *WiFi Terdeteksi*: Terlalu banyak untuk ditampilkan"
                
            return message
            
        elif action == "scan":
            result = run_command('termux-wifi-scaninfo')
            return f"🔍 *WiFi Scan Results*:\n\n`{result}`"
            
        elif action == "status":
            # Cek status WiFi
            result = run_command('termux-wifi-connectioninfo')
            if "null" in result or not result:
                return "📶 ❌ WiFi tidak terhubung"
            else:
                return f"📶 ✅ WiFi terhubung\n\n`{result}`"
                
        else:
            return "❌ Aksi tidak valid. Gunakan: on/off/info/scan/status"
            
    except Exception as e:
        return f"❌ Gagal mengontrol WiFi: {str(e)}"

# ======================== FUNGSI KONTROL SENTER ========================
def flashlight_control(action):
    """Kontrol senter/flashlight"""
    if not check_termux_api():
        return "❌ Termux API belum terinstall. Gunakan /install_api"
    
    try:
        if action == "on":
            result = run_command('termux-torch on')
            return "🔦 ✅ Senter berhasil dihidupkan"
            
        elif action == "off":
            result = run_command('termux-torch off')
            return "🔦 ❌ Senter berhasil dimatikan"
            
        elif action == "toggle":
            # Toggle senter
            status = run_command('termux-torch')
            if "on" in status.lower():
                run_command('termux-torch off')
                return "🔦 ❌ Senter dimatikan (toggle)"
            else:
                run_command('termux-torch on')
                return "🔦 ✅ Senter dihidupkan (toggle)"
                
        else:
            return "❌ Aksi tidak valid. Gunakan: on/off/toggle"
            
    except Exception as e:
        return f"❌ Gagal mengontrol senter: {str(e)}"

# ======================== FUNGSI GETAR DEVICE ========================
def vibrate_device(duration):
    """Getarkan device dengan durasi tertentu"""
    if not check_termux_api():
        return "❌ Termux API belum terinstall. Gunakan /install_api"
    
    try:
        duration = int(duration)
        if duration < 100:
            duration = 100
        elif duration > 10000:
            duration = 10000
            
        result = run_command(f'termux-vibrate -d {duration}')
        return f"📳 ✅ Device bergetar selama {duration}ms"
        
    except ValueError:
        return "❌ Durasi harus berupa angka (100-10000 ms)"
    except Exception as e:
        return f"❌ Gagal menggetarkan device: {str(e)}"

# ======================== FUNGSI NOTIFIKASI ========================
def send_notification(title, content):
    """Kirim notifikasi ke device"""
    if not check_termux_api():
        return "❌ Termux API belum terinstall"
    
    try:
        cmd = f'termux-notification --title "{title}" --content "{content}"'
        result = run_command(cmd)
        return "🔔 ✅ Notifikasi berhasil dikirim"
    except Exception as e:
        return f"❌ Gagal mengirim notifikasi: {str(e)}"

# ======================== FUNGSI MANAJEMEN FILE ========================
def list_files(path="/sdcard"):
    """List file dan folder"""
    try:
        if not os.path.exists(path):
            return f"❌ Path tidak ditemukan: {path}"
            
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                items.append(f"📄 {item} ({size_str})")
        
        if not items:
            return f"📂 Folder kosong: {path}"
            
        result = f"📂 *Isi folder: {path}*\n\n"
        result += "\n".join(items[:50])  # Batasi 50 item
        
        if len(items) > 50:
            result += f"\n\n... dan {len(items)-50} item lainnya"
            
        return result
        
    except Exception as e:
        return f"❌ Gagal membaca folder: {str(e)}"

def create_folder(path):
    """Buat folder baru"""
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder berhasil dibuat: {path}"
    except Exception as e:
        return f"❌ Gagal membuat folder: {str(e)}"

def remove_file(path):
    """Hapus file atau folder"""
    try:
        if not os.path.exists(path):
            return f"❌ Path tidak ditemukan: {path}"
            
        if os.path.isfile(path):
            os.remove(path)
            return f"✅ File berhasil dihapus: {path}"
        else:
            shutil.rmtree(path)
            return f"✅ Folder berhasil dihapus: {path}"
            
    except Exception as e:
        return f"❌ Gagal menghapus: {str(e)}"

def copy_file(src, dst):
    """Salin file atau folder"""
    try:
        if not os.path.exists(src):
            return f"❌ Source tidak ditemukan: {src}"
            
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            return f"✅ File berhasil disalin dari {src} ke {dst}"
        else:
            shutil.copytree(src, dst)
            return f"✅ Folder berhasil disalin dari {src} ke {dst}"
            
    except Exception as e:
        return f"❌ Gagal menyalin: {str(e)}"

# ======================== FUNGSI INSTALL LIBRARY ========================
def install_library(lib_name):
    """Install library/package"""
    try:
        # Cek apakah sudah terinstall
        check_result = run_command(f'pkg list-installed | grep -i "^{lib_name}"')
        if check_result and not check_result.startswith("❌"):
            return f"✅ Library {lib_name} sudah terinstall"
        
        # Install library
        result = run_command(f'pkg install -y {lib_name}', timeout=120)
        
        if "error" in result.lower() or "❌" in result:
            return f"❌ Gagal install {lib_name}: {result}"
        else:
            return f"✅ Berhasil install {lib_name}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

def list_installed_packages():
    """List semua package yang terinstall"""
    try:
        result = run_command('pkg list-installed')
        return result if result else "Tidak ada package yang terinstall"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ======================== FUNGSI BOT PERSISTENCE ========================
def plant_bot():
    """Tanam bot agar auto-start"""
    try:
        # Buat direktori tersembunyi
        bot_dir = Path.home() / '.termux_controller'
        bot_dir.mkdir(exist_ok=True)
        
        # Salin script ke direktori tersembunyi
        current_script = Path(__file__)
        target_script = bot_dir / 'termux_bot.py'
        shutil.copy2(current_script, target_script)
        
        # Buat script startup
        startup_script = f'''#!/bin/bash
# Auto-start Termux Controller Bot
cd {bot_dir}
python termux_bot.py &
'''
        
        startup_file = Path.home() / '.bashrc'
        with open(startup_file, 'a') as f:
            f.write('\n# Termux Controller Bot Auto-Start\n')
            f.write(f'cd {bot_dir} && python termux_bot.py & 2>/dev/null\n')
        
        # Buat service file
        service_content = f'''#!/bin/bash
while true; do
    cd {bot_dir}
    python termux_bot.py
    sleep 5
done
'''
        
        service_file = bot_dir / 'run_bot.sh'
        with open(service_file, 'w') as f:
            f.write(service_content)
        os.chmod(service_file, 0o755)
        
        return f"🌱 ✅ Bot berhasil ditanam!\n\n📁 Lokasi: {bot_dir}\n🔄 Auto-start: Aktif\n\n⚠️ Restart Termux untuk mengaktifkan auto-start"
        
    except Exception as e:
        return f"❌ Gagal menanam bot: {str(e)}"

# ======================== HANDLER PERINTAH ========================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak! Bot ini hanya untuk pemilik.")
        return
    
    # Cek status Termux API
    api_status = "✅ Terinstall" if check_termux_api() else "❌ Tidak terinstall"
    
    welcome_msg = f"""🎉 *Selamat datang di {BOT_NAME}!*

👋 Halo *{message.from_user.first_name}*!

🤖 *{BOT_NAME}*
📦 *Versi*: `{VERSION}`
📅 *Rilis*: `{RELEASE_DATE}`
👨‍💻 *Developer*: [{DEVELOPER}]({GITHUB})

🔧 *Status Sistem*:
└─ Termux API: {api_status}

🚀 *Fitur Utama*:
• 📶 Kontrol WiFi (ON/OFF/Info)
• 🔦 Kontrol Senter (ON/OFF)
• 📳 Getar Device
• 📁 Manajemen File Lengkap
• 📦 Install/Manage Package
• 🔔 Notifikasi Device
• 🖥️ Informasi Sistem Detail
• 🌱 Bot Persistence

ℹ️ Ketik /help untuk panduan lengkap"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("📖 Help", callback_data="help"),
        types.InlineKeyboardButton("🛠️ Install API", callback_data="install_api")
    )
    keyboard.row(
        types.InlineKeyboardButton("🖥️ System Info", callback_data="sysinfo"),
        types.InlineKeyboardButton("🔧 Quick Controls", callback_data="controls")
    )
    
    bot.reply_to(message, welcome_msg, parse_mode='Markdown', reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def send_help(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    help_msg = f"""📖 *PANDUAN LENGKAP {BOT_NAME}*

🔧 *SETUP*
• `/install_api` - Install Termux API
• `/plant` - Tanam bot (auto-start)

📶 *KONTROL WIFI*
• `/wifi on` - Hidupkan WiFi
• `/wifi off` - Matikan WiFi
• `/wifi info` - Info WiFi detail
• `/wifi scan` - Scan WiFi tersedia
• `/wifi status` - Status koneksi

🔦 *KONTROL SENTER*
• `/flash on` - Hidupkan senter
• `/flash off` - Matikan senter
• `/flash toggle` - Toggle senter

📳 *DEVICE CONTROLS*
• `/vibrate <ms>` - Getar (100-10000ms)
• `/notify <title> <text>` - Kirim notifikasi

📁 *MANAJEMEN FILE*
• `/ls [path]` - List file/folder
• `/mkdir <path>` - Buat folder
• `/rm <path>` - Hapus file/folder
• `/cp <src> <dst>` - Salin file/folder

📦 *PACKAGE MANAGER*
• `/install <pkg>` - Install package
• `/pkglist` - List package terinstall
• `/update` - Update package list

🖥️ *SISTEM*
• `/sysinfo` - Info sistem lengkap
• `/cmd <command>` - Jalankan perintah
• `/uptime` - Waktu aktif sistem
• `/cleanup` - Bersihkan cache

🔔 *NOTIFIKASI & ALERT*
• `/alert <text>` - Alert cepat
• `/status` - Status bot lengkap

⚙️ *ADVANCED*
• `/screenshot` - Ambil screenshot
• `/battery` - Info baterai
• `/location` - Info lokasi

🆘 *Bantuan*: Jika ada masalah, coba install Termux API terlebih dahulu dengan `/install_api`"""

    bot.reply_to(message, help_msg, parse_mode='Markdown')

@bot.message_handler(commands=['install_api'])
def handle_install_api(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    bot.reply_to(message, "🔄 Menginstall Termux API... Mohon tunggu...")
    result = install_termux_api()
    bot.reply_to(message, f"📦 *Hasil Install Termux API*:\n\n{result}", parse_mode='Markdown')

# WiFi Controls
@bot.message_handler(commands=['wifi'])
def handle_wifi(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        action = message.text.split(maxsplit=1)[1].lower()
        result = wifi_control(action)
        bot.reply_to(message, result, parse_mode='Markdown')
    except IndexError:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📶 ON", callback_data="wifi_on"),
            types.InlineKeyboardButton("📶 OFF", callback_data="wifi_off")
        )
        keyboard.row(
            types.InlineKeyboardButton("ℹ️ Info", callback_data="wifi_info"),
            types.InlineKeyboardButton("🔍 Scan", callback_data="wifi_scan")
        )
        bot.reply_to(message, "📶 *Kontrol WiFi*\n\nPilih aksi:", parse_mode='Markdown', reply_markup=keyboard)

# Flashlight Controls
@bot.message_handler(commands=['flash'])
def handle_flash(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        action = message.text.split(maxsplit=1)[1].lower()
        result = flashlight_control(action)
        bot.reply_to(message, result)
    except IndexError:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("🔦 ON", callback_data="flash_on"),
            types.InlineKeyboardButton("🔦 OFF", callback_data="flash_off")
        )
        keyboard.row(types.InlineKeyboardButton("🔄 Toggle", callback_data="flash_toggle"))
        bot.reply_to(message, "🔦 *Kontrol Senter*\n\nPilih aksi:", parse_mode='Markdown', reply_markup=keyboard)

# Vibrate Control
@bot.message_handler(commands=['vibrate'])
def handle_vibrate(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        duration = message.text.split(maxsplit=1)[1]
        result = vibrate_device(duration)
        bot.reply_to(message, result)
    except IndexError:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📳 200ms", callback_data="vibrate_200"),
            types.InlineKeyboardButton("📳 500ms", callback_data="vibrate_500")
        )
        keyboard.row(
            types.InlineKeyboardButton("📳 1000ms", callback_data="vibrate_1000"),
            types.InlineKeyboardButton("📳 2000ms", callback_data="vibrate_2000")
        )
        bot.reply_to(message, "📳 *Getar Device*\n\nPilih durasi atau ketik: `/vibrate <durasi_ms>`", parse_mode='Markdown', reply_markup=keyboard)

# System Info
@bot.message_handler(commands=['sysinfo'])
def handle_sysinfo(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    bot.reply_to(message, "🔄 Mengumpulkan informasi sistem...")
    info = get_system_info()
    bot.reply_to(message, info, parse_mode='Markdown')

# File Management
@bot.message_handler(commands=['ls'])
def handle_ls(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        path = message.text.split(maxsplit=1)[1]
    except IndexError:
        path = "/sdcard"
    
    result = list_files(path)
    if len(result) > 4000:
        # Kirim sebagai file jika terlalu panjang
        with open('filelist.txt', 'w') as f:
            f.write(result)
        with open('filelist.txt', 'rb') as f:
            bot.send_document(message.chat.id, f, caption=f"📂 File list: {path}")
        os.remove('filelist.txt')
    else:
        bot.reply_to(message, result, parse_mode='Markdown')

@bot.message_handler(commands=['mkdir'])
def handle_mkdir(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        path = message.text.split(maxsplit=1)[1]
        result = create_folder(path)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format: /mkdir <path>")

@bot.message_handler(commands=['rm'])
def handle_rm(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        path = message.text.split(maxsplit=1)[1]
        result = remove_file(path)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format: /rm <path>")

@bot.message_handler(commands=['cp'])
def handle_cp(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        _, src, dst = message.text.split(maxsplit=2)
        result = copy_file(src, dst)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "❌ Format: /cp <source> <destination>")

# Package Management
@bot.message_handler(commands=['install'])
def handle_install(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        pkg_name = message.text.split(maxsplit=1)[1]
        bot.reply_to(message, f"🔄 Menginstall {pkg_name}... Mohon tunggu...")
        result = install_library(pkg_name)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format: /install <package_name>")

@bot.message_handler(commands=['pkglist'])
def handle_pkglist(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    result = list_installed_packages()
    if len(result) > 4000:
        with open('packages.txt', 'w') as f:
            f.write(result)
        with open('packages.txt', 'rb') as f:
            bot.send_document(message.chat.id, f, caption="📦 Package List")
        os.remove('packages.txt')
    else:
        bot.reply_to(message, f"📦 *Installed Packages*:\n\n```\n{result}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['update'])
def handle_update(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    bot.reply_to(message, "🔄 Updating package list...")
    result = run_command('pkg update -y', timeout=120)
    bot.reply_to(message, f"✅ Update completed:\n\n`{result}`", parse_mode='Markdown')

# Command Execution
@bot.message_handler(commands=['cmd'])
def handle_cmd(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        command = message.text.split(maxsplit=1)[1]
        
        # Security check - block dangerous commands
        dangerous_cmds = ['rm -rf /', 'format', 'dd if=', 'mkfs.', 'fdisk', ': (){ :|:& };:']
        if any(dangerous in command.lower() for dangerous in dangerous_cmds):
            bot.reply_to(message, "⛔ Perintah berbahaya diblokir untuk keamanan!")
            return
        
        result = run_command(command, timeout=30)
        
        if len(result) > 4000:
            with open('command_output.txt', 'w') as f:
                f.write(f"Command: {command}\n\nOutput:\n{result}")
            with open('command_output.txt', 'rb') as f:
                bot.send_document(message.chat.id, f, caption=f"⚙️ Output: `{command}`")
            os.remove('command_output.txt')
        else:
            bot.reply_to(message, f"⚙️ *Command*: `{command}`\n\n*Output*:\n```\n{result}\n```", parse_mode='Markdown')
            
    except IndexError:
        bot.reply_to(message, "❌ Format: /cmd <command>")

# Notification
@bot.message_handler(commands=['notify'])
def handle_notify(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        title = parts[1]
        content = parts[2]
        result = send_notification(title, content)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format: /notify <title> <content>")

# Quick Alert
@bot.message_handler(commands=['alert'])
def handle_alert(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    try:
        alert_text = message.text.split(maxsplit=1)[1]
        result = send_notification("🚨 ALERT", alert_text)
        vibrate_device("1000")  # Getar juga
        bot.reply_to(message, f"{result}\n📳 Device bergetar")
    except IndexError:
        bot.reply_to(message, "❌ Format: /alert <message>")

# Advanced Features
@bot.message_handler(commands=['battery'])
def handle_battery(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    if not check_termux_api():
        bot.reply_to(message, "❌ Termux API belum terinstall. Gunakan /install_api")
        return
    
    result = run_command('termux-battery-status')
    try:
        battery_info = json.loads(result)
        message_text = f"""🔋 *INFORMASI BATERAI*

📊 *Level*: {battery_info.get('percentage', 'N/A')}%
🔌 *Status*: {battery_info.get('status', 'N/A')}
⚡ *Health*: {battery_info.get('health', 'N/A')}
🌡️ *Temperature*: {battery_info.get('temperature', 'N/A')}°C
⚡ *Plugged*: {battery_info.get('plugged', 'N/A')}
🔋 *Current*: {battery_info.get('current', 'N/A')} mA"""
        bot.reply_to(message, message_text, parse_mode='Markdown')
    except:
        bot.reply_to(message, f"🔋 *Battery Info*:\n\n`{result}`", parse_mode='Markdown')

@bot.message_handler(commands=['location'])
def handle_location(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    if not check_termux_api():
        bot.reply_to(message, "❌ Termux API belum terinstall. Gunakan /install_api")
        return
    
    bot.reply_to(message, "🗺️ Mendapatkan lokasi... (izinkan akses lokasi jika diminta)")
    result = run_command('termux-location -p gps', timeout=15)
    
    try:
        location_info = json.loads(result)
        lat = location_info.get('latitude', 'N/A')
        lng = location_info.get('longitude', 'N/A')
        accuracy = location_info.get('accuracy', 'N/A')
        altitude = location_info.get('altitude', 'N/A')
        
        message_text = f"""🗺️ *INFORMASI LOKASI*

📍 *Latitude*: `{lat}`
📍 *Longitude*: `{lng}`
🎯 *Accuracy*: `{accuracy}m`
⛰️ *Altitude*: `{altitude}m`

🌐 *Google Maps*: [Buka Lokasi](https://maps.google.com/?q={lat},{lng})"""
        
        bot.reply_to(message, message_text, parse_mode='Markdown')
        
        # Kirim lokasi sebagai pin juga
        if lat != 'N/A' and lng != 'N/A':
            bot.send_location(message.chat.id, float(lat), float(lng))
            
    except:
        bot.reply_to(message, f"🗺️ *Location Info*:\n\n`{result}`", parse_mode='Markdown')

@bot.message_handler(commands=['screenshot'])
def handle_screenshot(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    if not check_termux_api():
        bot.reply_to(message, "❌ Termux API belum terinstall. Gunakan /install_api")
        return
    
    bot.reply_to(message, "📸 Mengambil screenshot...")
    
    # Buat nama file unik
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"/sdcard/screenshot_{timestamp}.png"
    
    result = run_command(f'termux-camera-photo {screenshot_path}')
    
    if os.path.exists(screenshot_path):
        try:
            with open(screenshot_path, 'rb') as photo:
                bot.send_photo(message.chat.id, photo, caption=f"📸 Screenshot - {timestamp}")
            os.remove(screenshot_path)  # Hapus file setelah dikirim
        except Exception as e:
            bot.reply_to(message, f"❌ Gagal mengi

@bot.message_handler(commands=['uptime'])
def handle_uptime(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    uptime = run_command('uptime')
    boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%A, %d %B %Y %H:%M:%S")
    
    message_text = f"""⏰ *WAKTU SISTEM*

🕐 *Uptime*: `{uptime}`
🚀 *Boot Time*: `{boot_time}`
📅 *Sekarang*: `{datetime.now().strftime("%A, %d %B %Y %H:%M:%S")}`"""
    
    bot.reply_to(message, message_text, parse_mode='Markdown')

@bot.message_handler(commands=['cleanup'])
def handle_cleanup(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    bot.reply_to(message, "🧹 Membersihkan cache dan file temporary...")
    
    commands = [
        'pkg clean',
        'apt autoremove -y',
        'rm -rf /data/data/com.termux/files/usr/tmp/*',
        'rm -rf ~/.cache/*'
    ]
    
    results = []
    for cmd in commands:
        result = run_command(cmd)
        results.append(f"• {cmd}: ✅")
    
    message_text = "🧹 *CLEANUP COMPLETED*\n\n" + "\n".join(results) + "\n\n✨ Cache berhasil dibersihkan!"
    bot.reply_to(message, message_text, parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def handle_status(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    # Status lengkap bot dan sistem
    api_status = "✅ Aktif" if check_termux_api() else "❌ Tidak aktif"
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
    except:
        cpu_percent = "N/A"
        memory = None
        disk = None
    
    message_text = f"""📊 *STATUS SISTEM & BOT*

🤖 *Bot Status*
├─ Nama: {BOT_NAME}
├─ Versi: {VERSION}
├─ Uptime Bot: Aktif
└─ API Status: {api_status}

💻 *Sistem Performance*
├─ CPU Usage: {cpu_percent}%
├─ RAM Usage: {memory.percent if memory else 'N/A'}%
└─ Storage Usage: {(disk.used/disk.total)*100:.1f}% if disk else 'N/A'

🕐 *Waktu*
└─ Sekarang: {datetime.now().strftime("%H:%M:%S, %d %b %Y")}

✅ *Semua sistem berjalan normal!*"""
    
    bot.reply_to(message, message_text, parse_mode='Markdown')

# Plant Bot
@bot.message_handler(commands=['plant'])
def handle_plant(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
    
    result = plant_bot()
    bot.reply_to(message, result, parse_mode='Markdown')

# ======================== CALLBACK HANDLERS ========================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if str(call.message.chat.id) != str(CHAT_ID):
        bot.answer_callback_query(call.id, "⛔ Akses ditolak!")
        return
    
    # WiFi callbacks
    if call.data.startswith('wifi_'):
        action = call.data.replace('wifi_', '')
        result = wifi_control(action)
        bot.answer_callback_query(call.id, "📶 Processing...")
        bot.edit_message_text(result, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    # Flash callbacks
    elif call.data.startswith('flash_'):
        action = call.data.replace('flash_', '')
        result = flashlight_control(action)
        bot.answer_callback_query(call.id, "🔦 Processing...")
        bot.edit_message_text(result, call.message.chat.id, call.message.message_id)
    
    # Vibrate callbacks
    elif call.data.startswith('vibrate_'):
        duration = call.data.replace('vibrate_', '')
        result = vibrate_device(duration)
        bot.answer_callback_query(call.id, "📳 Vibrating...")
        bot.edit_message_text(result, call.message.chat.id, call.message.message_id)
    
    # Other callbacks
    elif call.data == 'help':
        help_msg = """📖 *QUICK HELP*

🔧 *Setup*: /install_api, /plant
📶 *WiFi*: /wifi <on/off/info>
🔦 *Flash*: /flash <on/off>
📳 *Vibrate*: /vibrate <ms>
📁 *Files*: /ls, /mkdir, /rm, /cp
📦 *Packages*: /install, /pkglist
🖥️ *System*: /sysinfo, /cmd

Type /help for full manual"""
        bot.edit_message_text(help_msg, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    elif call.data == 'install_api':
        bot.answer_callback_query(call.id, "🔄 Installing API...")
        result = install_termux_api()
        bot.edit_message_text(f"📦 *Install Termux API*:\n\n{result}", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    elif call.data == 'sysinfo':
        bot.answer_callback_query(call.id, "🔄 Getting system info...")
        info = get_system_info()
        bot.edit_message_text(info, call.message.chat.id, call.message.message_id, parse_mode='Markdown')
    
    elif call.data == 'controls':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📶 WiFi", callback_data="control_wifi"),
            types.InlineKeyboardButton("🔦 Flash", callback_data="control_flash")
        )
        keyboard.row(
            types.InlineKeyboardButton("📳 Vibrate", callback_data="control_vibrate"),
            types.InlineKeyboardButton("🔔 Notify", callback_data="control_notify")
        )
        keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="back_main"))
        
        bot.edit_message_text("🔧 *Quick Controls*\n\nPilih kontrol yang ingin digunakan:", 
                             call.message.chat.id, call.message.message_id, 
                             parse_mode='Markdown', reply_markup=keyboard)
    
    elif call.data == 'control_wifi':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📶 ON", callback_data="wifi_on"),
            types.InlineKeyboardButton("📶 OFF", callback_data="wifi_off")
        )
        keyboard.row(
            types.InlineKeyboardButton("ℹ️ Info", callback_data="wifi_info"),
            types.InlineKeyboardButton("🔍 Scan", callback_data="wifi_scan")
        )
        keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="controls"))
        
        bot.edit_message_text("📶 *WiFi Control*\n\nPilih aksi:", 
                             call.message.chat.id, call.message.message_id,
                             parse_mode='Markdown', reply_markup=keyboard)
    
    elif call.data == 'control_flash':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("🔦 ON", callback_data="flash_on"),
            types.InlineKeyboardButton("🔦 OFF", callback_data="flash_off")
        )
        keyboard.row(types.InlineKeyboardButton("🔄 Toggle", callback_data="flash_toggle"))
        keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="controls"))
        
        bot.edit_message_text("🔦 *Flashlight Control*\n\nPilih aksi:", 
                             call.message.chat.id, call.message.message_id,
                             parse_mode='Markdown', reply_markup=keyboard)
    
    elif call.data == 'control_vibrate':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("📳 200ms", callback_data="vibrate_200"),
            types.InlineKeyboardButton("📳 500ms", callback_data="vibrate_500")
        )
        keyboard.row(
            types.InlineKeyboardButton("📳 1s", callback_data="vibrate_1000"),
            types.InlineKeyboardButton("📳 2s", callback_data="vibrate_2000")
        )
        keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="controls"))
        
        bot.edit_message_text("📳 *Vibrate Control*\n\nPilih durasi:", 
                             call.message.chat.id, call.message.message_id,
                             parse_mode='Markdown', reply_markup=keyboard)

# ======================== MESSAGE HANDLERS ========================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if str(message.chat.id) != str(CHAT_ID):
        bot.reply_to(message, "⛔ Akses ditolak! Bot ini hanya untuk pemilik terverifikasi.")
        return
    
    # Smart command suggestion
    text = message.text.lower()
    
    if any(word in text for word in ['wifi', 'internet', 'network']):
        bot.reply_to(message, "💡 Mungkin Anda ingin mengontrol WiFi? Coba: /wifi")
    elif any(word in text for word in ['flash', 'senter', 'lampu']):
        bot.reply_to(message, "💡 Mungkin Anda ingin mengontrol senter? Coba: /flash")
    elif any(word in text for word in ['getar', 'vibrat', 'bergetar']):
        bot.reply_to(message, "💡 Mungkin Anda ingin menggetarkan device? Coba: /vibrate <durasi>")
    elif any(word in text for word in ['info', 'sistem', 'status']):
        bot.reply_to(message, "💡 Mungkin Anda ingin melihat info sistem? Coba: /sysinfo")
    elif any(word in text for word in ['install', 'package', 'pkg']):
        bot.reply_to(message, "💡 Mungkin Anda ingin install package? Coba: /install <nama_package>")
    elif any(word in text for word in ['file', 'folder', 'ls', 'list']):
        bot.reply_to(message, "💡 Mungkin Anda ingin melihat file? Coba: /ls")
    else:
        bot.reply_to(message, f"""❓ *Perintah tidak dikenali*

💡 *Saran perintah populer*:
• `/help` - Panduan lengkap
• `/sysinfo` - Info sistem
• `/wifi info` - Status WiFi  
• `/flash on` - Hidupkan senter
• `/vibrate 500` - Getar device

Atau ketik pesan yang mengandung kata kunci seperti: wifi, senter, getar, dll.""", parse_mode='Markdown')

# ======================== ERROR HANDLER ========================
@bot.message_handler(func=lambda message: True, content_types=['photo', 'document', 'audio', 'video'])
def handle_files(message):
    if str(message.chat.id) != str(CHAT_ID):
        return
    
    bot.reply_to(message, "📁 File diterima! Saat ini bot hanya mendukung perintah teks. Gunakan /help untuk melihat perintah yang tersedia.")

# ======================== MAIN FUNCTION ========================
def main():
    """Fungsi utama untuk menjalankan bot"""
    
    # Cek konfigurasi
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("❌ ERROR: Bot token dan Chat ID harus dikonfigurasi!")
        print("📝 Edit script dan ganti YOUR_BOT_TOKEN_HERE dan YOUR_CHAT_ID_HERE")
        print("🔗 Atau set environment variables: BOT_TOKEN dan CHAT_ID")
        return
    
    # Auto-install dependencies
    print("🔄 Checking dependencies...")
    required_packages = [
        'python',
        'python3', 
        'python-pip'
    ]
    
    pip_packages = [
        'pyTelegramBotAPI',
        'psutil',
        'requests'
    ]
    
    # Install system packages
    for pkg in required_packages:
        try:
            result = subprocess.run(['pkg', 'list-installed'], 
                                  capture_output=True, text=True)
            if pkg not in result.stdout:
                print(f"📦 Installing {pkg}...")
                subprocess.run(['pkg', 'install', '-y', pkg], 
                             capture_output=True)
        except:
            pass
    
    # Install Python packages
    for pkg in pip_packages:
        try:
            __import__(pkg.replace('-', '_').split('_')[0])
        except ImportError:
            print(f"🐍 Installing Python package: {pkg}")
            subprocess.run(['pip', 'install', pkg], capture_output=True)
    
    # Tampilkan info startup
    print(f"""
{'='*50}
🤖 {BOT_NAME}
📦 Versi: {VERSION}
📅 Rilis: {RELEASE_DATE}
👨‍💻 Developer: {DEVELOPER}
🌐 GitHub: {GITHUB}
{'='*50}
✅ Bot berhasil diinisialisasi!
🔄 Memulai polling...
📱 Chat ID: {CHAT_ID}
🔧 API Status: {'✅ Ready' if check_termux_api() else '❌ Install required'}
{'='*50}
""")
    
    # Kirim notifikasi startup ke chat
    try:
        startup_msg = f"""🚀 *{BOT_NAME} STARTED*

✅ Bot berhasil dijalankan!
🕐 Waktu: {datetime.now().strftime('%H:%M:%S, %d %b %Y')}
🔧 Status: Siap menerima perintah

Ketik /help untuk panduan lengkap."""
        
        bot.send_message(CHAT_ID, startup_msg, parse_mode='Markdown')
    except:
        print("⚠️ Tidak dapat mengirim notifikasi startup (mungkin bot token salah)")
    
    # Mulai polling dengan error handling
    while True:
        try:
            print("🔄 Starting bot polling...")
            bot.infinity_polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            print(f"❌ Bot error: {str(e)}")
            print("🔄 Restarting in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    main()
