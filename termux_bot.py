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
import base64
import hashlib
import re

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
bot_status = True
flashlight_status = False

class TermuxController:
    def __init__(self):
        self.install_required_libraries()
        
    def install_required_libraries(self):
        """Install library yang diperlukan secara otomatis"""
        required_libs = [
            'pyTelegramBotAPI',
            'python-dotenv', 
            'psutil',
            'requests'
        ]
        
        for lib in required_libs:
            try:
                __import__(lib.replace('-', '_'))
            except ImportError:
                print(f"📦 Installing {lib}...")
                subprocess.run([sys.executable, '-m', 'pip', 'install', lib], 
                             capture_output=True)
    
    def escape_markdown(self, text):
        """Escape markdown characters"""
        escape_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    def get_system_info(self):
        """Ambil informasi sistem Termux dari terminal"""
        try:
            info_parts = []
            
            # Header
            info_parts.append("🤖 *TERMUX BOT CONTROLLER v3\\.0 BETA*")
            info_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # Informasi Pengguna dari terminal
            info_parts.append("👤 *INFORMASI PENGGUNA*")
            
            # Username dari whoami
            try:
                username_result = subprocess.run(['whoami'], capture_output=True, text=True)
                username = username_result.stdout.strip() if username_result.returncode == 0 else "termux"
            except:
                username = "termux"
            
            # Hostname dari uname
            try:
                hostname_result = subprocess.run(['uname', '-n'], capture_output=True, text=True)
                hostname = hostname_result.stdout.strip() if hostname_result.returncode == 0 else "localhost"
            except:
                hostname = "localhost"
            
            # IP Address dari ip command
            try:
                ip_result = subprocess.run(['ip', 'route', 'get', '1.1.1.1'], capture_output=True, text=True)
                ip_line = ip_result.stdout.split('\n')[0]
                ip_address = ip_line.split('src ')[1].split()[0] if 'src ' in ip_line else "127.0.0.1"
            except:
                ip_address = "127.0.0.1"
            
            info_parts.append(f"├ Nama ID Termux: {self.escape_markdown(username + '@' + hostname)}")
            info_parts.append(f"├ IP Jaringan: {self.escape_markdown(ip_address)}")
            info_parts.append("└ Status: Online ✅")
            info_parts.append("")
            
            # Informasi Memori dari /proc/meminfo
            info_parts.append("💾 *INFORMASI MEMORI*")
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                
                mem_total = int(re.search(r'MemTotal:\s+(\d+)', meminfo).group(1)) * 1024
                mem_available = int(re.search(r'MemAvailable:\s+(\d+)', meminfo).group(1)) * 1024
                mem_used = mem_total - mem_available
                
                total_gb = round(mem_total / (1024**3), 2)
                used_gb = round(mem_used / (1024**3), 2)
                free_gb = round(mem_available / (1024**3), 2)
                usage_percent = round((mem_used / mem_total) * 100, 1)
                
                info_parts.append(f"├ Total RAM: {total_gb} GB")
                info_parts.append(f"├ RAM Terpakai: {used_gb} GB")
                info_parts.append(f"├ Sisa RAM: {free_gb} GB")
                info_parts.append(f"└ Penggunaan: {usage_percent}%")
            except:
                info_parts.append("├ Total RAM: N/A")
                info_parts.append("├ RAM Terpakai: N/A")
                info_parts.append("├ Sisa RAM: N/A")
                info_parts.append("└ Penggunaan: N/A")
            
            info_parts.append("")
            
            # Informasi Sistem dari uname
            info_parts.append("⚙️ *INFORMASI SISTEM*")
            try:
                # OS Info
                os_result = subprocess.run(['uname', '-s'], capture_output=True, text=True)
                os_name = os_result.stdout.strip() if os_result.returncode == 0 else "Linux"
                
                # OS Version
                version_result = subprocess.run(['uname', '-r'], capture_output=True, text=True)
                os_version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"
                
                # Kernel
                kernel_result = subprocess.run(['uname', '-v'], capture_output=True, text=True)
                kernel = kernel_result.stdout.strip() if kernel_result.returncode == 0 else "Unknown"
                
                # Architecture
                arch_result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
                architecture = arch_result.stdout.strip() if arch_result.returncode == 0 else "Unknown"
                
                # CPU Info
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                    cpu_cores = cpuinfo.count('processor')
                    cpu_model_match = re.search(r'model name\s*:\s*(.+)', cpuinfo)
                    cpu_model = cpu_model_match.group(1).strip() if cpu_model_match else architecture
                except:
                    cpu_cores = 1
                    cpu_model = architecture
                
                info_parts.append(f"├ Jenis OS: {self.escape_markdown(os_name)}")
                info_parts.append(f"├ Versi OS: {self.escape_markdown(os_version)}")
                info_parts.append(f"├ Kernel: {self.escape_markdown(kernel[:50])}")
                info_parts.append(f"├ CPU: {self.escape_markdown(cpu_model[:30])}")
                info_parts.append(f"└ Core CPU: {cpu_cores}")
            except:
                info_parts.append("├ Jenis OS: Linux")
                info_parts.append("├ Versi OS: Unknown")
                info_parts.append("├ Kernel: Unknown")
                info_parts.append("├ CPU: Unknown")
                info_parts.append("└ Core CPU: Unknown")
            
            info_parts.append("")
            info_parts.append("👨‍💻 *INFORMASI DEVELOPER*")
            info_parts.append("├ Developer: SerpentSecHunter")
            info_parts.append("├ GitHub: https://github\\.com/SerpentSecHunter")
            info_parts.append("├ Versi: 3\\.0 BETA")
            info_parts.append("└ Rilis: Rabu, 30 Juli 2025")
            info_parts.append("")
            info_parts.append("📋 *CARA PENGGUNAAN:*")
            info_parts.append("Gunakan perintah berikut:")
            info_parts.append("• /help \\- Bantuan")
            info_parts.append("• /info \\- Info sistem")
            info_parts.append("• /termux \\<command\\> \\- Jalankan perintah")
            info_parts.append("• /ai \\<question\\> \\- Tanya AI")
            info_parts.append("• /clear \\- Hapus pesan")
            info_parts.append("• /on, /off \\- Nyala/mati bot")
            
            return "\n".join(info_parts)
        except Exception as e:
            return f"❌ Error getting system info: {str(e)}"

    def get_installed_packages(self):
        """Lihat semua library yang terinstall"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')[2:]  # Skip header
                packages = []
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            packages.append(f"📦 {parts[0]} \\- v{parts[1]}")
                
                if packages:
                    return "📚 *LIBRARY TERINSTALL:*\n\n" + "\n".join(packages[:20])
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
            # Blacklist perintah berbahaya
            dangerous_commands = ['rm -rf /', 'rm -rf ~', 'rm -rf *', 'format', 'dd if=']
            if any(cmd in command.lower() for cmd in dangerous_commands):
                return "❌ Perintah berbahaya ditolak!"
            
            result = subprocess.run(command, shell=True, capture_output=True, 
                                  text=True, timeout=30, cwd=os.path.expanduser('~'))
            
            output = result.stdout or result.stderr or "Command executed successfully"
            
            # Batasi output untuk menghindari error Telegram
            if len(output) > 3000:
                output = output[:3000] + "\n... (output dipotong)"
            
            return f"```\n{output}\n```"
        except subprocess.TimeoutExpired:
            return "⏰ Command timeout (30 detik)"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def scan_media_files(self, path="/storage/emulated/0"):
        """Scan file media (Gallery Eyes)"""
        try:
            media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mkv', 
                              '.avi', '.mov', '.mp3', '.wav', '.flac', '.pdf'}
            media_files = []
            
            # Scan multiple paths
            scan_paths = [path, "/sdcard", os.path.expanduser("~")]
            
            for scan_path in scan_paths:
                if os.path.exists(scan_path):
                    try:
                        for root, dirs, files in os.walk(scan_path):
                            for file in files:
                                if any(file.lower().endswith(ext) for ext in media_extensions):
                                    file_path = os.path.join(root, file)
                                    try:
                                        size = os.path.getsize(file_path)
                                        media_files.append({
                                            'name': file,
                                            'path': file_path,
                                            'size': self.format_size(size),
                                            'type': self.get_file_type(file)
                                        })
                                    except:
                                        continue
                            
                            # Limit untuk performa
                            if len(media_files) >= 50:
                                break
                    except PermissionError:
                        continue
            
            if media_files:
                result_parts = ["🖼️ *FILE MEDIA DITEMUKAN:*\n"]
                for i, file in enumerate(media_files[:15], 1):  # Limit 15 files
                    name = self.escape_markdown(file['name'][:30])
                    path = self.escape_markdown(file['path'][:50])
                    result_parts.append(f"{i}\\. {file['type']} *{name}*")
                    result_parts.append(f"   📁 {path}")
                    result_parts.append(f"   📊 {file['size']}\n")
                
                if len(media_files) > 15:
                    result_parts.append(f"\\.\\.\\. dan {len(media_files) - 15} file lainnya")
                
                return "\n".join(result_parts)
            else:
                return "📁 Tidak ada file media ditemukan"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def get_wifi_info(self):
        """Informasi WiFi dari terminal"""
        try:
            info_parts = ["📶 *INFORMASI WIFI:*\n"]
            
            # Status koneksi dari ping
            try:
                ping_result = subprocess.run(['ping', '-c', '1', '-W', '3', '8.8.8.8'], 
                                           capture_output=True, text=True)
                if ping_result.returncode == 0:
                    info_parts.append("Status: 🟢 Terhubung")
                    info_parts.append("🌐 Koneksi Internet: ✅ Aktif")
                else:
                    info_parts.append("Status: 🔴 Terputus")
                    info_parts.append("🌐 Koneksi Internet: ❌ Tidak ada")
            except:
                info_parts.append("Status: ❓ Tidak diketahui")
            
            # IP Address dari ip command
            try:
                ip_result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True)
                if ip_result.returncode == 0:
                    lines = ip_result.stdout.split('\n')
                    for line in lines:
                        if 'inet ' in line and '127.0.0.1' not in line:
                            ip = line.split('inet ')[1].split('/')[0].strip()
                            info_parts.append(f"📍 IP Address: {ip}")
                            break
            except:
                info_parts.append("📍 IP Address: Unknown")
            
            # Gateway dari ip route
            try:
                route_result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                            capture_output=True, text=True)
                if route_result.returncode == 0 and route_result.stdout:
                    gateway = route_result.stdout.split('via ')[1].split()[0]
                    info_parts.append(f"🚪 Gateway: {gateway}")
            except:
                info_parts.append("🚪 Gateway: Unknown")
            
            # DNS dari resolv.conf
            try:
                with open('/etc/resolv.conf', 'r') as f:
                    resolv = f.read()
                dns_servers = re.findall(r'nameserver\s+(\S+)', resolv)
                if dns_servers:
                    info_parts.append(f"🔍 DNS: {', '.join(dns_servers[:2])}")
            except:
                info_parts.append("🔍 DNS: Unknown")
            
            return "\n".join(info_parts)
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def vibrate_device(self):
        """Getarkan device menggunakan Termux API"""
        try:
            # Cek apakah termux-api tersedia
            result = subprocess.run(['which', 'termux-vibrate'], capture_output=True)
            if result.returncode != 0:
                # Coba install termux-api
                install_result = subprocess.run(['pkg', 'install', '-y', 'termux-api'], 
                                              capture_output=True)
                if install_result.returncode != 0:
                    return "❌ Termux API tidak tersedia. Install dengan: pkg install termux-api"
            
            # Jalankan vibrate
            vibrate_result = subprocess.run(['termux-vibrate', '-d', '500'], 
                                          capture_output=True, timeout=5)
            if vibrate_result.returncode == 0:
                return "📳 Device berhasil digetarkan!"
            else:
                return "❌ Gagal menggetarkan device. Pastikan Termux:API terinstall dari F-Droid"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def toggle_flashlight(self):
        """Toggle senter menggunakan Termux API"""
        global flashlight_status
        try:
            # Cek termux-api
            result = subprocess.run(['which', 'termux-torch'], capture_output=True)
            if result.returncode != 0:
                return "❌ Termux API tidak tersedia. Install dengan: pkg install termux-api"
            
            if flashlight_status:
                torch_result = subprocess.run(['termux-torch', 'off'], 
                                            capture_output=True, timeout=5)
                if torch_result.returncode == 0:
                    flashlight_status = False
                    return "🔦 Senter dimatikan"
                else:
                    return "❌ Gagal mematikan senter"
            else:
                torch_result = subprocess.run(['termux-torch', 'on'], 
                                            capture_output=True, timeout=5)
                if torch_result.returncode == 0:
                    flashlight_status = True
                    return "🔦 Senter dinyalakan"
                else:
                    return "❌ Gagal menyalakan senter"
        except Exception as e:
            flashlight_status = False
            return f"❌ Error: {str(e)}"

    def ask_ai(self, question):
        """Tanya AI menggunakan Gemini API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"Jawab dalam bahasa Indonesia: {question}"
                    }]
                }]
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    answer = result['candidates'][0]['content']['parts'][0]['text']
                    # Escape markdown untuk Telegram
                    answer = self.escape_markdown(answer)
                    return f"🤖 *AI Assistant:*\n\n{answer}"
                else:
                    return "❌ AI tidak memberikan jawaban"
            else:
                return f"❌ Error API: {response.status_code}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def clear_chat(self, message_id):
        """Hapus pesan chat"""
        try:
            # Hapus pesan user
            bot.delete_message(CHAT_ID, message_id)
            return "🧹 Pesan berhasil dihapus"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def lock_file(self, file_path, password):
        """Kunci file/folder dengan password"""
        try:
            if not os.path.exists(file_path):
                return "❌ File/folder tidak ditemukan!"
            
            # Simple encryption using base64 (untuk demo)
            encoded_password = base64.b64encode(password.encode()).decode()
            
            if os.path.isfile(file_path):
                # Rename file
                locked_path = file_path + '.locked'
                os.rename(file_path, locked_path)
                locked_files[locked_path] = encoded_password
                return f"🔒 File berhasil dikunci: {os.path.basename(locked_path)}"
            else:
                # Zip folder then rename
                zip_path = file_path + '.zip'
                shutil.make_archive(file_path, 'zip', file_path)
                locked_path = file_path + '.locked'
                os.rename(zip_path, locked_path)
                shutil.rmtree(file_path)
                locked_files[locked_path] = encoded_password
                return f"🔒 Folder berhasil dikunci: {os.path.basename(locked_path)}"
                
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def unlock_file(self, locked_path, password):
        """Buka kunci file/folder"""
        try:
            if not os.path.exists(locked_path):
                return "❌ File terkunci tidak ditemukan!"
            
            encoded_password = base64.b64encode(password.encode()).decode()
            
            if locked_path in locked_files:
                if locked_files[locked_path] != encoded_password:
                    return "❌ Password salah!"
            
            original_path = locked_path.replace('.locked', '')
            
            if locked_path.endswith('.locked'):
                if original_path.endswith('.zip'):
                    # Unlock folder
                    zip_path = original_path
                    os.rename(locked_path, zip_path)
                    folder_path = zip_path.replace('.zip', '')
                    shutil.unpack_archive(zip_path, folder_path)
                    os.remove(zip_path)
                    if locked_path in locked_files:
                        del locked_files[locked_path]
                    return f"🔓 Folder berhasil dibuka: {os.path.basename(folder_path)}"
                else:
                    # Unlock file
                    os.rename(locked_path, original_path)
                    if locked_path in locked_files:
                        del locked_files[locked_path]
                    return f"🔓 File berhasil dibuka: {os.path.basename(original_path)}"
            
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def check_packages(self):
        """Cek struktur penyimpanan"""
        try:
            result_parts = ["📁 *STRUKTUR PENYIMPANAN:*\n"]
            
            # Home directory
            home_path = os.path.expanduser("~")
            if os.path.exists(home_path):
                result_parts.append("🏠 *HOME DIRECTORY:*")
                try:
                    items = os.listdir(home_path)[:10]  # Limit 10 items
                    for item in items:
                        item_path = os.path.join(home_path, item)
                        if os.path.isdir(item_path):
                            size = self.get_folder_size(item_path)
                            result_parts.append(f"├ 📁 {self.escape_markdown(item)} ({size})")
                        else:
                            try:
                                size = self.format_size(os.path.getsize(item_path))
                                result_parts.append(f"├ 📄 {self.escape_markdown(item)} ({size})")
                            except:
                                result_parts.append(f"├ 📄 {self.escape_markdown(item)} (N/A)")
                except PermissionError:
                    result_parts.append("❌ Akses ditolak")
            
            result_parts.append("")
            
            # Storage paths
            storage_paths = ["/storage/emulated/0", "/sdcard"]
            for storage_path in storage_paths:
                if os.path.exists(storage_path) and os.access(storage_path, os.R_OK):
                    result_parts.append(f"💾 *STORAGE ({storage_path}):*")
                    try:
                        items = os.listdir(storage_path)[:8]  # Limit 8 items
                        for item in items:
                            item_path = os.path.join(storage_path, item)
                            if os.path.isdir(item_path):
                                result_parts.append(f"├ 📁 {self.escape_markdown(item)}")
                            else:
                                result_parts.append(f"├ 📄 {self.escape_markdown(item)}")
                    except PermissionError:
                        result_parts.append("❌ Akses ditolak")
                    break
            
            return "\n".join(result_parts)
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def remove_file(self, path):
        """Hapus file/folder"""
        try:
            if not os.path.exists(path):
                return "❌ File/folder tidak ditemukan!"
            
            if os.path.isfile(path):
                os.remove(path)
                return f"🗑️ File berhasil dihapus: {os.path.basename(path)}"
            else:
                shutil.rmtree(path)
                return f"🗑️ Folder berhasil dihapus: {os.path.basename(path)}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def copy_file(self, src, dst):
        """Copy file/folder"""
        try:
            if not os.path.exists(src):
                return "❌ File/folder sumber tidak ditemukan!"
            
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                return f"📋 File berhasil dicopy ke: {os.path.basename(dst)}"
            else:
                if os.path.exists(dst):
                    dst = os.path.join(dst, os.path.basename(src))
                shutil.copytree(src, dst)
                return f"📋 Folder berhasil dicopy ke: {os.path.basename(dst)}"
        except Exception as e:
            return f"❌ Error: {str(e)}"

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
            count = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    count += 1
                    if count > 100:  # Limit untuk performa
                        return "Large"
                    try:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                    except:
                        continue
            return self.format_size(total_size)
        except:
            return "Unknown"

    def get_file_type(self, filename):
        """Tentukan tipe file"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            return "🖼️"
        elif ext in ['.mp4', '.mkv', '.avi', '.mov', '.wmv']:
            return "🎥"
        elif ext in ['.mp3', '.wav', '.flac', '.aac']:
            return "🎵"
        elif ext in ['.pdf', '.doc', '.docx']:
            return "📄"
        elif ext in ['.zip', '.rar', '.tar', '.gz']:
            return "📦"
        else:
            return "📋"

# Inisialisasi Controller
controller = TermuxController()

# Command handlers
@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    if message.chat.id != CHAT_ID:
        bot.reply_to(message, "❌ Unauthorized access!")
        return
    
    help_text = """
🤖 *TERMUX BOT CONTROLLER v3\\.0 BETA*

*PERINTAH TERSEDIA:*

📋 *INFORMASI & KONTROL:*
• `/start` atau `/help` \\- Bantuan
• `/info` \\- Informasi sistem lengkap
• `/on` \\- Nyalakan bot
• `/off` \\- Matikan bot
• `/clear` \\- Hapus pesan

⚡ *KONTROL TERMUX:*
• `/termux <command>` \\- Jalankan perintah
• `/install <library>` \\- Install library Python
• `/packages` \\- Lihat library terinstall
• `/storage` \\- Cek struktur penyimpanan

🔒 *FILE MANAGEMENT:*
• `/scan` \\- Scan file media \\(Gallery Eyes\\)
• `/lock <path> <password>` \\- Kunci file/folder
• `/unlock <path> <password>` \\- Buka kunci
• `/remove <path>` \\- Hapus file/folder
• `/copy <src> <dst>` \\- Copy file/folder

📱 *DEVICE CONTROL:*
• `/wifi` \\- Info WiFi dan jaringan
• `/vibrate` \\- Getarkan device
• `/flashlight` \\- Toggle senter
• `/ai <question>` \\- Tanya AI

*CONTOH PENGGUNAAN:*
• `/termux ls \\-la`
• `/install requests`
• `/lock /sdcard/secret\\.txt mypass123`
• `/ai Jelaskan tentang Python`

*Developer:* SerpentSecHunter
*GitHub:* https://github\\.com/SerpentSecHunter
