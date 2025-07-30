#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TermuxBot - Bot Telegram untuk Kontrol Termux
Developed by: SerpentSecHunter
GitHub: https://github.com/SerpentSecHunter
Version: 3.0 BETA
Release: Rabu, 30 Juli 2025
"""

import os
import sys
import subprocess
import json
import shutil
import platform
import psutil
import socket
import time
import threading
from datetime import datetime
from pathlib import Path
import requests
import telebot
from dotenv import load_dotenv
import cryptography.fernet as Fernet
import hashlib
import base64

# Load environment variables
load_dotenv()

# Konfigurasi Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not all([BOT_TOKEN, CHAT_ID, GEMINI_API_KEY]):
    print("❌ Error: Token, Chat ID, atau API Key tidak ditemukan!")
    print("Pastikan file .env berisi:")
    print("BOT_TOKEN=your_bot_token")
    print("CHAT_ID=your_chat_id") 
    print("GEMINI_API_KEY=your_gemini_api_key")
    sys.exit(1)

# Inisialisasi Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Variabel Global
locked_files = {}
hidden_files = set()
bot_planted = False
wifi_enabled = False
flashlight_enabled = False

class TermuxController:
    def __init__(self):
        self.install_required_libraries()
        
    def install_required_libraries(self):
        """Install library yang diperlukan secara otomatis"""
        required_libs = [
            'pyTelegramBotAPI',
            'python-dotenv', 
            'psutil',
            'requests',
            'cryptography',
            'pathlib'
        ]
        
        for lib in required_libs:
            try:
                __import__(lib.replace('-', '_'))
            except ImportError:
                print(f"📦 Installing {lib}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', lib], 
                             capture_output=True)
    
    def get_system_info(self):
        """Ambil informasi sistem Termux"""
        try:
            # Informasi dasar
            username = os.getenv('USER', 'termux')
            hostname = socket.gethostname()
            
            # Informasi RAM
            memory = psutil.virtual_memory()
            ram_total = round(memory.total / (1024**3), 2)
            ram_used = round(memory.used / (1024**3), 2)
            ram_free = round(memory.available / (1024**3), 2)
            
            # Informasi CPU
            cpu_info = platform.processor() or "ARM"
            cpu_cores = psutil.cpu_count()
            
            # Informasi OS
            os_info = platform.system()
            os_version = platform.release()
            kernel = platform.version()
            
            # IP Address
            try:
                ip_address = socket.gethostbyname(socket.gethostname())
            except:
                ip_address = "127.0.0.1"
            
            info = f"""
🤖 **TERMUX BOT CONTROLLER v3.0 BETA**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 **INFORMASI PENGGUNA**
├ Nama ID Termux: {username}@{hostname}
├ IP Jaringan: {ip_address}
└ Status: Online ✅

💾 **INFORMASI MEMORI**
├ Total RAM: {ram_total} GB
├ RAM Terpakai: {ram_used} GB
├ Sisa RAM: {ram_free} GB
└ Penggunaan: {round(memory.percent, 1)}%

⚙️ **INFORMASI SISTEM**
├ Jenis OS: {os_info}
├ Versi OS: {os_version}
├ Kernel: {kernel}
├ CPU: {cpu_info}
└ Core CPU: {cpu_cores}

👨‍💻 **INFORMASI DEVELOPER**
├ Developer: SerpentSecHunter
├ GitHub: https://github.com/SerpentSecHunter
├ Versi: 3.0 BETA
└ Rilis: Rabu, 30 Juli 2025

📋 **CARA PENGGUNAAN:**
Gunakan menu keyboard di bawah untuk mengakses fitur bot.
Semua perintah telah disediakan dalam bentuk tombol untuk kemudahan penggunaan.
            """
            return info
        except Exception as e:
            return f"❌ Error getting system info: {str(e)}"

    def get_installed_packages(self):
        """Lihat semua library yang terinstall"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                packages = result.stdout.split('\n')[2:]  # Skip header
                package_list = []
                for pkg in packages:
                    if pkg.strip():
                        parts = pkg.split()
                        if len(parts) >= 2:
                            package_list.append(f"📦 {parts[0]} - v{parts[1]}")
                
                if package_list:
                    return "📚 **LIBRARY TERINSTALL:**\n\n" + "\n".join(package_list)
                else:
                    return "📚 Tidak ada library yang terinstall"
            else:
                return f"❌ Error: {result.stderr}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def install_library(self, lib_name):
        """Install library baru"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', lib_name],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"✅ Library '{lib_name}' berhasil diinstall!"
            else:
                return f"❌ Gagal install '{lib_name}': {result.stderr}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def execute_command(self, command):
        """Kontrol penuh Termux"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=30)
            output = result.stdout or result.stderr or "Command executed"
            return f"```\n{output}\n```"
        except subprocess.TimeoutExpired:
            return "⏰ Command timeout (30 detik)"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def scan_media_files(self, path="/sdcard"):
        """Scan file media (Gallery Eyes)"""
        try:
            media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mkv', 
                              '.avi', '.mov', '.mp3', '.wav', '.flac'}
            media_files = []
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in media_extensions):
                        file_path = os.path.join(root, file)
                        size = os.path.getsize(file_path)
                        media_files.append({
                            'name': file,
                            'path': file_path,
                            'size': self.format_size(size),
                            'type': self.get_file_type(file)
                        })
            
            if media_files:
                result = "🖼️ **FILE MEDIA DITEMUKAN:**\n\n"
                for i, file in enumerate(media_files[:20], 1):  # Limit 20 files
                    result += f"{i}. {file['type']} **{file['name']}**\n"
                    result += f"   📁 {file['path']}\n"
                    result += f"   📊 {file['size']}\n\n"
                
                if len(media_files) > 20:
                    result += f"... dan {len(media_files) - 20} file lainnya"
                
                return result
            else:
                return "📁 Tidak ada file media ditemukan"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def lock_file(self, file_path, password):
        """Kunci file/folder penting"""
        try:
            if not os.path.exists(file_path):
                return "❌ File/folder tidak ditemukan!"
            
            # Generate key dari password
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000)
            fernet = Fernet(base64.urlsafe_b64encode(key[:32]))
            
            if os.path.isfile(file_path):
                # Lock file
                with open(file_path, 'rb') as f:
                    data = f.read()
                
                encrypted_data = fernet.encrypt(data)
                locked_path = file_path + '.locked'
                
                with open(locked_path, 'wb') as f:
                    f.write(encrypted_data)
                
                os.remove(file_path)
                locked_files[locked_path] = password
                
                return f"🔒 File berhasil dikunci: {locked_path}"
            else:
                # Lock folder (zip then encrypt)
                zip_path = file_path + '.zip'
                shutil.make_archive(file_path, 'zip', file_path)
                
                with open(zip_path, 'rb') as f:
                    data = f.read()
                
                encrypted_data = fernet.encrypt(data)
                locked_path = file_path + '.locked'
                
                with open(locked_path, 'wb') as f:
                    f.write(encrypted_data)
                
                os.remove(zip_path)
                shutil.rmtree(file_path)
                locked_files[locked_path] = password
                
                return f"🔒 Folder berhasil dikunci: {locked_path}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def unlock_file(self, locked_path, password):
        """Buka kunci file/folder"""
        try:
            if not os.path.exists(locked_path):
                return "❌ File terkunci tidak ditemukan!"
            
            # Generate key dari password
            key = hashlib.pbkdf2_hmac('sha256', password.encode(), b'salt', 100000)
            fernet = Fernet(base64.urlsafe_b64encode(key[:32]))
            
            with open(locked_path, 'rb') as f:
                encrypted_data = f.read()
            
            try:
                decrypted_data = fernet.decrypt(encrypted_data)
            except:
                return "❌ Password salah!"
            
            original_path = locked_path.replace('.locked', '')
            
            if locked_path.endswith('.locked') and not original_path.endswith('.zip'):
                # Unlock file
                with open(original_path, 'wb') as f:
                    f.write(decrypted_data)
            else:
                # Unlock folder
                zip_path = original_path + '.zip'
                with open(zip_path, 'wb') as f:
                    f.write(decrypted_data)
                
                shutil.unpack_archive(zip_path, original_path)
                os.remove(zip_path)
            
            os.remove(locked_path)
            if locked_path in locked_files:
                del locked_files[locked_path]
            
            return f"🔓 File/folder berhasil dibuka: {original_path}"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def check_packages(self):
        """Cek semua folder di storage"""
        try:
            result = "📁 **STRUKTUR PENYIMPANAN:**\n\n"
            
            # Internal Storage
            internal_path = "/data/data/com.termux/files/home"
            if os.path.exists(internal_path):
                result += "📱 **INTERNAL STORAGE:**\n"
                for item in os.listdir(internal_path):
                    item_path = os.path.join(internal_path, item)
                    if os.path.isdir(item_path):
                        size = self.get_folder_size(item_path)
                        result += f"├ 📁 {item} ({size})\n"
                    else:
                        size = self.format_size(os.path.getsize(item_path))
                        result += f"├ 📄 {item} ({size})\n"
            
            # SD Card (jika ada)
            sdcard_paths = ["/sdcard", "/storage/emulated/0"]
            for sdcard_path in sdcard_paths:
                if os.path.exists(sdcard_path) and os.path.ismount(sdcard_path):
                    result += f"\n💳 **SD CARD ({sdcard_path}):**\n"
                    try:
                        for item in os.listdir(sdcard_path)[:10]:  # Limit 10 items
                            item_path = os.path.join(sdcard_path, item)
                            if os.path.isdir(item_path):
                                size = self.get_folder_size(item_path)
                                result += f"├ 📁 {item} ({size})\n"
                            else:
                                size = self.format_size(os.path.getsize(item_path))
                                result += f"├ 📄 {item} ({size})\n"
                    except PermissionError:
                        result += "❌ Akses ditolak untuk SD Card\n"
                    break
            
            return result
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def remove_file(self, path):
        """Hapus file/folder"""
        try:
            if not os.path.exists(path):
                return "❌ File/folder tidak ditemukan!"
            
            if os.path.isfile(path):
                os.remove(path)
                return f"🗑️ File berhasil dihapus: {path}"
            else:
                shutil.rmtree(path)
                return f"🗑️ Folder berhasil dihapus: {path}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def copy_file(self, src, dst):
        """Copy file/folder"""
        try:
            if not os.path.exists(src):
                return "❌ File/folder sumber tidak ditemukan!"
            
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                return f"📋 File berhasil dicopy ke: {dst}"
            else:
                shutil.copytree(src, dst)
                return f"📋 Folder berhasil dicopy ke: {dst}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_wifi_info(self):
        """Informasi WiFi"""
        try:
            # Simulasi informasi WiFi (dalam environment Termux terbatas)
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True)
            
            info = "📶 **INFORMASI WIFI:**\n\n"
            info += f"Status: {'🟢 Terhubung' if 'wlan' in result.stdout else '🔴 Terputus'}\n"
            info += f"IP Address: {socket.gethostbyname(socket.gethostname())}\n"
            
            # Tambahan info jaringan
            try:
                result = subprocess.run(['ping', '-c', '1', 'google.com'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info += "🌐 Koneksi Internet: ✅ Aktif\n"
                else:
                    info += "🌐 Koneksi Internet: ❌ Tidak ada\n"
            except:
                info += "🌐 Koneksi Internet: ❓ Tidak diketahui\n"
            
            return info
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def plant_bot(self):
        """Tanam bot di Termux"""
        global bot_planted
        try:
            # Create service script
            service_script = '''#!/data/data/com.termux/files/usr/bin/bash
cd /data/data/com.termux/files/home
python termux_bot.py &
'''
            
            # Write to bash profile untuk auto start
            bashrc_path = os.path.expanduser('~/.bashrc')
            with open(bashrc_path, 'a') as f:
                f.write('\n# Auto start Termux Bot\n')
                f.write('cd ~ && python termux_bot.py &\n')
            
            bot_planted = True
            return "🌱 Bot berhasil ditanam! Bot akan auto-start setiap kali Termux dibuka."
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def vibrate_device(self):
        """Getarkan device"""
        try:
            # Termux API untuk vibrate
            result = subprocess.run(['termux-vibrate'], capture_output=True)
            if result.returncode == 0:
                return "📳 Device berhasil digetarkan!"
            else:
                return "❌ Fitur getar tidak tersedia (install termux-api)"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def toggle_flashlight(self):
        """Toggle senter"""
        global flashlight_enabled
        try:
            if flashlight_enabled:
                result = subprocess.run(['termux-torch', 'off'], capture_output=True)
                flashlight_enabled = False
                return "🔦 Senter dimatikan"
            else:
                result = subprocess.run(['termux-torch', 'on'], capture_output=True)
                flashlight_enabled = True
                return "🔦 Senter dinyalakan"
        except Exception as e:
            return f"❌ Error: {str(e)} (install termux-api)"

    # Utility functions
    def format_size(self, bytes):
        """Format ukuran file"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"

    def get_folder_size(self, path):
        """Hitung ukuran folder"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except:
                        continue
            return self.format_size(total_size)
        except:
            return "Unknown"

    def get_file_type(self, filename):
        """Tentukan tipe file"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return "🖼️"
        elif ext in ['.mp4', '.mkv', '.avi', '.mov']:
            return "🎥"
        elif ext in ['.mp3', '.wav', '.flac']:
            return "🎵"
        else:
            return "📄"

# Inisialisasi Controller
controller = TermuxController()

# Keyboard Markup
def get_main_keyboard():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("📦 Install Library", "📚 Lihat Library")
    keyboard.row("⚡ Kontrol Termux", "👁️ Gallery Eyes")
    keyboard.row("🔒 Kunci File", "🔓 Buka Kunci")
    keyboard.row("📁 Cek Package", "🗑️ Remove File")
    keyboard.row("📋 Copy File", "📶 WiFi Control")
    keyboard.row("📳 Getar Device", "🔦 Toggle Senter")
    keyboard.row("🌱 Tanam Bot", "ℹ️ Info System")
    return keyboard

# Handler pesan
@bot.message_handler(commands=['start'])
def start_handler(message):
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "❌ Unauthorized access!")
        return
    
    welcome_msg = controller.get_system_info()
    bot.send_message(CHAT_ID, welcome_msg, parse_mode='Markdown', 
                    reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def message_handler(message):
    if message.chat.id != CHAT_ID:
        return
    
    text = message.text
    
    if text == "📦 Install Library":
        msg = bot.send_message(CHAT_ID, "📦 Masukkan nama library yang ingin diinstall:")
        bot.register_next_step_handler(msg, install_lib_handler)
    
    elif text == "📚 Lihat Library":
        result = controller.get_installed_packages()
        bot.send_message(CHAT_ID, result, parse_mode='Markdown')
    
    elif text == "⚡ Kontrol Termux":
        msg = bot.send_message(CHAT_ID, "⚡ Masukkan perintah Termux:")
        bot.register_next_step_handler(msg, termux_command_handler)
    
    elif text == "👁️ Gallery Eyes":
        bot.send_message(CHAT_ID, "👁️ Scanning file media...")
        result = controller.scan_media_files()
        bot.send_message(CHAT_ID, result, parse_mode='Markdown')
    
    elif text == "🔒 Kunci File":
        msg = bot.send_message(CHAT_ID, "🔒 Masukkan path file/folder yang ingin dikunci:")
        bot.register_next_step_handler(msg, lock_file_handler)
    
    elif text == "🔓 Buka Kunci":
        msg = bot.send_message(CHAT_ID, "🔓 Masukkan path file terkunci (.locked):")
        bot.register_next_step_handler(msg, unlock_file_handler)
    
    elif text == "📁 Cek Package":
        result = controller.check_packages()
        bot.send_message(CHAT_ID, result, parse_mode='Markdown')
    
    elif text == "🗑️ Remove File":
        msg = bot.send_message(CHAT_ID, "🗑️ Masukkan path file/folder yang ingin dihapus:")
        bot.register_next_step_handler(msg, remove_file_handler)
    
    elif text == "📋 Copy File":
        msg = bot.send_message(CHAT_ID, "📋 Masukkan path sumber:")
        bot.register_next_step_handler(msg, copy_file_handler)
    
    elif text == "📶 WiFi Control":
        result = controller.get_wifi_info()
        bot.send_message(CHAT_ID, result, parse_mode='Markdown')
    
    elif text == "📳 Getar Device":
        result = controller.vibrate_device()
        bot.send_message(CHAT_ID, result)
    
    elif text == "🔦 Toggle Senter":
        result = controller.toggle_flashlight()
        bot.send_message(CHAT_ID, result)
    
    elif text == "🌱 Tanam Bot":
        result = controller.plant_bot()
        bot.send_message(CHAT_ID, result)
    
    elif text == "ℹ️ Info System":
        result = controller.get_system_info()
        bot.send_message(CHAT_ID, result, parse_mode='Markdown')

# Handler untuk step-by-step input
def install_lib_handler(message):
    lib_name = message.text.strip()
    bot.send_message(CHAT_ID, f"📦 Installing {lib_name}...")
    result = controller.install_library(lib_name)
    bot.send_message(CHAT_ID, result)

def termux_command_handler(message):
    command = message.text.strip()
    if command.lower() in ['rm -rf /', 'rm -rf ~', 'rm -rf *']:
        bot.send_message(CHAT_ID, "❌ Perintah berbahaya ditolak!")
        return
    
    bot.send_message(CHAT_ID, f"⚡ Executing: {command}")
    result = controller.execute_command(command)
    bot.send_message(CHAT_ID, result, parse_mode='Markdown')

def lock_file_handler(message):
    file_path = message.text.strip()
    msg = bot.send_message(CHAT_ID, "🔐 Masukkan password untuk kunci file:")
    bot.register_next_step_handler(msg, lambda m: lock_file_password_handler(m, file_path))

def lock_file_password_handler(message, file_path):
    password = message.text.strip()
    result = controller.lock_file(file_path, password)
    bot.send_message(CHAT_ID, result)

def unlock_file_handler(message):
    locked_path = message.text.strip()
    msg = bot.send_message(CHAT_ID, "🔐 Masukkan password:")
    bot.register_next_step_handler(msg, lambda m: unlock_file_password_handler(m, locked_path))

def unlock_file_password_handler(message, locked_path):
    password = message.text.strip()
    result = controller.unlock_file(locked_path, password)
    bot.send_message(CHAT_ID, result)

def remove_file_handler(message):
    file_path = message.text.strip()
    result = controller.remove_file(file_path)
    bot.send_message(CHAT_ID, result)

def copy_file_handler(message):
    src_path = message.text.strip()
    msg = bot.send_message(CHAT_ID, "📋 Masukkan path tujuan:")
    bot.register_next_step_handler(msg, lambda m: copy_file_dest_handler(m, src_path))

def copy_file_dest_handler(message, src_path):
    dst_path = message.text.strip()
    result = controller.copy_file(src_path, dst_path)
    bot.send_message(CHAT_ID, result)

# Background service untuk keep bot alive
def keep_alive():
    while True:
        try:
            time.sleep(300)  # 5 menit
            # Send heartbeat (optional)
        except:
            break

# Main function
def main():
    print("🚀 Starting Termux Bot...")
    print(f"Bot Token: {BOT_TOKEN[:10]}...")
    print(f"Chat ID: {CHAT_ID}")
    print("Bot is running...")
    
    # Start background service
    threading.Thread(target=keep_alive, daemon=True).start()
    
    # Start bot
    try:
        bot.send_message(CHAT_ID, "🚀 **Termux Bot Started!**\n\nBot siap digunakan!", 
                        parse_mode='Markdown', reply_markup=get_main_keyboard())
        bot.polling(none_stop=True, interval=1)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
        main()  # Restart bot

if __name__ == "__main__":
    # Validasi nama file
    if not sys.argv[0].endswith('termux_bot.py'):
        print("❌ Error: Script harus dinamai 'termux_bot.py'!")
        print("Script akan terhapus otomatis...")
        os.remove(sys.argv[0])
        sys.exit(1)
    
    main()
