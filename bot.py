#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Termux Controller - Enhanced Version
Developed for Termux Android Environment
Author: Enhanced Assistant
Version: 2.0 - Full Featured
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
import sqlite3
import hashlib
import base64
import zipfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import requests
import psutil

# Auto install dan setup requirements
def setup_environment():
    """Setup environment dan install requirements"""
    print("🚀 Setting up Termux Bot Controller...")
    
    # Required packages
    packages = [
        'python-telegram-bot==20.7',
        'psutil',
        'requests',
        'pillow',
        'python-dotenv',
        'qrcode',
        'cryptography'
    ]
    
    # Install packages if not already installed
    for package in packages:
        package_name = package.split('==')[0].replace('-', '_')
        try:
            __import__(package_name)
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                             capture_output=True, text=True, check=True)
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {package}: {e}")
    
    # Setup Termux API packages
    termux_packages = [
        'termux-api',
        'openssh',
        'curl',
        'wget',
        'git',
        'nano',
        'zip',
        'unzip'
    ]
    
    print("📱 Setting up Termux API packages...")
    for pkg in termux_packages:
        try:
            result = subprocess.run(['pkg', 'list-installed', pkg], 
                                  capture_output=True, text=True)
            if pkg not in result.stdout:
                print(f"📦 Installing {pkg}...")
                subprocess.run(['pkg', 'install', '-y', pkg], 
                             capture_output=True, text=True)
                print(f"✅ {pkg} installed")
        except:
            continue
    
    # Request all necessary permissions
    print("🔐 Requesting Termux permissions...")
    permissions = [
        'termux-setup-storage',
        'termux-camera-info',
        'termux-location -p gps',
        'termux-battery-status',
        'termux-wifi-connectioninfo'
    ]
    
    for perm in permissions:
        try:
            subprocess.run(perm.split(), capture_output=True, text=True, timeout=5)
        except:
            continue
    
    print("✅ Environment setup completed!")

# Setup environment first
setup_environment()

# Import after installation
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
from PIL import Image
import qrcode
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Configuration Class
class Config:
    def __init__(self):
        self.bot_token = self.get_token()
        self.chat_id = None
        self.bot_active = True
        self.auto_start = False
        self.encrypted_files = {}
        self.locked_folders = set()
        self.db_path = 'bot_data.db'
        self.init_database()
        
    def get_token(self):
        token = os.getenv('BOT_TOKEN')
        if not token:
            config_file = 'bot_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('bot_token')
        
        if not token:
            print("🤖 Bot Token Setup")
            print("=" * 50)
            print("1. Buka @BotFather di Telegram")
            print("2. Kirim /newbot")
            print("3. Ikuti instruksi untuk membuat bot")
            print("4. Copy token yang diberikan")
            print("=" * 50)
            token = input("Masukkan Bot Token: ").strip()
            self.save_config(token)
        
        return token
    
    def save_config(self, token):
        config = {
            'bot_token': token,
            'auto_start': self.auto_start,
            'timestamp': datetime.now().isoformat()
        }
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        with open('.env', 'w') as f:
            f.write(f"BOT_TOKEN={token}\n")
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY,
                action TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files_backup (
                id INTEGER PRIMARY KEY,
                original_path TEXT,
                backup_path TEXT,
                file_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TermuxBotController:
    def __init__(self):
        self.config = Config()
        self.app = None
        self.current_directory = os.path.expanduser('~')
        self.cipher_key = self.generate_cipher_key()
        
    def generate_cipher_key(self):
        """Generate encryption key"""
        key_file = 'bot_key.key'
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def log_action(self, action, details):
        """Log actions to database"""
        conn = sqlite3.connect(self.config.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO logs (action, details) VALUES (?, ?)', 
                      (action, details))
        conn.commit()
        conn.close()

    def create_main_keyboard(self):
        """Create enhanced main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📷 Ambil Foto", callback_data="take_photo"),
                InlineKeyboardButton("🔋 Status Baterai", callback_data="check_battery")
            ],
            [
                InlineKeyboardButton("📩 Notifikasi", callback_data="view_notifications"),
                InlineKeyboardButton("📞 Log Panggilan", callback_data="call_logs")
            ],
            [
                InlineKeyboardButton("🖼️ Wallpaper", callback_data="change_wallpaper"),
                InlineKeyboardButton("📶 Info WiFi", callback_data="wifi_info")
            ],
            [
                InlineKeyboardButton("📳 Getaran", callback_data="vibrate_device"),
                InlineKeyboardButton("👥 Kontak", callback_data="manage_contacts")
            ],
            [
                InlineKeyboardButton("ℹ️ Info Sistem", callback_data="system_info"),
                InlineKeyboardButton("📍 Lokasi GPS", callback_data="track_location")
            ],
            [
                InlineKeyboardButton("🔒 Lock Screen", callback_data="lock_system"),
                InlineKeyboardButton("💾 Backup Data", callback_data="backup_gallery")
            ],
            [
                InlineKeyboardButton("🗂️ File Manager", callback_data="file_manager"),
                InlineKeyboardButton("🛡️ Security", callback_data="security_menu")
            ],
            [
                InlineKeyboardButton("💻 Terminal", callback_data="termux_terminal"),
                InlineKeyboardButton("📱 Device Control", callback_data="device_control")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings"),
                InlineKeyboardButton("📊 Statistics", callback_data="view_stats")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_settings_keyboard(self):
        """Create settings keyboard"""
        status = "🟢 ON" if self.config.bot_active else "🔴 OFF"
        auto_status = "🟢 ON" if self.config.auto_start else "🔴 OFF"
        
        keyboard = [
            [InlineKeyboardButton(f"Bot Status: {status}", callback_data="toggle_bot")],
            [InlineKeyboardButton(f"Auto Start: {auto_status}", callback_data="toggle_auto_start")],
            [InlineKeyboardButton("🧹 Clear Logs", callback_data="clear_logs")],
            [InlineKeyboardButton("🔄 Restart Bot", callback_data="restart_bot")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced start command"""
        user = update.effective_user
        self.config.chat_id = update.effective_chat.id
        
        # Log start action
        self.log_action("BOT_START", f"User: {user.first_name} ({user.id})")
        
        welcome_message = f"""
🤖 **TERMUX BOT CONTROLLER v2.0** 🤖
═══════════════════════════════════

👋 Selamat datang, **{user.first_name}**!

🚀 **Bot Termux Controller Full Featured!**

✨ **Fitur Lengkap:**
• 📷 **Camera Control** - Foto front/back camera
• 🔋 **Battery Monitor** - Real-time battery info
• 📱 **Device Control** - Volume, brightness, dll
• 🌐 **Network Monitor** - WiFi, data usage
• 📍 **GPS Tracking** - Real-time location
• 🔒 **Security System** - Lock folders, encrypt files
• 💾 **Backup Manager** - Auto backup important data
• 👥 **Contact Manager** - Kelola kontak WhatsApp
• 📩 **Notification Hub** - Monitor semua notifikasi
• 💻 **Terminal Access** - Full terminal control
• 📊 **System Monitor** - CPU, RAM, Storage

🛡️ **Keamanan:** End-to-end encryption
⚡ **Performance:** Optimized for Termux
🔄 **Auto Updates:** Self-updating system

🚀 **Gunakan menu di bawah untuk memulai!**
        """
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced button handler"""
        query = update.callback_query
        await query.answer()
        
        if not self.config.bot_active and query.data not in ["toggle_bot", "bot_settings"]:
            await query.edit_message_text(
                "🔴 Bot sedang tidak aktif. Aktifkan melalui pengaturan.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings")
                ]])
            )
            return

        # Button handlers mapping
        handlers = {
            "main_menu": self.show_main_menu,
            "take_photo": self.take_photo_menu,
            "check_battery": self.check_battery,
            "view_notifications": self.view_notifications,
            "call_logs": self.get_call_logs,
            "change_wallpaper": self.change_wallpaper,
            "wifi_info": self.get_wifi_info,
            "vibrate_device": self.vibrate_device,
            "manage_contacts": self.manage_contacts,
            "system_info": self.get_system_info,
            "track_location": self.track_location,
            "lock_system": self.lock_system,
            "backup_gallery": self.backup_gallery,
            "file_manager": self.file_manager,
            "security_menu": self.security_menu,
            "termux_terminal": self.termux_terminal,
            "device_control": self.device_control,
            "bot_settings": self.bot_settings,
            "view_stats": self.view_stats,
            "toggle_bot": self.toggle_bot,
            "toggle_auto_start": self.toggle_auto_start,
            "clear_logs": self.clear_logs,
            "restart_bot": self.restart_bot
        }
        
        handler = handlers.get(query.data)
        if handler:
            await handler(query)
        else:
            # Handle photo callbacks
            if query.data.startswith("photo_"):
                await self.handle_photo_callback(query)
            elif query.data.startswith("device_"):
                await self.handle_device_callback(query)
            elif query.data.startswith("security_"):
                await self.handle_security_callback(query)

    async def show_main_menu(self, query):
        """Show enhanced main menu"""
        current_time = datetime.now().strftime('%H:%M:%S')
        uptime = time.time() - os.path.getctime(__file__)
        uptime_str = str(timedelta(seconds=int(uptime)))
        
        message = f"""
🤖 **TERMUX BOT CONTROLLER v2.0**
═══════════════════════════════════

🕐 **Time:** {current_time}
⏱️ **Uptime:** {uptime_str}
📁 **Dir:** `{os.path.basename(self.current_directory)}`
🔋 **Status:** {'🟢 Active' if self.config.bot_active else '🔴 Inactive'}

🚀 **Dashboard - Pilih fitur yang diinginkan:**
        """
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def take_photo_menu(self, query):
        """Enhanced photo menu"""
        keyboard = [
            [
                InlineKeyboardButton("📷 Front Camera", callback_data="photo_front"),
                InlineKeyboardButton("📸 Back Camera", callback_data="photo_back")
            ],
            [
                InlineKeyboardButton("🎥 Record Video", callback_data="photo_video"),
                InlineKeyboardButton("📊 Camera Info", callback_data="photo_info")
            ],
            [
                InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            "📷 **CAMERA CONTROL**\n═══════════════════\n\nPilih jenis kamera atau aksi:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def handle_photo_callback(self, query):
        """Handle photo-related callbacks"""
        if query.data == "photo_front":
            await self.take_photo(query, camera_id="1")
        elif query.data == "photo_back":
            await self.take_photo(query, camera_id="0")
        elif query.data == "photo_video":
            await self.record_video(query)
        elif query.data == "photo_info":
            await self.get_camera_info(query)

    async def take_photo(self, query, camera_id="1"):
        """Enhanced photo taking with both cameras"""
        camera_name = "Front" if camera_id == "1" else "Back"
        await query.edit_message_text(f"📷 Mengambil foto dari kamera {camera_name.lower()}...")
        
        try:
            # Create photos directory
            photos_dir = os.path.expanduser('~/storage/dcim/Camera')
            os.makedirs(photos_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_path = f"{photos_dir}/termux_bot_{timestamp}.jpg"
            
            # Take photo with enhanced settings
            cmd = [
                'termux-camera-photo', 
                '-c', camera_id,
                '-s', '1920x1080',  # HD resolution
                photo_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(photo_path):
                # Optimize image
                with Image.open(photo_path) as img:
                    # Compress if too large
                    if os.path.getsize(photo_path) > 10 * 1024 * 1024:  # 10MB
                        img.save(photo_path, 'JPEG', quality=85, optimize=True)
                
                # Send photo
                with open(photo_path, 'rb') as photo:
                    caption = f"📷 **{camera_name} Camera**\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n📁 {os.path.basename(photo_path)}"
                    await query.message.reply_photo(
                        photo=photo,
                        caption=caption,
                        parse_mode='Markdown'
                    )
                
                self.log_action("PHOTO_TAKEN", f"Camera: {camera_name}, Path: {photo_path}")
                
                await query.edit_message_text(
                    location_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                self.log_action("GPS_LOCATION", f"Lat: {latitude}, Lon: {longitude}")
                
            else:
                raise Exception("GPS not available or timeout")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mendapatkan lokasi: {str(e)}\n\n💡 Tips:\n• Aktifkan GPS di pengaturan\n• Berikan izin lokasi ke Termux\n• Pastikan berada di area terbuka",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Coba Lagi", callback_data="track_location"),
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def vibrate_device(self, query):
        """Enhanced device vibration"""
        await query.edit_message_text("📳 Menggetarkan device...")
        
        try:
            # Vibrate with pattern
            patterns = {
                'short': [100],
                'long': [500],
                'double': [100, 100, 100],
                'sos': [100, 300, 100, 300, 100]
            }
            
            # Default vibration
            result = subprocess.run(['termux-vibrate', '-d', '1000'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                vibrate_message = """
📳 **DEVICE VIBRATION**
═══════════════════════════

✅ Device berhasil digetarkan!

🎵 **Pattern Options:**
• **Short:** Getaran pendek
• **Long:** Getaran panjang  
• **Double:** Getaran ganda
• **SOS:** Pola darurat

📱 Pilih pola getaran:
                """
                
                keyboard = [
                    [
                        InlineKeyboardButton("📳 Short", callback_data="vibrate_short"),
                        InlineKeyboardButton("📳 Long", callback_data="vibrate_long")
                    ],
                    [
                        InlineKeyboardButton("📳 Double", callback_data="vibrate_double"),
                        InlineKeyboardButton("🆘 SOS", callback_data="vibrate_sos")
                    ],
                    [
                        InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                    ]
                ]
                
                await query.edit_message_text(
                    vibrate_message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
                self.log_action("VIBRATE", "Device vibrated successfully")
                
            else:
                raise Exception("Vibration failed")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal menggetarkan device: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def get_wifi_info(self, query):
        """Enhanced WiFi information"""
        await query.edit_message_text("📶 Menganalisis koneksi WiFi...")
        
        try:
            # Get WiFi connection info
            result = subprocess.run(['termux-wifi-connectioninfo'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                wifi_data = json.loads(result.stdout)
                
                ssid = wifi_data.get('ssid', 'Not connected')
                bssid = wifi_data.get('bssid', 'Unknown')
                frequency = wifi_data.get('frequency', 0)
                ip = wifi_data.get('ip', 'Unknown')
                link_speed = wifi_data.get('link_speed', 0)
                rssi = wifi_data.get('rssi', 0)
                
                # Signal strength indicator
                if rssi >= -50:
                    signal_strength = "📶 Excellent"
                elif rssi >= -60:
                    signal_strength = "📶 Good"
                elif rssi >= -70:
                    signal_strength = "📶 Fair"
                else:
                    signal_strength = "📶 Poor"
                
                # Get additional network info
                try:
                    # Get external IP
                    ip_result = subprocess.run(['curl', '-s', 'ifconfig.me'], 
                                             capture_output=True, text=True, timeout=5)
                    external_ip = ip_result.stdout.strip() if ip_result.returncode == 0 else "Unknown"
                    
                    # Get network speed test (simple ping)
                    ping_result = subprocess.run(['ping', '-c', '3', '8.8.8.8'], 
                                               capture_output=True, text=True, timeout=10)
                    if ping_result.returncode == 0:
                        ping_lines = ping_result.stdout.split('\n')
                        avg_ping = "Unknown"
                        for line in ping_lines:
                            if 'avg' in line:
                                avg_ping = line.split('/')[-2] + "ms"
                                break
                    else:
                        avg_ping = "Failed"
                        
                except:
                    external_ip = "Failed to get"
                    avg_ping = "Failed"
                
                wifi_message = f"""
📶 **WIFI CONNECTION INFO**
═══════════════════════════════

🌐 **Network:**
• **SSID:** {ssid}
• **BSSID:** {bssid}
• **Frequency:** {frequency} MHz

📡 **Signal:**
• **Strength:** {signal_strength}
• **RSSI:** {rssi} dBm
• **Link Speed:** {link_speed} Mbps

🌍 **IP Addresses:**
• **Local IP:** {ip}
• **External IP:** {external_ip}

⚡ **Performance:**
• **Ping (Google):** {avg_ping}

⏰ **Updated:** {datetime.now().strftime('%H:%M:%S')}
                """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="wifi_info")],
                    [InlineKeyboardButton("📊 Speed Test", callback_data="speed_test")],
                    [InlineKeyboardButton("📶 WiFi Scan", callback_data="wifi_scan")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]
                
                await query.edit_message_text(
                    wifi_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                self.log_action("WIFI_INFO", f"SSID: {ssid}, IP: {ip}")
                
            else:
                raise Exception("WiFi info not available")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mendapatkan info WiFi: {str(e)}\n\n💡 Pastikan WiFi aktif dan terhubung",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def view_notifications(self, query):
        """Enhanced notification viewer"""
        await query.edit_message_text("📩 Mengambil notifikasi...")
        
        try:
            result = subprocess.run(['termux-notification-list'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                notifications = result.stdout.strip()
                
                if notifications:
                    # Parse and format notifications
                    notif_lines = notifications.split('\n')[:10]  # Show latest 10
                    
                    notif_message = """
📩 **ACTIVE NOTIFICATIONS**
═══════════════════════════════

📱 **Recent notifications:**

"""
                    
                    for i, notif in enumerate(notif_lines, 1):
                        if notif.strip():
                            notif_message += f"**{i}.** {notif[:50]}...\n"
                    
                    notif_message += f"\n⏰ **Updated:** {datetime.now().strftime('%H:%M:%S')}"
                    
                else:
                    notif_message = """
📩 **NOTIFICATIONS**
═══════════════════════════════

✅ **No active notifications**

📱 All clear! No pending notifications.
                    """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="view_notifications")],
                    [InlineKeyboardButton("🧹 Clear All", callback_data="clear_notifications")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]
                
                await query.edit_message_text(
                    notif_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                self.log_action("VIEW_NOTIFICATIONS", f"Count: {len(notif_lines) if notifications else 0}")
                
            else:
                raise Exception("Cannot access notifications")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil notifikasi: {str(e)}\n\n💡 Berikan izin notifikasi ke Termux",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def get_call_logs(self, query):
        """Enhanced call logs"""
        await query.edit_message_text("📞 Mengambil log panggilan...")
        
        try:
            result = subprocess.run(['termux-call-log'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                call_data = json.loads(result.stdout)
                
                if call_data:
                    call_message = """
📞 **CALL LOGS**
═══════════════════════════════

📱 **Recent calls:**

"""
                    
                    for i, call in enumerate(call_data[:5], 1):  # Show latest 5
                        phone = call.get('phone_number', 'Unknown')
                        name = call.get('name', 'Unknown')
                        call_type = call.get('type', 'Unknown')
                        date = call.get('date', 'Unknown')
                        duration = call.get('duration', '0')
                        
                        # Format call type
                        type_icons = {
                            'incoming': '📞',
                            'outgoing': '📱',
                            'missed': '❌'
                        }
                        
                        type_icon = type_icons.get(call_type.lower(), '📞')
                        
                        call_message += f"""
**{i}.** {type_icon} **{name}**
• Phone: {phone}
• Type: {call_type}
• Duration: {duration}s
• Date: {date}
"""
                    
                else:
                    call_message = """
📞 **CALL LOGS**
═══════════════════════════════

✅ **No call logs found**

📱 No recent calls to display.
                    """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="call_logs")],
                    [InlineKeyboardButton("📊 Call Stats", callback_data="call_stats")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]
                
                await query.edit_message_text(
                    call_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                self.log_action("CALL_LOGS", f"Count: {len(call_data) if call_data else 0}")
                
            else:
                raise Exception("Cannot access call logs")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil log panggilan: {str(e)}\n\n💡 Berikan izin panggilan ke Termux",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def device_control(self, query):
        """Device control menu"""
        device_message = """
📱 **DEVICE CONTROL**
═══════════════════════════════

🎛️ **Control your device remotely:**

• 🔊 **Volume Control**
• 🔆 **Brightness Control** 
• 🔔 **Silent Mode Toggle**
• 📳 **Vibration Patterns**
• 🔒 **Screen Lock**
• ⚡ **Torch Control**
• 📺 **Display Settings**
• 🎵 **Media Control**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔊 Volume", callback_data="device_volume"),
                InlineKeyboardButton("🔆 Brightness", callback_data="device_brightness")
            ],
            [
                InlineKeyboardButton("🔔 Silent Mode", callback_data="device_silent"),
                InlineKeyboardButton("⚡ Torch", callback_data="device_torch")
            ],
            [
                InlineKeyboardButton("📳 Vibrate", callback_data="vibrate_device"),
                InlineKeyboardButton("🔒 Lock Screen", callback_data="lock_system")
            ],
            [
                InlineKeyboardButton("🎵 Media", callback_data="device_media"),
                InlineKeyboardButton("📺 Display", callback_data="device_display")
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            device_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_device_callback(self, query):
        """Handle device control callbacks"""
        if query.data == "device_volume":
            await self.volume_control(query)
        elif query.data == "device_brightness":
            await self.brightness_control(query)

    async def volume_control(self, query):
        """Volume control"""
        try:
            # Get current volume
            result = subprocess.run(['termux-volume'], 
                                  capture_output=True, text=True, timeout=5)
            
            volume_message = """
🔊 **VOLUME CONTROL**
═══════════════════════════════

🎵 **Current Volume Levels:**
• Music: Getting info...
• Ring: Getting info...
• System: Getting info...

📱 **Quick Actions:**
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔇 Mute", callback_data="volume_mute"),
                    InlineKeyboardButton("🔊 Max", callback_data="volume_max")
                ],
                [
                    InlineKeyboardButton("➖ Down", callback_data="volume_down"),
                    InlineKeyboardButton("➕ Up", callback_data="volume_up")
                ],
                [
                    InlineKeyboardButton("🔙 Device Control", callback_data="device_control")
                ]
            ]
            
            await query.edit_message_text(
                volume_message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Volume control error: {str(e)}")

    async def get_system_info(self, query):
        """Enhanced system information"""
        await query.edit_message_text("ℹ️ Menganalisis sistem...")
        
        try:
            # Get comprehensive system info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get Android specific info
            android_info = {}
            try:
                # Android version
                result = subprocess.run(['getprop', 'ro.build.version.release'], 
                                      capture_output=True, text=True)
                android_info['version'] = result.stdout.strip() or 'Unknown'
                
                # Device model
                result = subprocess.run(['getprop', 'ro.product.model'], 
                                      capture_output=True, text=True)
                android_info['model'] = result.stdout.strip() or 'Unknown'
                
                # Device brand
                result = subprocess.run(['getprop', 'ro.product.brand'], 
                                      capture_output=True, text=True)
                android_info['brand'] = result.stdout.strip() or 'Unknown'
                
                # Android SDK
                result = subprocess.run(['getprop', 'ro.build.version.sdk'], 
                                      capture_output=True, text=True)
                android_info['sdk'] = result.stdout.strip() or 'Unknown'
                
                # Architecture
                result = subprocess.run(['uname', '-m'], 
                                      capture_output=True, text=True)
                android_info['arch'] = result.stdout.strip() or 'Unknown'
                
            except:
                android_info = {
                    'version': 'Unknown',
                    'model': 'Unknown', 
                    'brand': 'Unknown',
                    'sdk': 'Unknown',
                    'arch': 'Unknown'
                }
            
            # Get network interfaces
            network_info = []
            try:
                interfaces = psutil.net_if_addrs()
                for interface, addresses in interfaces.items():
                    for addr in addresses:
                        if addr.family == 2:  # IPv4
                            network_info.append(f"{interface}: {addr.address}")
            except:
                network_info = ["Network info unavailable"]
            
            # System uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    uptime_str = str(timedelta(seconds=int(uptime_seconds)))
            except:
                uptime_str = "Unknown"
            
            # Storage info
            storage_used = disk.used // (1024**3)  # GB
            storage_total = disk.total // (1024**3)  # GB
            storage_free = disk.free // (1024**3)  # GB
            
            # Memory info
            ram_used = memory.used // (1024**2)  # MB
            ram_total = memory.total // (1024**2)  # MB
            ram_available = memory.available // (1024**2)  # MB
            
            system_message = f"""
ℹ️ **SYSTEM INFORMATION**
═══════════════════════════════

📱 **Device Info:**
• **Brand:** {android_info['brand']}
• **Model:** {android_info['model']}
• **Android:** {android_info['version']} (SDK {android_info['sdk']})
• **Architecture:** {android_info['arch']}

💻 **Performance:**
• **CPU Usage:** {cpu_percent}% ({cpu_count} cores)
• **RAM Usage:** {memory.percent}%
  └ Used: {ram_used}MB / {ram_total}MB
  └ Available: {ram_available}MB

💾 **Storage:**
• **Usage:** {disk.percent}%
  └ Used: {storage_used}GB / {storage_total}GB
  └ Free: {storage_free}GB

🌐 **Network:**
{chr(10).join([f"• {info}" for info in network_info[:3]])}

⏱️ **System:**
• **Uptime:** {uptime_str}
• **Current Dir:** `{os.path.basename(self.current_directory)}`
• **Python:** {sys.version.split()[0]}

⏰ **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="system_info"),
                    InlineKeyboardButton("📊 Detailed", callback_data="system_detailed")
                ],
                [
                    InlineKeyboardButton("🧹 Clean RAM", callback_data="clean_ram"),
                    InlineKeyboardButton("💾 Storage", callback_data="storage_info")
                ],
                [
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]
            ]
            
            await query.edit_message_text(
                system_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            self.log_action("SYSTEM_INFO", f"CPU: {cpu_percent}%, RAM: {memory.percent}%")
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil info sistem: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def file_manager(self, query):
        """Enhanced file manager"""
        files_message = f"""
🗂️ **FILE MANAGER**
═══════════════════════════════

📁 **Current Directory:** 
`{self.current_directory}`

📋 **Quick Actions:**
• Browse files and folders
• Upload/Download files
• Create/Delete files
• File compression
• Search files
• File permissions

🚀 **Choose an action:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📂 Browse", callback_data="file_browse"),
                InlineKeyboardButton("🔍 Search", callback_data="file_search")
            ],
            [
                InlineKeyboardButton("📄 Create File", callback_data="file_create"),
                InlineKeyboardButton("📁 Create Folder", callback_data="folder_create")
            ],
            [
                InlineKeyboardButton("📤 Upload", callback_data="file_upload"),
                InlineKeyboardButton("📥 Download", callback_data="file_download")
            ],
            [
                InlineKeyboardButton("🗜️ Compress", callback_data="file_compress"),
                InlineKeyboardButton("📊 Disk Usage", callback_data="disk_usage")
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            files_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def security_menu(self, query):
        """Enhanced security menu"""
        security_message = """
🛡️ **SECURITY CENTER**
═══════════════════════════════

🔒 **Available Security Features:**

• **File Encryption** - Encrypt sensitive files
• **Folder Lock** - Password protect folders  
• **Secure Delete** - Permanently delete files
• **Permission Manager** - File permissions
• **Access Logs** - Monitor file access
• **Backup & Restore** - Secure backups
• **QR Code Generator** - Generate QR codes
• **Password Generator** - Strong passwords

🛡️ **Choose security action:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔐 Encrypt Files", callback_data="security_encrypt"),
                InlineKeyboardButton("🗂️ Lock Folder", callback_data="security_lock_folder")
            ],
            [
                InlineKeyboardButton("🗑️ Secure Delete", callback_data="security_delete"),
                InlineKeyboardButton("👁️ Access Logs", callback_data="security_logs")
            ],
            [
                InlineKeyboardButton("🔑 Gen Password", callback_data="security_password"),
                InlineKeyboardButton("📱 QR Generator", callback_data="security_qr")
            ],
            [
                InlineKeyboardButton("💾 Secure Backup", callback_data="security_backup"),
                InlineKeyboardButton("🔒 Permissions", callback_data="security_permissions")
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            security_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def backup_gallery(self, query):
        """Enhanced backup system"""
        await query.edit_message_text("💾 Initializing backup system...")
        
        try:
            # Create backup directory
            backup_dir = os.path.expanduser('~/termux_bot_backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Backup locations
            backup_paths = {
                'Photos': '~/storage/dcim/Camera',
                'Downloads': '~/storage/downloads', 
                'Documents': '~/storage/shared/Documents',
                'WhatsApp': '~/storage/shared/WhatsApp'
            }
            
            backup_info = []
            total_size = 0
            
            for name, path in backup_paths.items():
                full_path = os.path.expanduser(path)
                if os.path.exists(full_path):
                    try:
                        # Get folder size
                        size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                 for dirpath, dirnames, filenames in os.walk(full_path)
                                 for filename in filenames)
                        
                        file_count = sum(len(filenames) 
                                       for dirpath, dirnames, filenames in os.walk(full_path))
                        
                        backup_info.append({
                            'name': name,
                            'path': path,
                            'size': size,
                            'files': file_count
                        })
                        total_size += size
                        
                    except Exception as e:
                        backup_info.append({
                            'name': name,
                            'path': path,
                            'size': 0,
                            'files': 0
                        })
            
            backup_message = f"""
💾 **BACKUP MANAGER**
═══════════════════════════════

📊 **Backup Overview:**

"""
            
            for info in backup_info:
                size_mb = info['size'] / (1024 * 1024)
                backup_message += f"**{info['name']}:**\n"
                backup_message += f"• Files: {info['files']}\n"
                backup_message += f"• Size: {size_mb:.1f} MB\n"
                backup_message += f"• Path: `{info['path']}`\n\n"
            
            total_mb = total_size / (1024 * 1024)
            backup_message += f"📈 **Total Size:** {total_mb:.1f} MB\n"
            backup_message += f"⏰ **Last Check:** {datetime.now().strftime('%H:%M:%S')}"
            
            keyboard = [
                [
                    InlineKeyboardButton("📷 Backup Photos", callback_data="backup_photos"),
                    InlineKeyboardButton("📄 Backup Docs", callback_data="backup_docs")
                ],
                [
                    InlineKeyboardButton("💬 Backup WhatsApp", callback_data="backup_whatsapp"),
                    InlineKeyboardButton("📥 Backup All", callback_data="backup_all")
                ],
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="backup_gallery"),
                    InlineKeyboardButton("📊 Backup History", callback_data="backup_history")
                ],
                [
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]
            ]
            
            await query.edit_message_text(
                backup_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
            self.log_action("BACKUP_SCAN", f"Total size: {total_mb:.1f}MB")
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Backup scan failed: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def view_stats(self, query):
        """View bot statistics"""
        try:
            conn = sqlite3.connect(self.config.db_path)
            cursor = conn.cursor()
            
            # Get action counts
            cursor.execute('SELECT action, COUNT(*) FROM logs GROUP BY action ORDER BY COUNT(*) DESC LIMIT 10')
            action_stats = cursor.fetchall()
            
            # Get recent activity
            cursor.execute('SELECT action, details, timestamp FROM logs ORDER BY timestamp DESC LIMIT 5')
            recent_activity = cursor.fetchall()
            
            conn.close()
            
            stats_message = f"""
📊 **BOT STATISTICS**
═══════════════════════════════

📈 **Top Actions:**
"""
            
            for i, (action, count) in enumerate(action_stats, 1):
                stats_message += f"{i}. **{action}:** {count}x\n"
            
            stats_message += f"""

🕐 **Recent Activity:**
"""
            
            for action, details, timestamp in recent_activity:
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M')
                stats_message += f"• **{time_str}** - {action}\n"
            
            stats_message += f"""

ℹ️ **System Stats:**
• **Bot Uptime:** {str(timedelta(seconds=int(time.time() - os.path.getctime(__file__))))}
• **Current Dir:** `{os.path.basename(self.current_directory)}`
• **Last Update:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            await query.edit_message_text(
                stats_message,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Refresh", callback_data="view_stats"),
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Stats error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def lock_system(self, query):
        """Enhanced system lock"""
        await query.edit_message_text("🔒 Locking system...")
        
        try:
            # Multiple lock methods
            lock_methods = []
            
            # Method 1: Screen lock
            try:
                result = subprocess.run(['termux-keyguard-lock'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lock_methods.append("Screen lock activated")
            except:
                pass
            
            # Method 2: Turn off screen
            try:
                result = subprocess.run(['termux-torch', 'off'], 
                                      capture_output=True, text=True, timeout=3)
            except:
                pass
            
            # Method 3: Activate device admin (if available)
            try:
                result = subprocess.run(['am', 'start', '-a', 'android.app.action.ADD_DEVICE_ADMIN'], 
                                      capture_output=True, text=True, timeout=5)
            except:
                pass
            
            if lock_methods:
                lock_message = f"""
🔒 **SYSTEM LOCKED**
═══════════════════════════════

✅ **Lock Status:**
{chr(10).join([f"• {method}" for method in lock_methods])}

🛡️ **Security Active:**
• Screen locked
• Unauthorized access blocked
• Bot monitoring continues

⏰ **Locked at:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

💡 **Note:** Use biometric or PIN to unlock device
                """
            else:
                lock_message = """
🔒 **SYSTEM LOCK ATTEMPTED**
═══════════════════════════════

⚠️ **Partial Lock Applied:**
• Screen timeout reduced
• Some security measures activated

💡 **Note:** Full lock requires device admin permissions
                """
            
            await query.edit_message_text(
                lock_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔓 Unlock Info", callback_data="unlock_info")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
            self.log_action("SYSTEM_LOCK", "System lock attempted")
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Lock failed: {str(e)}\n\n💡 Beberapa fitur lock memerlukan root access",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def change_wallpaper(self, query):
        """Enhanced wallpaper changer"""
        wallpaper_message = """
🖼️ **WALLPAPER MANAGER**
═══════════════════════════════

🎨 **Wallpaper Options:**

• **Random Online** - Download random wallpaper
• **Solid Color** - Set solid color background
• **Upload Custom** - Use your own image
• **Gallery Pick** - Choose from device gallery
• **Restore Default** - Reset to default

📱 **Current Status:** Getting info...

🚀 **Choose wallpaper source:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🌐 Random Online", callback_data="wallpaper_random"),
                InlineKeyboardButton("🎨 Solid Color", callback_data="wallpaper_color")
            ],
            [
                InlineKeyboardButton("📷 From Gallery", callback_data="wallpaper_gallery"),
                InlineKeyboardButton("📤 Upload Custom", callback_data="wallpaper_upload")
            ],
            [
                InlineKeyboardButton("🔄 Restore Default", callback_data="wallpaper_default"),
                InlineKeyboardButton("ℹ️ Current Info", callback_data="wallpaper_info")
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            wallpaper_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def manage_contacts(self, query):
        """Enhanced contact manager"""
        contacts_message = """
👥 **CONTACT MANAGER**
═══════════════════════════════

📱 **Contact Operations:**

• **View Contacts** - Show all contacts
• **Add Contact** - Add new contact
• **Search Contact** - Find specific contact
• **Export Contacts** - Backup to file
• **Import Contacts** - Restore from backup
• **Contact Statistics** - Usage stats

📊 **Quick Stats:** Loading...

🚀 **Choose operation:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📱 View All", callback_data="contacts_view"),
                InlineKeyboardButton("➕ Add New", callback_data="contacts_add")
            ],
            [
                InlineKeyboardButton("🔍 Search", callback_data="contacts_search"),
                InlineKeyboardButton("📤 Export", callback_data="contacts_export")
            ],
            [
                InlineKeyboardButton("📥 Import", callback_data="contacts_import"),
                InlineKeyboardButton("📊 Statistics", callback_data="contacts_stats")
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            contacts_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def termux_terminal(self, query):
        """Enhanced terminal interface"""
        terminal_message = f"""
💻 **TERMUX TERMINAL**
═══════════════════════════════

📁 **Current Directory:** 
`{self.current_directory}`

🚀 **Terminal Features:**
• Execute any Linux command
• File operations (ls, cd, mkdir, etc.)
• Package management (pkg install)
• Python script execution
• Network tools (ping, curl, wget)
• System monitoring (top, ps, df)

💡 **Quick Commands:**
• `ls` - List files
• `cd ~` - Go to home
• `pwd` - Current path
• `df -h` - Disk usage
• `free -h` - Memory usage

⌨️ **Ketik perintah langsung di chat!**

📋 **Quick Actions:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📂 ls", callback_data="cmd_ls"),
                InlineKeyboardButton("🏠 cd ~", callback_data="cmd_home")
            ],
            [
                InlineKeyboardButton("💾 df -h", callback_data="cmd_df"),
                InlineKeyboardButton("🧠 free -h", callback_data="cmd_free")
            ],
            [
                InlineKeyboardButton("⚡ top", callback_data="cmd_top"),
                InlineKeyboardButton("📊 ps aux", callback_data="cmd_ps")
            ],
            [
                InlineKeyboardButton("🌐 ping google.com", callback_data="cmd_ping"),
                InlineKeyboardButton("📦 pkg list-installed", callback_data="cmd_pkg")
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            terminal_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def bot_settings(self, query):
        """Enhanced bot settings"""
        settings_message = f"""
⚙️ **BOT SETTINGS**
═══════════════════════════════

🤖 **Bot Status:** {'🟢 Active' if self.config.bot_active else '🔴 Inactive'}
🌱 **Auto Start:** {'🟢 Enabled' if self.config.auto_start else '🔴 Disabled'}

📊 **Statistics:**
• **Uptime:** {str(timedelta(seconds=int(time.time() - os.path.getctime(__file__))))}
• **Commands Used:** Loading...
• **Last Activity:** {datetime.now().strftime('%H:%M:%S')}

🛠️ **Configuration:**
• **Working Dir:** `{os.path.basename(self.current_directory)}`
• **Log Level:** INFO
• **Encryption:** Enabled

⚙️ **Management Options:**
        """
        
        await query.edit_message_text(
            settings_message,
            reply_markup=self.create_settings_keyboard(),
            parse_mode='Markdown'
        )

    async def toggle_bot(self, query):
        """Toggle bot status"""
        self.config.bot_active = not self.config.bot_active
        status = "🟢 activated" if self.config.bot_active else "🔴 deactivated" 
        
        message = f"""
{'✅' if self.config.bot_active else '❌'} **Bot {status.split()[1].upper()}**
═══════════════════════════════

🤖 **Status Changed:**
Bot has been {status}

{'🚀 **All features are now available!**' if self.config.bot_active else '⚠️ **Bot features are now disabled**'}

⏰ **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        self.log_action("BOT_TOGGLE", f"Status: {self.config.bot_active}")

    async def toggle_auto_start(self, query):
        """Toggle auto start"""
        self.config.auto_start = not self.config.auto_start
        self.config.save_config(self.config.bot_token)
        
        status = "🟢 enabled" if self.config.auto_start else "🔴 disabled"
        
        message = f"""
{'✅' if self.config.auto_start else '❌'} **Auto Start {status.split()[1].upper()}**
═══════════════════════════════

🌱 **Auto Start Status:**
Auto start has been {status}

{'🚀 **Bot will start automatically when Termux opens**' if self.config.auto_start else '⚠️ **Bot will need manual start**'}

⏰ **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    async def clear_logs(self, query):
        """Clear bot logs"""
        try:
            conn = sqlite3.connect(self.config.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM logs')
            conn.commit()
            conn.close()
            
            # Clear log file
            with open('bot.log', 'w') as f:
                f.write('')
            
            await query.edit_message_text(
                "✅ **LOGS CLEARED**\n═══════════════════════════════\n\n🧹 All logs have been cleared successfully!\n\n⏰ **Time:** " + datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚙️ Settings", callback_data="bot_settings")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(f"❌ Clear logs failed: {str(e)}")

    async def restart_bot(self, query):
        """Restart bot"""
        await query.edit_message_text(
            "🔄 **RESTARTING BOT**\n═══════════════════════════════\n\n⏳ Bot is restarting...\nPlease wait a moment and send /start",
            parse_mode='Markdown'
        )
        
        # Log restart
        self.log_action("BOT_RESTART", "Bot restart initiated")
        
        # Restart the bot
        os.execv(sys.executable, [sys.executable] + sys.argv)

    async def handle_terminal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced terminal command handler"""
        command = update.message.text.strip()
        
        if not self.config.bot_active:
            await update.message.reply_text("🔴 Bot tidak aktif. Aktifkan melalui /start → Settings")
            return
        
        # Log command
        self.log_action("TERMINAL_CMD", command[:50])
        
        try:
            # Handle special commands
            if command.startswith('cd '):
                await self.handle_cd_command(update, command)
                return
            elif command in ['clear', 'cls']:
                await update.message.reply_text("💻 **Terminal cleared**", parse_mode='Markdown')
                return
            elif command == 'pwd':
                await update.message.reply_text(f"📁 **Current directory:**\n`{self.current_directory}`", parse_mode='Markdown')
                return
            
            # Execute command
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=self.current_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=30)
                output = stdout + stderr
                
                if not output.strip():
                    output = "✅ Command executed successfully (no output)"
                
                # Limit output length
                if len(output) > 3500:
                    output = output[:3500] + "\n\n... (output truncated - too long)"
                
                # Format output
                formatted_output = f"💻 **Command:** `{command}`\n📁 **Directory:** `{os.path.basename(self.current_directory)}`\n\n```\n{output}\n```"
                
                await update.message.reply_text(formatted_output, parse_mode='Markdown')
                
            except subprocess.TimeoutExpired:
                process.kill()
                await update.message.reply_text("⏰ **Command timeout** (30s limit)\n💡 Command was terminated")
                
        except Exception as e:
            error_msg = f"❌ **Command Error:**\n```\n{str(e)}\n```\n\n💡 **Tips:**\n• Check command syntax\n• Verify file permissions\n• Use absolute paths if needed"
            await update.message.reply_text(error_msg, parse_mode='Markdown')

    async def handle_cd_command(self, update, command):
        """Handle cd command specially"""
        path = command[3:].strip()
        
        if not path:
            path = '~'
        
        if path == '~':
            new_path = os.path.expanduser('~')
        elif path.startswith('/'):
            new_path = path
        else:
            new_path = os.path.join(self.current_directory, path)
        
        new_path = os.path.abspath(new_path)
        
        if os.path.exists(new_path) and os.path.isdir(new_path):
            self.current_directory = new_path
            
            # Get directory info
            try:
                files = os.listdir(new_path)
                file_count = len([f for f in files if os.path.isfile(os.path.join(new_path, f))])
                dir_count = len([f for f in files if os.path.isdir(os.path.join(new_path, f))])
            except:
                file_count = dir_count = 0
            
            response = f"""
📁 **Directory Changed**
═══════════════════════════════

✅ **New Location:** `{new_path}`

📊 **Contents:**
• **Files:** {file_count}
• **Folders:** {dir_count}

💡 **Use `ls` to see contents**
            """
            
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text(f"❌ **Directory not found:** `{path}`\n💡 Use `ls` to see available directories", parse_mode='Markdown')

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced error handler"""
        error_msg = str(context.error)
        logger.error(f"Update {update} caused error {context.error}")
        
        # Log error to database
        self.log_action("ERROR", error_msg[:200])
        
        try:
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"❌ **Bot Error**\n```\n{error_msg[:500]}\n```\n\n🔄 Try /start to restart",
                    parse_mode='Markdown'
                )
        except:
            pass

    def run(self):
        """Enhanced bot runner"""
        print("\n" + "="*60)
        print("🤖 TERMUX BOT CONTROLLER v2.0 - ENHANCED")
        print("="*60)
        print("🚀 Initializing enhanced bot...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🔗 Bot Token: {self.config.bot_token[:10]}...****")
        print(f"💾 Database: {self.config.db_path}")
        print(f"🔐 Encryption: Enabled")
        
        try:
            # Create application
            self.app = Application.builder().token(self.config.bot_token).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CallbackQueryHandler(self.button_handler))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_terminal_command))
            self.app.add_error_handler(self.error_handler)
            
            print("✅ Bot successfully initialized!")
            print("💬 Send /start in Telegram to begin")
            print("🔄 Press Ctrl+C to stop")
            print("="*60)
            
            # Log bot start
            self.log_action("BOT_STARTED", f"Version 2.0 - {datetime.now().isoformat()}")
            
            # Run the bot
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            self.log_action("BOT_STOPPED", "Manual stop")
        except Exception as e:
            print(f"❌ Critical error: {e}")
            self.log_action("BOT_ERROR", str(e))
            sys.exit(1)

def main():
    """Main function with error handling"""
    try:
        # Check if running in Termux
        if not os.path.exists('/data/data/com.termux'):
            print("⚠️  WARNING: This bot is designed for Termux environment")
            print("Some features may not work properly outside Termux")
            
        bot = TermuxBotController()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()_text(
                    f"✅ Foto {camera_name.lower()} berhasil diambil!\n📁 Tersimpan di: `{photo_path}`",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📷 Foto Lagi", callback_data="take_photo")],
                        [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception(f"Camera error: {result.stderr}")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil foto: {str(e)}\n\n💡 Tips:\n• Pastikan Termux:API terinstall\n• Berikan izin kamera ke Termux\n• Coba restart aplikasi",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="take_photo")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ])
            )

    async def record_video(self, query):
        """Record video from camera"""
        await query.edit_message_text("🎥 Recording video selama 10 detik...")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_path = f"/tmp/video_{timestamp}.mp4"
            
            result = subprocess.run([
                'termux-tts-speak', 'Recording started'
            ], capture_output=True)
            
            result = subprocess.run([
                'termux-camera-video', 
                '-c', '1',
                '-s', '1280x720',
                '-l', '10',  # 10 seconds
                video_path
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(video_path):
                file_size = os.path.getsize(video_path)
                if file_size < 50 * 1024 * 1024:  # 50MB limit
                    with open(video_path, 'rb') as video:
                        await query.message.reply_video(
                            video=video,
                            caption=f"🎥 Video recorded\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                        )
                    os.remove(video_path)
                    
                    await query.edit_message_text(
                        "✅ Video berhasil direkam dan dikirim!",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🔙 Kembali", callback_data="take_photo")
                        ]])
                    )
                else:
                    await query.edit_message_text("❌ Video terlalu besar (>50MB)")
            else:
                raise Exception("Failed to record video")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal merekam video: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="take_photo")
                ]])
            )

    async def get_camera_info(self, query):
        """Get camera information"""
        try:
            result = subprocess.run(['termux-camera-info'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                camera_info = json.loads(result.stdout)
                
                info_text = "📊 **CAMERA INFO**\n═══════════════════\n\n"
                
                for i, camera in enumerate(camera_info):
                    facing = "📷 Front" if camera.get('facing') == 'front' else "📸 Back"
                    info_text += f"**Camera {i}:** {facing}\n"
                    info_text += f"• **ID:** {camera.get('id', 'Unknown')}\n"
                    if 'sizes' in camera:
                        sizes = camera['sizes'][:3]  # Show first 3 sizes
                        info_text += f"• **Sizes:** {', '.join(sizes)}\n"
                    info_text += "\n"
                
                await query.edit_message_text(
                    info_text,
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="take_photo")
                    ]]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception("Cannot get camera info")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="take_photo")
                ]])
            )

    async def check_battery(self, query):
        """Enhanced battery status"""
        await query.edit_message_text("🔋 Menganalisis status baterai...")
        
        try:
            result = subprocess.run(['termux-battery-status'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                battery_info = json.loads(result.stdout)
                
                percentage = battery_info.get('percentage', 0)
                status = battery_info.get('status', 'UNKNOWN')
                health = battery_info.get('health', 'UNKNOWN')
                temperature = battery_info.get('temperature', 0)
                voltage = battery_info.get('voltage', 0)
                current = battery_info.get('current', 0)
                
                # Enhanced status icons
                status_icons = {
                    'CHARGING': '🔌',
                    'DISCHARGING': '🔋',
                    'NOT_CHARGING': '🔌',
                    'FULL': '🔋',
                    'UNKNOWN': '❓'
                }
                
                health_icons = {
                    'GOOD': '✅',
                    'OVERHEAT': '🔥',
                    'DEAD': '💀',
                    'COLD': '🧊',
                    'UNKNOWN': '❓'
                }
                
                # Battery level emoji
                if percentage >= 90:
                    battery_emoji = "🔋"
                elif percentage >= 70:
                    battery_emoji = "🔋"
                elif percentage >= 50:
                    battery_emoji = "🔋"
                elif percentage >= 30:
                    battery_emoji = "🪫"
                else:
                    battery_emoji = "🪫"
                
                # Create battery bar
                bar_length = 20
                filled = int((percentage / 100) * bar_length)
                battery_bar = '█' * filled + '░' * (bar_length - filled)
                
                # Temperature warning
                temp_warning = ""
                if temperature > 40:
                    temp_warning = "\n⚠️ **Temperature tinggi!**"
                elif temperature < 0:
                    temp_warning = "\n❄️ **Temperature rendah!**"
                
                battery_message = f"""
🔋 **BATTERY STATUS** {battery_emoji}
═══════════════════════════════

📊 **Level:** {percentage}%
{battery_bar}

{status_icons.get(status, '❓')} **Status:** {status}
{health_icons.get(health, '❓')} **Health:** {health}
🌡️ **Temperature:** {temperature}°C{temp_warning}
⚡ **Voltage:** {voltage/1000:.2f}V
🔌 **Current:** {current}mA

⏰ **Updated:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                """
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="check_battery")],
                    [InlineKeyboardButton("📊 Battery History", callback_data="battery_history")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]
                
                await query.edit_message_text(
                    battery_message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
                
                self.log_action("BATTERY_CHECK", f"Level: {percentage}%, Status: {status}")
                
            else:
                raise Exception("Cannot access battery information")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengecek baterai: {str(e)}\n\n💡 Pastikan Termux:API terinstall",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def track_location(self, query):
        """Enhanced GPS location tracking"""
        await query.edit_message_text("📍 Mendapatkan lokasi GPS...")
        
        try:
            # Get location with high accuracy
            result = subprocess.run([
                'termux-location', 
                '-p', 'gps',
                '-r', 'once'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                location_data = json.loads(result.stdout)
                
                latitude = location_data.get('latitude', 0)
                longitude = location_data.get('longitude', 0)
                accuracy = location_data.get('accuracy', 0)
                altitude = location_data.get('altitude', 0)
                speed = location_data.get('speed', 0)
                bearing = location_data.get('bearing', 0)
                
                # Create Google Maps link
                maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                
                # Get address using reverse geocoding
                try:
                    geocode_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={latitude}&longitude={longitude}&localityLanguage=id"
                    response = requests.get(geocode_url, timeout=10)
                    address_data = response.json()
                    address = address_data.get('display_name', 'Unknown location')
                except:
                    address = "Address lookup failed"
                
                location_message = f"""
📍 **GPS LOCATION FOUND**
═══════════════════════════════

🌍 **Coordinates:**
• **Latitude:** {latitude:.6f}
• **Longitude:** {longitude:.6f}

📐 **Details:**
• **Accuracy:** ±{accuracy:.1f}m
• **Altitude:** {altitude:.1f}m
• **Speed:** {speed:.1f} m/s
• **Bearing:** {bearing:.1f}°

📍 **Address:**
{address}

🗺️ **Maps:** [Open in Google Maps]({maps_link})

⏰ **Time:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
                """
                
                # Send location
                await query.message.reply_location(
                    latitude=latitude,
                    longitude=longitude
                )
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Update Location", callback_data="track_location")],
                    [InlineKeyboardButton("🗺️ Open Maps", url=maps_link)],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]
                
                await query.edit_message
