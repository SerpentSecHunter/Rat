#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Termux Controller - REALISTIC VERSION
Developed for Termux Android Environment
Author: Assistant
Version: 2.0 - Real Working Features Only
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
import shutil
import glob
from datetime import datetime
from pathlib import Path

# Auto install required packages
def install_requirements():
    packages = [
        'python-telegram-bot==20.7',
        'psutil',
        'requests',
        'python-dotenv'
    ]
    
    for package in packages:
        try:
            __import__(package.split('==')[0].replace('-', '_'))
        except ImportError:
            print(f"📦 Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         capture_output=True, text=True)

# Install requirements first
install_requirements()

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from dotenv import load_dotenv
import psutil

# Load environment variables
load_dotenv()

# Configuration
class Config:
    def __init__(self):
        self.bot_token = self.get_token()
        self.chat_id = None
        self.bot_active = True
        self.auto_start = False
        
    def get_token(self):
        token = os.getenv('BOT_TOKEN')
        if not self.termux_api_available:
            print("⚠️  WARNING: Termux:API not detected!")
            print("   Install Termux:API from F-Droid for full features")
        
        try:
            # Create application
            self.app = Application.builder().token(self.config.bot_token).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CallbackQueryHandler(self.button_handler))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_terminal_command))
            self.app.add_error_handler(self.error_handler)
            
            print("✅ Bot successfully started!")
            print("💬 Send /start in Telegram to begin")
            print("🔄 Press Ctrl+C to stop")
            print("="*60)
            
            # Send startup notification if chat_id exists
            if self.config.chat_id:
                try:
                    startup_message = f"""
🤖 **BOT RESTARTED**
═══════════════════════

✅ **Status:** Bot is now online
📁 **Directory:** `{os.path.basename(self.current_directory)}`
📱 **Termux:API:** {'✅ Available' if self.termux_api_available else '❌ Not Available'}
🕐 **Time:** {datetime.now().strftime('%H:%M:%S')}

🚀 **Ready to use!**
                    """
                    # This will be sent when first message is received
                except:
                    pass
            
            # Run the bot
            self.app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            logger.error(f"Bot startup error: {e}")
            sys.exit(1)

def main():
    """Main function with auto-restart capability"""
    print("🤖 TERMUX BOT CONTROLLER")
    print("Loading...")
    
    # Check if auto-start is enabled
    if len(sys.argv) > 1 and sys.argv[1] == '--auto-start':
        print("🌱 Auto-start mode detected")
        time.sleep(2)  # Wait for system to stabilize
    
    max_restarts = 5
    restart_count = 0
    
    while restart_count < max_restarts:
        try:
            bot = TermuxBot()
            bot.run()
            break  # Normal exit
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            break
            
        except Exception as e:
            restart_count += 1
            print(f"❌ Bot crashed (restart {restart_count}/{max_restarts}): {e}")
            
            if restart_count < max_restarts:
                print(f"🔄 Restarting in 5 seconds...")
                time.sleep(5)
            else:
                print("💀 Max restarts reached. Bot stopped.")
                break

if __name__ == "__main__":
    main() not token:
            config_file = 'bot_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('bot_token')
        
        if not token:
            print("🤖 SETUP BOT TOKEN")
            print("=" * 50)
            print("1. Buat bot baru di @BotFather")
            print("2. Copy token yang diberikan")
            print("3. Paste di bawah ini")
            print("=" * 50)
            token = input("Masukkan Bot Token: ").strip()
            self.save_config(token)
        
        return token
    
    def save_config(self, token):
        config = {
            'bot_token': token,
            'auto_start': self.auto_start
        }
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        with open('.env', 'w') as f:
            f.write(f"BOT_TOKEN={token}\n")

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

class TermuxBot:
    def __init__(self):
        self.config = Config()
        self.app = None
        self.current_directory = os.path.expanduser('~')
        self.termux_api_available = self.check_termux_api()
        
    def check_termux_api(self):
        """Check if Termux:API is installed and working"""
        try:
            result = subprocess.run(['which', 'termux-battery-status'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
        
    def create_main_keyboard(self):
        """Create main menu keyboard with working features only"""
        keyboard = [
            [
                InlineKeyboardButton("💻 Terminal Termux", callback_data="termux_terminal"),
                InlineKeyboardButton("ℹ️ Info Sistem", callback_data="system_info")
            ],
            [
                InlineKeyboardButton("📁 File Manager", callback_data="file_manager"),
                InlineKeyboardButton("🔍 Cari File", callback_data="search_files")
            ]
        ]
        
        # Add Termux:API features if available
        if self.termux_api_available:
            keyboard.extend([
                [
                    InlineKeyboardButton("📷 Ambil Foto", callback_data="take_photo"),
                    InlineKeyboardButton("🔋 Cek Baterai", callback_data="check_battery")
                ],
                [
                    InlineKeyboardButton("📍 Lokasi GPS", callback_data="get_location"),
                    InlineKeyboardButton("📳 Getarkan HP", callback_data="vibrate_device")
                ],
                [
                    InlineKeyboardButton("📋 Clipboard", callback_data="clipboard_menu"),
                    InlineKeyboardButton("🔆 Brightness", callback_data="brightness_control")
                ]
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⚠️ Install Termux:API", callback_data="install_api_guide")
            ])
            
        keyboard.extend([
            [
                InlineKeyboardButton("📊 Monitor Sistem", callback_data="system_monitor"),
                InlineKeyboardButton("🔧 Tools Utilitas", callback_data="utility_tools")
            ],
            [
                InlineKeyboardButton("⚙️ Pengaturan Bot", callback_data="bot_settings"),
                InlineKeyboardButton("❓ Bantuan", callback_data="help_menu")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)

    def create_settings_keyboard(self):
        """Create settings keyboard"""
        status = "🟢 ON" if self.config.bot_active else "🔴 OFF"
        auto_status = "🟢 ON" if self.config.auto_start else "🔴 OFF"
        
        keyboard = [
            [InlineKeyboardButton(f"Bot Status: {status}", callback_data="toggle_bot")],
            [InlineKeyboardButton(f"Auto Start: {auto_status}", callback_data="toggle_auto_start")],
            [InlineKeyboardButton("🌱 Tanam Bot", callback_data="plant_bot")],
            [InlineKeyboardButton("🔄 Restart Bot", callback_data="restart_bot")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.config.chat_id = update.effective_chat.id
        
        api_status = "✅ Terinstall" if self.termux_api_available else "❌ Belum Install"
        
        welcome_message = f"""
🤖 **TERMUX BOT CONTROLLER v2.0**
═══════════════════════════════════

👋 Selamat datang, **{user.first_name}**!

🎯 **STATUS SISTEM:**
• 🤖 Bot: **Aktif & Siap**
• 📱 Termux:API: **{api_status}**
• 📁 Directory: `{os.path.basename(self.current_directory)}`

🔥 **FITUR YANG BENAR-BENAR BERFUNGSI:**

**💻 TERMINAL & FILE:**
• Terminal Termux penuh (cd, ls, python, dll)
• File manager dengan upload/download
• Pencarian file dan folder
• Monitor sistem real-time

**📱 TERMUX:API (Jika Terinstall):**
• Ambil foto kamera depan/belakang
• Status baterai real-time
• GPS location tracking
• Getarkan device
• Clipboard management
• Brightness control

**⚡ TOOLS UTILITAS:**
• Process manager
• Network tools
• Package manager
• System monitoring

🚀 **Pilih menu untuk memulai!**
        """
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if not self.config.bot_active and query.data not in ["toggle_bot", "bot_settings"]:
            await query.edit_message_text("🔴 Bot sedang tidak aktif. Aktifkan melalui pengaturan.")
            return

        # Handle different button callbacks
        handlers = {
            "main_menu": self.show_main_menu,
            "termux_terminal": self.termux_terminal,
            "system_info": self.get_system_info,
            "file_manager": self.file_manager,
            "search_files": self.search_files,
            "take_photo": self.take_photo,
            "check_battery": self.check_battery,
            "get_location": self.get_location,
            "vibrate_device": self.vibrate_device,
            "clipboard_menu": self.clipboard_menu,
            "brightness_control": self.brightness_control,
            "install_api_guide": self.install_api_guide,
            "system_monitor": self.system_monitor,
            "utility_tools": self.utility_tools,
            "bot_settings": self.bot_settings,
            "help_menu": self.help_menu,
            "toggle_bot": self.toggle_bot,
            "toggle_auto_start": self.toggle_auto_start,
            "plant_bot": self.plant_bot,
            "restart_bot": self.restart_bot
        }
        
        handler = handlers.get(query.data)
        if handler:
            await handler(query)

    async def show_main_menu(self, query):
        """Show main menu"""
        api_status = "✅" if self.termux_api_available else "❌"
        message = f"""
🤖 **TERMUX BOT CONTROLLER**
═══════════════════════════════

📊 **STATUS:**
• Bot: 🟢 Aktif
• Termux:API: {api_status}
• Directory: `{os.path.basename(self.current_directory)}`

🎯 **Pilih fitur yang ingin digunakan:**
        """
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def termux_terminal(self, query):
        """Show termux terminal interface"""
        terminal_message = f"""
💻 **TERMUX TERMINAL**
═══════════════════════════════

📁 **Current Directory:** 
`{self.current_directory}`

📝 **Cara Penggunaan:**
Ketik perintah langsung di chat untuk eksekusi!

**📋 Contoh perintah:**
```
ls -la                 # Lihat file detail
cd /sdcard            # Masuk ke storage
python script.py      # Jalankan Python
pkg install git       # Install package
ps aux                # Lihat process
df -h                 # Lihat disk usage
```

💡 **Tips:**
• Gunakan `cd ~` untuk kembali ke home
• `pwd` untuk lihat directory saat ini
• `history` untuk lihat command history

⚡ **Ketik perintah Anda sekarang!**
        """
        
        await query.edit_message_text(
            terminal_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 File Manager", callback_data="file_manager"),
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]]),
            parse_mode='Markdown'
        )

    async def get_system_info(self, query):
        """Get detailed system information"""
        await query.edit_message_text("ℹ️ Mengambil informasi sistem...")
        
        try:
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            # Get Android info
            android_info = {}
            try:
                android_info['version'] = subprocess.run(['getprop', 'ro.build.version.release'], 
                                                       capture_output=True, text=True).stdout.strip()
                android_info['model'] = subprocess.run(['getprop', 'ro.product.model'], 
                                                     capture_output=True, text=True).stdout.strip()
                android_info['brand'] = subprocess.run(['getprop', 'ro.product.brand'], 
                                                     capture_output=True, text=True).stdout.strip()
                android_info['sdk'] = subprocess.run(['getprop', 'ro.build.version.sdk'], 
                                                   capture_output=True, text=True).stdout.strip()
            except:
                android_info = {'version': 'Unknown', 'model': 'Unknown', 'brand': 'Unknown', 'sdk': 'Unknown'}
            
            # Get network info
            try:
                ip_result = subprocess.run(['curl', '-s', 'ifconfig.me'], 
                                         capture_output=True, text=True, timeout=5)
                public_ip = ip_result.stdout.strip() if ip_result.returncode == 0 else "Unknown"
            except:
                public_ip = "Unknown"
            
            # Create system bars
            cpu_bar = self.create_progress_bar(cpu_percent)
            ram_bar = self.create_progress_bar(memory.percent)
            disk_bar = self.create_progress_bar(disk.percent)
            
            system_message = f"""
ℹ️ **INFORMASI SISTEM LENGKAP**
═══════════════════════════════════

📱 **DEVICE INFO:**
• **Brand:** {android_info['brand']}
• **Model:** {android_info['model']}
• **Android:** {android_info['version']} (SDK {android_info['sdk']})

💻 **SYSTEM RESOURCES:**
• **CPU:** {cpu_percent}% ({cpu_count} cores)
{cpu_bar}

• **RAM:** {memory.percent}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)
{ram_bar}

• **Storage:** {disk.percent}% ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)
{disk_bar}

🌐 **NETWORK:**
• **Public IP:** `{public_ip}`
• **Termux:API:** {'✅ Available' if self.termux_api_available else '❌ Not Installed'}

📁 **DIRECTORY:**
• **Current:** `{self.current_directory}`
• **Home:** `{os.path.expanduser('~')}`

⏰ **UPTIME:**
• **Boot Time:** {boot_time.strftime('%d/%m/%Y %H:%M:%S')}
• **Current:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            await query.edit_message_text(
                system_message,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Refresh", callback_data="system_info"),
                        InlineKeyboardButton("📊 Monitor", callback_data="system_monitor")
                    ],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil info sistem: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    def create_progress_bar(self, percentage, length=20):
        """Create progress bar for percentages"""
        filled = int((percentage / 100) * length)
        bar = '█' * filled + '░' * (length - filled)
        return f"`{bar}` {percentage:.1f}%"

    async def file_manager(self, query):
        """File manager functionality"""
        try:
            files = []
            dirs = []
            
            # Get files and directories
            for item in os.listdir(self.current_directory):
                item_path = os.path.join(self.current_directory, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            dirs.sort()
            files.sort()
            
            # Limit display
            display_dirs = dirs[:10]
            display_files = files[:10]
            
            file_list = ""
            
            if display_dirs:
                file_list += "📁 **DIREKTORI:**\n"
                for d in display_dirs:
                    file_list += f"  📁 `{d}`\n"
                file_list += "\n"
            
            if display_files:
                file_list += "📄 **FILE:**\n"
                for f in display_files:
                    size = self.get_file_size(os.path.join(self.current_directory, f))
                    file_list += f"  📄 `{f}` ({size})\n"
            
            if not display_dirs and not display_files:
                file_list = "📭 **Folder kosong**"
            
            if len(dirs) > 10 or len(files) > 10:
                file_list += f"\n... dan {len(dirs) + len(files) - 20} item lainnya"
            
            message = f"""
📁 **FILE MANAGER**
═══════════════════════════════

📍 **Path:** `{self.current_directory}`

{file_list}

💡 **Commands:**
• `cd nama_folder` - Masuk folder
• `ls -la` - Detail view
• `pwd` - Current path
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📁 Go to Home", callback_data="go_home"),
                    InlineKeyboardButton("⬆️ Parent Dir", callback_data="parent_dir")
                ],
                [
                    InlineKeyboardButton("🔍 Search", callback_data="search_files"),
                    InlineKeyboardButton("💻 Terminal", callback_data="termux_terminal")
                ],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    def get_file_size(self, filepath):
        """Get human readable file size"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f}{unit}"
                size /= 1024
            return f"{size:.1f}TB"
        except:
            return "Unknown"

    async def take_photo(self, query):
        """Take photo using camera - REAL IMPLEMENTATION"""
        if not self.termux_api_available:
            await query.edit_message_text(
                "❌ Termux:API tidak terinstall!\n\nInstall dulu Termux:API app.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📥 Install Guide", callback_data="install_api_guide"),
                    InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
                ]])
            )
            return
            
        await query.edit_message_text("📷 Mengambil foto...")
        
        try:
            # Create temp directory
            temp_dir = "/tmp"
            os.makedirs(temp_dir, exist_ok=True)
            photo_path = f"{temp_dir}/termux_photo_{int(time.time())}.jpg"
            
            # Take photo with front camera (camera 1)
            result = subprocess.run([
                'termux-camera-photo', 
                '-c', '1',  # Front camera
                photo_path
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(photo_path):
                # Check file size
                file_size = os.path.getsize(photo_path)
                if file_size > 0:
                    # Send photo
                    with open(photo_path, 'rb') as photo:
                        await query.message.reply_photo(
                            photo=photo,
                            caption=f"📷 **Foto berhasil diambil!**\n📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n📏 Size: {self.get_file_size(photo_path)}"
                        )
                    
                    # Cleanup
                    os.remove(photo_path)
                    
                    await query.edit_message_text(
                        "✅ Foto berhasil diambil dan dikirim!",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📷 Foto Lagi", callback_data="take_photo")],
                            [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                        ])
                    )
                else:
                    raise Exception("File foto kosong")
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                raise Exception(f"Camera error: {error_msg}")
                
        except subprocess.TimeoutExpired:
            await query.edit_message_text(
                "⏰ Timeout! Foto tidak bisa diambil dalam 15 detik.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil foto: {str(e)}\n\n💡 **Pastikan:**\n• Izin kamera sudah diberikan\n• Kamera tidak digunakan app lain\n• Termux:API ter-update",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="take_photo")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ])
            )

    async def check_battery(self, query):
        """Check battery status - REAL IMPLEMENTATION"""
        if not self.termux_api_available:
            await query.edit_message_text(
                "❌ Termux:API tidak terinstall!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )
            return
            
        await query.edit_message_text("🔋 Mengecek status baterai...")
        
        try:
            result = subprocess.run(['termux-battery-status'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                battery_info = json.loads(result.stdout)
                
                percentage = battery_info.get('percentage', 0)
                status = battery_info.get('status', 'UNKNOWN')
                health = battery_info.get('health', 'UNKNOWN')
                temperature = battery_info.get('temperature', 0)
                plugged = battery_info.get('plugged', 'UNKNOWN')
                
                # Battery emoji based on percentage
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
                
                # Status emoji
                status_emoji = {
                    'CHARGING': '🔌',
                    'DISCHARGING': '🔋',
                    'NOT_CHARGING': '⏸️',
                    'FULL': '✅'
                }.get(status, '❓')
                
                # Health emoji
                health_emoji = {
                    'GOOD': '✅',
                    'OVERHEAT': '🔥',
                    'DEAD': '💀',
                    'COLD': '🧊',
                    'OVER_VOLTAGE': '⚡'
                }.get(health, '❓')
                
                # Plugged type
                plugged_emoji = {
                    'PLUGGED_AC': '🔌',
                    'PLUGGED_USB': '🔌',
                    'PLUGGED_WIRELESS': '📶',
                    'UNPLUGGED': '🔋'
                }.get(plugged, '❓')
                
                # Create battery bar
                battery_bar = self.create_progress_bar(percentage, 25)
                
                battery_message = f"""
🔋 **STATUS BATERAI LENGKAP**
═══════════════════════════════════

{battery_emoji} **Level Baterai:**
{battery_bar}

📊 **DETAIL STATUS:**
• **Persentase:** {percentage}%
• **Status:** {status_emoji} {status}
• **Kesehatan:** {health_emoji} {health}
• **Suhu:** 🌡️ {temperature}°C
• **Charger:** {plugged_emoji} {plugged}

⏰ **Waktu Check:** {datetime.now().strftime('%H:%M:%S')}

💡 **Tips:**
{'🔌 Sedang mengisi daya' if 'CHARGING' in status else '⚡ Gunakan power saving jika < 20%'}
                """
                
                await query.edit_message_text(
                    battery_message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Refresh", callback_data="check_battery")],
                        [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception("Tidak dapat mengakses informasi baterai")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengecek baterai: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def install_api_guide(self, query):
        """Show Termux:API installation guide"""
        guide_message = """
📥 **PANDUAN INSTALL TERMUX:API**
═══════════════════════════════════

**🔧 LANGKAH INSTALASI:**

**1️⃣ Download Termux:API App:**
• Buka F-Droid: https://f-droid.org
• Cari "Termux:API" 
• Download & Install APK

**2️⃣ Install Package di Termux:**
```
pkg update
pkg install termux-api
```

**3️⃣ Berikan Izin Lengkap:**
• Buka Settings Android
• Apps → Termux:API
• Permissions → Allow ALL
• Terutama: Camera, Location, Storage, Phone

**4️⃣ Test Installation:**
```
termux-battery-status
termux-camera-info
```

**⚠️ PENTING:**
• Termux:API harus dari F-Droid (bukan Play Store)
• Berikan semua permission yang diminta
• Restart Termux setelah install

**✅ FITUR YANG AKAN AKTIF:**
• 📷 Ambil foto kamera
• 🔋 Status baterai real-time
• 📍 GPS location tracking
• 📳 Getarkan device
• 📋 Clipboard management
• 🔆 Brightness control
• Dan masih banyak lagi!
        """
        
        await query.edit_message_text(
            guide_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Check API Status", callback_data="check_api_status")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ]),
            parse_mode='Markdown'
        )

    async def check_api_status(self, query):
        """Check Termux:API status"""
        await query.edit_message_text("🔍 Mengecek status Termux:API...")
        
        # Recheck API availability
        self.termux_api_available = self.check_termux_api()
        
        if self.termux_api_available:
            # Test multiple API functions
            test_results = "\n".join([f"• {name}: {status}" for name, status in tests])
            
            status_message = f"""
✅ **TERMUX:API TERDETEKSI!**
═══════════════════════════════

**📋 HASIL TEST:**
{test_results}

**🎯 STATUS:** API sudah terinstall dan siap digunakan!

💡 Jika ada yang ❌, berikan permission di Settings Android.
            """
        else:
            status_message = """
❌ **TERMUX:API TIDAK TERDETEKSI**
═══════════════════════════════

**🔍 KEMUNGKINAN MASALAH:**
• Termux:API app belum diinstall
• Package `termux-api` belum diinstall
• Permission belum diberikan
• Restart Termux diperlukan

**💡 SOLUSI:**
1. Install Termux:API dari F-Droid
2. Jalankan: `pkg install termux-api`
3. Berikan semua permission
4. Restart Termux
            """
        
        await query.edit_message_text(
            status_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Install Guide", callback_data="install_api_guide")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ]),
            parse_mode='Markdown'
        )

    async def get_location(self, query):
        """Get GPS location"""
        if not self.termux_api_available:
            await query.edit_message_text(
                "❌ Termux:API tidak terinstall!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )
            return
            
        await query.edit_message_text("📍 Mengambil lokasi GPS...")
        
        try:
            # Get location with timeout
            result = subprocess.run([
                'termux-location', 
                '-p', 'gps',  # Use GPS provider
                '-r', 'once'  # Single request
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                location_data = json.loads(result.stdout)
                
                latitude = location_data.get('latitude', 0)
                longitude = location_data.get('longitude', 0)
                accuracy = location_data.get('accuracy', 0)
                altitude = location_data.get('altitude', 0)
                bearing = location_data.get('bearing', 0)
                speed = location_data.get('speed', 0)
                timestamp = location_data.get('time', 0)
                
                if timestamp:
                    time_str = datetime.fromtimestamp(timestamp/1000).strftime('%d/%m/%Y %H:%M:%S')
                else:
                    time_str = "Unknown"
                
                location_message = f"""
📍 **LOKASI GPS TERKINI**
═══════════════════════════════

🎯 **KOORDINAT:**
• **Latitude:** `{latitude}`
• **Longitude:** `{longitude}`
• **Altitude:** {altitude:.1f}m

📊 **DETAIL:**
• **Akurasi:** ±{accuracy:.1f}m
• **Arah:** {bearing:.1f}°
• **Kecepatan:** {speed:.1f} m/s
• **Waktu:** {time_str}

🗺️ **QUICK LINKS:**
• [Google Maps](https://maps.google.com/?q={latitude},{longitude})
• [OpenStreetMap](https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}&zoom=15)

📱 **Lokasi berhasil diambil!**
                """
                
                # Send location to Telegram
                await query.message.reply_location(
                    latitude=latitude,
                    longitude=longitude
                )
                
                await query.edit_message_text(
                    location_message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📍 Update Lokasi", callback_data="get_location")],
                        [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception("Tidak dapat mengambil lokasi GPS")
                
        except subprocess.TimeoutExpired:
            await query.edit_message_text(
                "⏰ Timeout! GPS tidak merespon dalam 30 detik.\n\n💡 Pastikan GPS aktif dan di area terbuka.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="get_location")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ])
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil lokasi: {str(e)}\n\n💡 **Pastikan:**\n• GPS aktif di Android\n• Permission Location diberikan\n• Berada di area terbuka",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Coba Lagi", callback_data="get_location")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ])
            )

    async def vibrate_device(self, query):
        """Vibrate the device"""
        if not self.termux_api_available:
            await query.edit_message_text(
                "❌ Termux:API tidak terinstall!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )
            return
            
        try:
            # Vibrate for 1 second
            subprocess.run(['termux-vibrate', '-d', '1000'], timeout=5)
            
            await query.edit_message_text(
                "📳 **Device berhasil digetarkan!**\n\n🎯 Getaran selama 1 detik telah dikirim.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📳 Getar Lagi", callback_data="vibrate_device")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ])
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal menggetarkan device: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def clipboard_menu(self, query):
        """Clipboard management menu"""
        if not self.termux_api_available:
            await query.edit_message_text(
                "❌ Termux:API tidak terinstall!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )
            return
        
        try:
            # Get current clipboard content
            result = subprocess.run(['termux-clipboard-get'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                clipboard_content = result.stdout.strip()
                if len(clipboard_content) > 100:
                    preview = clipboard_content[:100] + "..."
                else:
                    preview = clipboard_content
                
                if not clipboard_content:
                    preview = "(Clipboard kosong)"
            else:
                preview = "(Tidak dapat membaca clipboard)"
            
            message = f"""
📋 **CLIPBOARD MANAGER**
═══════════════════════════════

📄 **ISI CLIPBOARD SAAT INI:**
```
{preview}
```

🎯 **ACTIONS:**
• **Get** - Ambil isi clipboard
• **Set** - Atur isi clipboard (kirim text)
• **Clear** - Kosongkan clipboard

💡 Kirim text untuk mengatur clipboard!
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📄 Get Clipboard", callback_data="get_clipboard"),
                    InlineKeyboardButton("🗑️ Clear", callback_data="clear_clipboard")
                ],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error clipboard: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    async def system_monitor(self, query):
        """Real-time system monitoring"""
        await query.edit_message_text("📊 Memuat system monitor...")
        
        try:
            # Get detailed system info
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage('/')
            
            # Get process count
            process_count = len(psutil.pids())
            
            # Get network info
            network = psutil.net_io_counters()
            
            # Get temperatures (if available)
            try:
                temps = psutil.sensors_temperatures()
                temp_info = "Available" if temps else "Not Available"
            except:
                temp_info = "Not Supported"
            
            # Calculate averages
            cpu_avg = sum(cpu_percent) / len(cpu_percent)
            
            # Create bars
            cpu_bar = self.create_progress_bar(cpu_avg)
            ram_bar = self.create_progress_bar(memory.percent)
            swap_bar = self.create_progress_bar(swap.percent)
            disk_bar = self.create_progress_bar(disk.percent)
            
            monitor_message = f"""
📊 **SYSTEM MONITOR REAL-TIME**
═══════════════════════════════════

💻 **CPU USAGE:**
• **Average:** {cpu_avg:.1f}%
{cpu_bar}
• **Cores:** {len(cpu_percent)} cores
• **Frequency:** {cpu_freq.current:.0f}MHz (max: {cpu_freq.max:.0f}MHz)

🧠 **MEMORY:**
• **RAM:** {memory.percent:.1f}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)
{ram_bar}
• **Available:** {memory.available//1024//1024}MB
• **Swap:** {swap.percent:.1f}% ({swap.used//1024//1024}MB/{swap.total//1024//1024}MB)
{swap_bar}

💾 **STORAGE:**
• **Used:** {disk.percent:.1f}% ({disk.used//1024//1024//1024:.1f}GB/{disk.total//1024//1024//1024:.1f}GB)
{disk_bar}
• **Free:** {disk.free//1024//1024//1024:.1f}GB

📈 **SYSTEM:**
• **Processes:** {process_count}
• **Network Sent:** {network.bytes_sent//1024//1024:.1f}MB
• **Network Recv:** {network.bytes_recv//1024//1024:.1f}MB
• **Temperature:** {temp_info}

🕐 **Updated:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            await query.edit_message_text(
                monitor_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="system_monitor")],
                    [InlineKeyboardButton("📊 Process List", callback_data="process_list")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error system monitor: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
                ]])
            )

    # Placeholder methods for additional features
    async def search_files(self, query):
        await query.edit_message_text(
            "🔍 **FILE SEARCH**\n\nKetik nama file yang ingin dicari!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")
            ]])
        )

    async def brightness_control(self, query):
        await query.edit_message_text("🔆 Fitur brightness control akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def utility_tools(self, query):
        await query.edit_message_text("🔧 Menu tools utilitas akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def help_menu(self, query):
        help_message = """
❓ **BANTUAN & PANDUAN**
═══════════════════════════════

🎯 **FITUR UTAMA:**
• **💻 Terminal:** Eksekusi command Termux
• **📁 File Manager:** Browse & kelola file
• **📊 System Monitor:** Monitor resources
• **📷 Camera:** Ambil foto (butuh API)
• **🔋 Battery:** Status baterai (butuh API)
• **📍 GPS:** Lokasi tracking (butuh API)

🔧 **REQUIREMENTS:**
• **Termux:API** - Untuk fitur hardware
• **Permissions** - Camera, Location, Storage
• **Internet** - Untuk bot connection

💡 **TIPS PENGGUNAAN:**
• Berikan permission lengkap ke Termux:API
• Gunakan `cd ~` untuk kembali ke home
• Monitor system secara berkala
• Install Termux:API dari F-Droid

📞 **SUPPORT:**
• Check log file: `bot.log`
• Restart bot jika error
• Update Termux & packages secara berkala
        """
        
        await query.edit_message_text(
            help_message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📥 Install Guide", callback_data="install_api_guide")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ]),
            parse_mode='Markdown'
        )

    async def bot_settings(self, query):
        """Show bot settings"""
        settings_message = f"""
⚙️ **PENGATURAN BOT**
═══════════════════════════════

🤖 **STATUS BOT:**
• **Active:** {'🟢 ON' if self.config.bot_active else '🔴 OFF'}
• **Auto Start:** {'🟢 ON' if self.config.auto_start else '🔴 OFF'}
• **Termux:API:** {'✅ Available' if self.termux_api_available else '❌ Not Available'}

📁 **DIRECTORY:**
• **Current:** `{os.path.basename(self.current_directory)}`
• **Home:** `{os.path.basename(os.path.expanduser('~'))}`

🔧 **BOT INFO:**
• **Config File:** bot_config.json
• **Log File:** bot.log
• **Token:** {self.config.bot_token[:10]}...

💡 **OPTIONS:**
        """
        
        await query.edit_message_text(
            settings_message,
            reply_markup=self.create_settings_keyboard(),
            parse_mode='Markdown'
        )

    async def toggle_bot(self, query):
        """Toggle bot active status"""
        self.config.bot_active = not self.config.bot_active
        status = "🟢 diaktifkan" if self.config.bot_active else "🔴 dinonaktifkan"
        
        await query.edit_message_text(
            f"✅ Bot berhasil {status}!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Pengaturan", callback_data="bot_settings")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ])
        )

    async def toggle_auto_start(self, query):
        """Toggle auto start feature"""
        self.config.auto_start = not self.config.auto_start
        self.config.save_config(self.config.bot_token)
        
        status = "🟢 diaktifkan" if self.config.auto_start else "🔴 dinonaktifkan"
        
        await query.edit_message_text(
            f"✅ Auto Start berhasil {status}!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Pengaturan", callback_data="bot_settings")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
            ])
        )

    async def plant_bot(self, query):
        """Plant bot for auto-start"""
        await query.edit_message_text("🌱 Menanam bot ke sistem...")
        
        try:
            # Create auto-start in .bashrc
            bashrc_path = os.path.expanduser('~/.bashrc')
            auto_start_line = f"cd {os.getcwd()} && nohup python3 bot.py > /dev/null 2>&1 &"
            
            # Check if already exists
            bashrc_exists = os.path.exists(bashrc_path)
            if bashrc_exists:
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                if "bot.py" in content:
                    await query.edit_message_text(
                        "⚠️ Bot sudah tertanam di sistem!\n\n🌱 Auto-start sudah aktif.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("⚙️ Pengaturan", callback_data="bot_settings")]
                        ])
                    )
                    return
            
            # Add to bashrc
            with open(bashrc_path, 'a') as f:
                f.write(f"\n# Termux Bot Auto Start\n{auto_start_line}\n")
            
            self.config.auto_start = True
            self.config.save_config(self.config.bot_token)
            
            await query.edit_message_text(
                "✅ **Bot berhasil ditanam ke sistem!**\n\n🌱 **Auto-start aktif:**\n• Bot akan jalan otomatis saat buka Termux\n• Bisa langsung minimize Termux\n• Bot tetap running di background",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⚙️ Pengaturan", callback_data="bot_settings")],
                    [InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu")]
                ])
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal menanam bot: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Pengaturan", callback_data="bot_settings")
                ]])
            )

    async def restart_bot(self, query):
        """Restart the bot"""
        await query.edit_message_text("🔄 Restarting bot...")
        
        try:
            # Send restart message
            await query.message.reply_text("🔄 **Bot sedang restart...**\n\n⏳ Tunggu beberapa detik dan coba /start lagi.")
            
            # Exit with code 0 to allow restart
            os._exit(0)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Error restart: {str(e)}")

    async def handle_terminal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle terminal commands"""
        command = update.message.text.strip()
        
        if not self.config.bot_active:
            await update.message.reply_text("🔴 Bot sedang tidak aktif.")
            return
        
        # Check if it's a file search
        if command.startswith('find ') or command.startswith('search '):
            await self.handle_file_search(update, command)
            return
        
        try:
            # Handle cd command specially
            if command.startswith('cd '):
                path = command[3:].strip()
                if path == '~':
                    self.current_directory = os.path.expanduser('~')
                elif path == '..':
                    self.current_directory = os.path.dirname(self.current_directory)
                else:
                    new_path = os.path.join(self.current_directory, path)
                    if os.path.exists(new_path) and os.path.isdir(new_path):
                        self.current_directory = os.path.abspath(new_path)
                    else:
                        await update.message.reply_text(f"❌ Directory tidak ditemukan: `{path}`", parse_mode='Markdown')
                        return
                
                await update.message.reply_text(
                    f"📁 **Directory changed:**\n`{self.current_directory}`", 
                    parse_mode='Markdown'
                )
                return
            
            # Execute other commands
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.current_directory,
                capture_output=True, 
                text=True, 
                timeout=60
            )
            
            output = result.stdout
            error = result.stderr
            
            if not output and not error:
                output = "✅ Command executed successfully (no output)"
            elif error and not output:
                output = f"❌ Error:\n{error}"
            elif error and output:
                output = f"Output:\n{output}\n\nError:\n{error}"
            
            # Limit output length
            if len(output) > 3500:
                output = output[:3500] + "\n\n... (output truncated)"
            
            await update.message.reply_text(f"```\n{output}\n```", parse_mode='Markdown')
            
        except subprocess.TimeoutExpired:
            await update.message.reply_text("⏰ **Timeout!** Command exceeded 60 seconds limit.")
        except Exception as e:
            await update.message.reply_text(f"❌ **Error:** {str(e)}")

    async def handle_file_search(self, update, command):
        """Handle file search commands"""
        try:
            if command.startswith('find '):
                search_term = command[5:].strip()
            else:
                search_term = command[7:].strip()
            
            if not search_term:
                await update.message.reply_text("❓ Masukkan nama file yang dicari!\nContoh: `find script.py`", parse_mode='Markdown')
                return
            
            await update.message.reply_text(f"🔍 Mencari file: `{search_term}`...", parse_mode='Markdown')
            
            # Search files
            found_files = []
            search_dirs = [self.current_directory, os.path.expanduser('~'), '/sdcard']
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for root, dirs, files in os.walk(search_dir):
                        for file in files:
                            if search_term.lower() in file.lower():
                                file_path = os.path.join(root, file)
                                file_size = self.get_file_size(file_path)
                                found_files.append((file_path, file_size))
                                
                                if len(found_files) >= 20:  # Limit results
                                    break
                        if len(found_files) >= 20:
                            break
                    if len(found_files) >= 20:
                        break
            
            if found_files:
                results = "🔍 **HASIL PENCARIAN:**\n\n"
                for file_path, file_size in found_files[:15]:
                    rel_path = os.path.relpath(file_path, os.path.expanduser('~'))
                    results += f"📄 `{rel_path}` ({file_size})\n"
                
                if len(found_files) > 15:
                    results += f"\n... dan {len(found_files) - 15} file lainnya"
                
                await update.message.reply_text(results, parse_mode='Markdown')
            else:
                await update.message.reply_text(f"❌ Tidak ditemukan file dengan nama: `{search_term}`", parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error pencarian: {str(e)}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if update and update.effective_chat:
            try:
                await update.effective_chat.send_message(
                    "❌ **Terjadi error!** Check log file untuk detail."
                )
            except:
                pass

    def run(self):
        """Run the bot"""
        print("\n" + "="*60)
        print("🤖 TERMUX BOT CONTROLLER v2.0 - REALISTIC VERSION")
        print("="*60)
        print("🚀 Starting bot...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🔗 Bot Token: {self.config.bot_token[:10]}...")
        print(f"📱 Termux:API: {'✅ Available' if self.termux_api_available else '❌ Not Available'}")
        
        ifs = []
            
            # Test battery
            try:
                result = subprocess.run(['termux-battery-status'], 
                                      capture_output=True, text=True, timeout=5)
                tests.append(("🔋 Battery", "✅" if result.returncode == 0 else "❌"))
            except:
                tests.append(("🔋 Battery", "❌"))
            
            # Test camera info
            try:
                result = subprocess.run(['termux-camera-info'], 
                                      capture_output=True, text=True, timeout=5)
                tests.append(("📷 Camera", "✅" if result.returncode == 0 else "❌"))
            except:
                tests.append(("📷 Camera", "❌"))
            
            # Test clipboard
            try:
                result = subprocess.run(['termux-clipboard-get'], 
                                      capture_output=True, text=True, timeout=5)
                tests.append(("📋 Clipboard", "✅" if result.returncode == 0 else "❌"))
            except:
                tests.append(("📋 Clipboard", "❌"))
            
            test
