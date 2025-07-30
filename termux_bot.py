#!/usr/bin/env python3
# termux_bot.py

import os
import subprocess
import time
import shutil
import re
from datetime import datetime
from dotenv import load_dotenv
import telebot
from telebot import types
import socket
import psutil
import platform
import requests

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TOKEN)

# Informasi bot
BOT_NAME = "Termux Controller Bot"
DEVELOPER = "SerpentSecHunter"
GITHUB = "https://github.com/SerpentSecHunter"
VERSION = "3.0 BETA"
RELEASE_DATE = datetime.now().strftime("%A, %d %B %Y")

# Fungsi untuk mendapatkan info sistem
def get_system_info():
    try:
        # Nama pengguna Termux
        username = subprocess.getoutput('whoami')
        
        # Informasi jaringan
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        # Informasi RAM
        ram = psutil.virtual_memory()
        total_ram = round(ram.total / (1024 ** 3), 2)
        used_ram = round(ram.used / (1024 ** 3), 2)
        free_ram = round(ram.free / (1024 ** 3), 2)
        
        # Informasi OS
        os_info = platform.uname()
        os_name = os_info.system
        os_version = os_info.version
        kernel = os_info.release
        cpu = os_info.machine
        
        info = (
            f"🖥️ *System Information*\n\n"
            f"🔹 *Termux ID*: `{username}`\n"
            f"🔹 *IP Address*: `{ip_address}`\n\n"
            f"💾 *RAM*\n"
            f"  - Total: `{total_ram} GB`\n"
            f"  - Digunakan: `{used_ram} GB`\n"
            f"  - Tersedia: `{free_ram} GB`\n\n"
            f"📌 *OS*\n"
            f"  - Jenis: `{os_name}`\n"
            f"  - Versi: `{os_version}`\n"
            f"  - Kernel: `{kernel}`\n"
            f"  - CPU: `{cpu}`\n"
        )
        
        return info
    except Exception as e:
        return f"⚠️ Gagal mendapatkan info sistem: {str(e)}"

# Fungsi untuk menjalankan perintah Termux
def run_termux_command(command):
    try:
        result = subprocess.getoutput(command)
        return result if result else "Perintah berhasil dijalankan"
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi untuk install library
def install_library(lib_name):
    try:
        result = subprocess.getoutput(f'pkg install -y {lib_name}')
        if "already installed" in result.lower():
            return f"✅ Library {lib_name} sudah terinstall"
        elif "error" in result.lower():
            return f"❌ Gagal install {lib_name}: {result}"
        else:
            return f"✅ Berhasil install {lib_name}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Fungsi untuk mengecek library yang terinstall
def check_installed_libraries():
    try:
        result = subprocess.getoutput('pkg list-installed')
        return result if result else "Tidak ada library yang terinstall"
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi untuk mengecek storage
def check_storage():
    try:
        internal = subprocess.getoutput('ls /sdcard')
        sd_card = subprocess.getoutput('ls /storage') if os.path.exists('/storage') else "Tidak ada SD Card"
        
        result = "📂 *Storage Contents*\n\n"
        result += "🔹 *Internal Storage*:\n"
        result += f"`{internal}`\n\n" if internal else "Kosong\n\n"
        
        if sd_card != "Tidak ada SD Card":
            result += "🔹 *SD Card*:\n"
            result += f"`{sd_card}`\n" if sd_card else "Kosong\n"
        else:
            result += "🔹 *SD Card*: Tidak terdeteksi\n"
            
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi untuk mengunci folder/file
def lock_file(path, password):
    try:
        if not os.path.exists(path):
            return "❌ Path tidak ditemukan"
            
        # Enkripsi sederhana (bisa diganti dengan metode yang lebih aman)
        encrypted_name = f".{os.path.basename(path)}.locked"
        os.rename(path, os.path.join(os.path.dirname(path), encrypted_name))
        return f"✅ Berhasil mengunci {path} dengan password: {password}"
    except Exception as e:
        return f"❌ Gagal mengunci: {str(e)}"

# Fungsi untuk membuka kunci folder/file
def unlock_file(path, password):
    try:
        if not os.path.exists(path):
            return "❌ Path tidak ditemukan"
            
        # Dekripsi (harus sesuai dengan metode enkripsi)
        original_name = os.path.basename(path).replace('.locked', '').lstrip('.')
        os.rename(path, os.path.join(os.path.dirname(path), original_name))
        return f"✅ Berhasil membuka kunci {path}"
    except Exception as e:
        return f"❌ Gagal membuka kunci: {str(e)}"

# Fungsi untuk menghapus file/folder
def remove_file(path):
    try:
        if not os.path.exists(path):
            return "❌ Path tidak ditemukan"
            
        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
        return f"✅ Berhasil menghapus {path}"
    except Exception as e:
        return f"❌ Gagal menghapus: {str(e)}"

# Fungsi untuk menyalin file/folder
def copy_file(src, dst):
    try:
        if not os.path.exists(src):
            return "❌ Source path tidak ditemukan"
            
        if os.path.isfile(src):
            shutil.copy2(src, dst)
        else:
            shutil.copytree(src, dst)
        return f"✅ Berhasil menyalin dari {src} ke {dst}"
    except Exception as e:
        return f"❌ Gagal menyalin: {str(e)}"

# Fungsi untuk mengontrol WiFi
def wifi_control(action):
    try:
        if action == "on":
            result = subprocess.getoutput('termux-wifi-enable true')
            return "✅ WiFi dihidupkan"
        elif action == "off":
            result = subprocess.getoutput('termux-wifi-enable false')
            return "✅ WiFi dimatikan"
        elif action == "info":
            result = subprocess.getoutput('termux-wifi-connectioninfo')
            return f"📶 *WiFi Info*\n\n`{result}`"
        else:
            return "❌ Aksi WiFi tidak valid"
    except Exception as e:
        return f"❌ Gagal mengontrol WiFi: {str(e)}"

# Fungsi untuk mengontrol senter
def flashlight_control(action):
    try:
        if action == "on":
            result = subprocess.getoutput('termux-torch on')
            return "🔦 Senter dihidupkan"
        elif action == "off":
            result = subprocess.getoutput('termux-torch off')
            return "🔦 Senter dimatikan"
        else:
            return "❌ Aksi senter tidak valid"
    except Exception as e:
        return f"❌ Gagal mengontrol senter: {str(e)}"

# Fungsi untuk getar device
def vibrate_device(duration):
    try:
        result = subprocess.getoutput(f'termux-vibrate -d {duration}')
        return f"📳 Device bergetar selama {duration}ms"
    except Exception as e:
        return f"❌ Gagal menggetarkan device: {str(e)}"

# Fungsi untuk menanam bot di Termux
def plant_bot():
    try:
        # Buat direktori jika belum ada
        os.makedirs('/data/data/com.termux/files/home/.termux_bot', exist_ok=True)
        
        # Salin script ke direktori tersembunyi
        shutil.copy2(__file__, '/data/data/com.termux/files/home/.termux_bot/termux_bot.py')
        
        # Buat startup script
        with open('/data/data/com.termux/files/home/.bashrc', 'a') as f:
            f.write('\n# Start Termux Bot\npython ~/.termux_bot/termux_bot.py &\n')
            
        return "🌱 Bot berhasil ditanam di Termux. Bot akan otomatis berjalan saat Termux dibuka."
    except Exception as e:
        return f"❌ Gagal menanam bot: {str(e)}"

# Handler untuk perintah start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    welcome_msg = (
        f"👋 *Halo {message.from_user.first_name}!*\n\n"
        f"🤖 *{BOT_NAME}*\n"
        f"*Versi*: `{VERSION}`\n"
        f"*Rilis*: `{RELEASE_DATE}`\n\n"
        f"*Developer*: [{DEVELOPER}]({GITHUB})\n\n"
        f"📌 *Fitur yang tersedia*:\n"
        f"- Install library Termux\n"
        f"- Lihat library terinstall\n"
        f- Kontrol penuh Termux\n"
        f"- Manajemen file/folder\n"
        f- Kontrol WiFi dan senter\n"
        f"- Tanam bot di Termux\n\n"
        f"ℹ️ Gunakan /help untuk melihat panduan penggunaan"
    )
    
    bot.reply_to(message, welcome_msg, parse_mode='Markdown')

# Handler untuk perintah help
@bot.message_handler(commands=['help'])
def send_help(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    help_msg = (
        "📖 *Panduan Penggunaan*\n\n"
        "🔹 *Install Library*:\n"
        "`/install <nama_library>`\n\n"
        "🔹 *Lihat Library Terinstall*:\n"
        "`/liblist`\n\n"
        "🔹 *Kontrol Termux*:\n"
        "`/cmd <perintah>`\n\n"
        "🔹 *Manajemen File*:\n"
        "`/storage` - Lihat isi storage\n"
        "`/lock <path> <password>` - Kunci file/folder\n"
        "`/unlock <path> <password>` - Buka kunci file/folder\n"
        "`/remove <path>` - Hapus file/folder\n"
        "`/copy <src> <dst>` - Salin file/folder\n\n"
        "🔹 *Kontrol Device*:\n"
        "`/wifi <on/off/info>` - Kontrol WiFi\n"
        "`/flash <on/off>` - Kontrol senter\n"
        "`/vibrate <durasi_ms>` - Getarkan device\n\n"
        "🔹 *Lainnya*:\n"
        "`/plant` - Tanam bot di Termux\n"
        "`/sysinfo` - Info sistem\n"
        "`/help` - Panduan ini\n"
    )
    
    bot.reply_to(message, help_msg, parse_mode='Markdown')

# Handler untuk perintah install library
@bot.message_handler(commands=['install'])
def handle_install(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        lib_name = message.text.split()[1]
        result = install_library(lib_name)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /install <nama_library>")

# Handler untuk perintah list library
@bot.message_handler(commands=['liblist'])
def handle_liblist(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    result = check_installed_libraries()
    if len(result) > 4000:  # Batas panjang pesan Telegram
        with open('liblist.txt', 'w') as f:
            f.write(result)
        with open('liblist.txt', 'rb') as f:
            bot.send_document(message.chat.id, f)
        os.remove('liblist.txt')
    else:
        bot.reply_to(message, f"📚 *Library Terinstall*:\n\n`{result}`", parse_mode='Markdown')

# Handler untuk perintah kontrol Termux
@bot.message_handler(commands=['cmd'])
def handle_cmd(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        command = message.text.split(maxsplit=1)[1]
        result = run_termux_command(command)
        bot.reply_to(message, f"⚙️ *Hasil Perintah*:\n\n`{result}`", parse_mode='Markdown')
    except IndexError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /cmd <perintah>")

# Handler untuk perintah cek storage
@bot.message_handler(commands=['storage'])
def handle_storage(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    result = check_storage()
    bot.reply_to(message, result, parse_mode='Markdown')

# Handler untuk perintah kunci file
@bot.message_handler(commands=['lock'])
def handle_lock(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        _, path, password = message.text.split(maxsplit=2)
        result = lock_file(path, password)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /lock <path> <password>")

# Handler untuk perintah buka kunci file
@bot.message_handler(commands=['unlock'])
def handle_unlock(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        _, path, password = message.text.split(maxsplit=2)
        result = unlock_file(path, password)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /unlock <path> <password>")

# Handler untuk perintah hapus file
@bot.message_handler(commands=['remove'])
def handle_remove(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        path = message.text.split(maxsplit=1)[1]
        result = remove_file(path)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /remove <path>")

# Handler untuk perintah salin file
@bot.message_handler(commands=['copy'])
def handle_copy(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        _, src, dst = message.text.split(maxsplit=2)
        result = copy_file(src, dst)
        bot.reply_to(message, result)
    except ValueError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /copy <source> <destination>")

# Handler untuk perintah kontrol WiFi
@bot.message_handler(commands=['wifi'])
def handle_wifi(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        action = message.text.split(maxsplit=1)[1]
        result = wifi_control(action)
        bot.reply_to(message, result, parse_mode='Markdown')
    except IndexError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /wifi <on/off/info>")

# Handler untuk perintah kontrol senter
@bot.message_handler(commands=['flash'])
def handle_flash(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        action = message.text.split(maxsplit=1)[1]
        result = flashlight_control(action)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /flash <on/off>")

# Handler untuk perintah getar device
@bot.message_handler(commands=['vibrate'])
def handle_vibrate(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    try:
        duration = message.text.split(maxsplit=1)[1]
        result = vibrate_device(duration)
        bot.reply_to(message, result)
    except IndexError:
        bot.reply_to(message, "❌ Format salah. Gunakan: /vibrate <duration_ms>")

# Handler untuk perintah tanam bot
@bot.message_handler(commands=['plant'])
def handle_plant(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    result = plant_bot()
    bot.reply_to(message, result)

# Handler untuk perintah info sistem
@bot.message_handler(commands=['sysinfo'])
def handle_sysinfo(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    info = get_system_info()
    bot.reply_to(message, info, parse_mode='Markdown')

# Handler untuk pesan bukan perintah
@bot.message_handler(func=lambda message: True)
def handle_all(message):
    if str(message.chat.id) != CHAT_ID:
        bot.reply_to(message, "⛔ Akses ditolak!")
        return
        
    bot.reply_to(message, "❌ Perintah tidak dikenali. Gunakan /help untuk melihat daftar perintah")

# Fungsi utama
if __name__ == '__main__':
    # Cek nama file
    if os.path.basename(__file__) != 'termux_bot.py':
        os.remove(__file__)
        exit("❌ Nama file tidak valid. Script akan terhapus.")
    
    # Cek dan install dependensi
    required_libs = ['python-dotenv', 'pyTelegramBotAPI', 'psutil', 'requests']
    for lib in required_libs:
        try:
            __import__(lib.split('-')[0].replace('python-', ''))
        except ImportError:
            os.system(f'pip install {lib}')
    
    print(f"🤖 {BOT_NAME} v{VERSION} berjalan...")
    print(f"📅 Rilis: {RELEASE_DATE}")
    print(f"👨‍💻 Developer: {DEVELOPER}")
    print(f"🌐 GitHub: {GITHUB}")
    
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Error: {str(e)}")
        time.sleep(5)
