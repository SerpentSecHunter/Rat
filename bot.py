#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Termux Control Bot - BOT.PY
Bot Telegram untuk kontrol penuh Termux
PERINGATAN: Jangan ubah nama file ini dari bot.py!
"""

import os
import sys
import subprocess
import json
import glob
from pathlib import Path
import asyncio
import logging
from datetime import datetime
import shutil
import psutil

# Auto install dependencies
def install_package(package):
    """Install package jika belum ada"""
    try:
        __import__(package)
        return True
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True

# Install required packages
required_packages = [
    "python-telegram-bot",
    "python-dotenv",
    "pillow",
    "psutil"
]

for package in required_packages:
    if package == "python-telegram-bot":
        try:
            import telegram
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot[all]"])
    else:
        install_package(package)

# Import after installation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

# Security check - prevent script renaming
current_script = os.path.basename(__file__)
if current_script != "bot.py":
    print("CRITICAL ERROR: Script name has been changed!")
    print("This script must be named 'bot.py' for security reasons.")
    print("Deleting compromised file...")
    try:
        os.remove(__file__)
        print("File deleted for security.")
    except:
        pass
    sys.exit(1)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("USER_ID")) if os.getenv("USER_ID") else None

if not BOT_TOKEN or not AUTHORIZED_USER_ID:
    print("ERROR: BOT_TOKEN dan USER_ID harus diset di file .env")
    print("Buat file .env dengan format:")
    print("BOT_TOKEN=your_bot_token_here")
    print("USER_ID=your_telegram_user_id")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_authorized(user_id):
    """Check if user is authorized"""
    return user_id == AUTHORIZED_USER_ID

def run_termux_command(command):
    """Execute termux command"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else result.stderr
    except subprocess.TimeoutExpired:
        return "Command timeout (30s)"
    except Exception as e:
        return f"Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized access!")
        return
    
    keyboard = [
        [InlineKeyboardButton("📱 Open Apps", callback_data="apps")],
        [InlineKeyboardButton("🔦 Flashlight", callback_data="flashlight")],
        [InlineKeyboardButton("📩 Notifications", callback_data="notifications")],
        [InlineKeyboardButton("📍 GPS Location", callback_data="gps")],
        [InlineKeyboardButton("💻 System Info", callback_data="sysinfo")],
        [InlineKeyboardButton("📸 Media Files", callback_data="media")],
        [InlineKeyboardButton("🔊 Text to Speech", callback_data="tts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *Termux Control Bot*\n\n"
        "Pilih fitur yang ingin digunakan:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if not is_authorized(query.from_user.id):
        await query.edit_message_text("❌ Unauthorized access!")
        return
    
    data = query.data
    
    if data == "apps":
        await show_apps_menu(query)
    elif data == "flashlight":
        await show_flashlight_menu(query)
    elif data == "notifications":
        await show_notifications_menu(query)
    elif data == "gps":
        await get_location(query)
    elif data == "sysinfo":
        await show_system_info(query)
    elif data == "media":
        await show_media_menu(query)
    elif data == "tts":
        await show_tts_menu(query)
    elif data.startswith("app_"):
        await open_app(query, data[4:])
    elif data == "flash_on":
        await toggle_flashlight(query, True)
    elif data == "flash_off":
        await toggle_flashlight(query, False)
    elif data.startswith("notif_"):
        await get_notifications(query, data[6:])
    elif data == "media_getall":
        await get_all_media(query)
    elif data.startswith("media_get_"):
        await get_single_media(query, data[10:])
    elif data == "back_main":
        await show_main_menu(query)

async def show_apps_menu(query):
    """Show apps menu"""
    # Apps yang dapat dibuka dengan termux-open-url
    apps = [
        ("TikTok", "tiktok"),
        ("WhatsApp", "whatsapp"),
        ("Instagram", "instagram"), 
        ("Facebook", "facebook"),
        ("YouTube", "youtube"),
        ("Chrome", "chrome"),
        ("Gallery", "gallery"),
        ("Camera", "camera")
    ]
    
    keyboard = []
    for app_name, app_id in apps:
        keyboard.append([InlineKeyboardButton(f"📱 {app_name}", callback_data=f"app_{app_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📱 *Open Applications*\n\n"
        "Pilih aplikasi yang ingin dibuka:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def open_app(query, app_id):
    """Open application"""
    app_commands = {
        "tiktok": "am start -n com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity",
        "whatsapp": "am start -n com.whatsapp/com.whatsapp.HomeActivity", 
        "instagram": "am start -n com.instagram.android/com.instagram.mainactivity.MainActivity",
        "facebook": "am start -n com.facebook.katana/com.facebook.katana.LoginActivity",
        "youtube": "am start -n com.google.android.youtube/com.google.android.youtube.HomeActivity",
        "chrome": "am start -n com.android.chrome/com.google.android.apps.chrome.Main",
        "gallery": "am start -a android.intent.action.VIEW -t image/*",
        "camera": "am start -a android.media.action.IMAGE_CAPTURE"
    }
    
    if app_id in app_commands:
        result = run_termux_command(app_commands[app_id])
        await query.edit_message_text(
            f"📱 *Opening {app_id.title()}*\n\n"
            f"Status: {'✅ Success' if 'Error' not in result else '❌ Failed'}\n"
            f"Output: `{result}`",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ App not supported")

async def show_flashlight_menu(query):
    """Show flashlight menu"""
    keyboard = [
        [InlineKeyboardButton("🔦 Turn ON", callback_data="flash_on")],
        [InlineKeyboardButton("⚫ Turn OFF", callback_data="flash_off")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔦 *Flashlight Control*\n\n"
        "Kontrol senter perangkat:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def toggle_flashlight(query, state):
    """Toggle flashlight on/off"""
    command = "termux-torch on" if state else "termux-torch off"
    result = run_termux_command(command)
    
    status = "🔦 ON" if state else "⚫ OFF"
    await query.edit_message_text(
        f"🔦 *Flashlight {status}*\n\n"
        f"Status: {'✅ Success' if not result or 'Error' not in result else '❌ Failed'}\n"
        f"Output: `{result if result else 'Command executed'}`",
        parse_mode='Markdown'
    )

async def show_notifications_menu(query):
    """Show notifications menu"""
    keyboard = [
        [InlineKeyboardButton("📱 All Notifications", callback_data="notif_all")],
        [InlineKeyboardButton("💬 WhatsApp", callback_data="notif_whatsapp")],
        [InlineKeyboardButton("📧 SMS", callback_data="notif_sms")],
        [InlineKeyboardButton("📞 Calls", callback_data="notif_calls")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📩 *Notifications*\n\n"
        "Pilih jenis notifikasi:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def get_notifications(query, notif_type):
    """Get notifications"""
    if notif_type == "all":
        command = "termux-notification-list"
    elif notif_type == "whatsapp":
        command = "termux-notification-list | grep 'com.whatsapp'"
    elif notif_type == "sms":
        command = "termux-notification-list | grep 'com.android.mms'"
    elif notif_type == "calls":
        command = "termux-notification-list | grep 'com.android.dialer'"
    
    result = run_termux_command(command)
    
    await query.edit_message_text(
        f"📩 *Notifications - {notif_type.title()}*\n\n"
        f"```\n{result if result else 'No notifications found'}\n```",
        parse_mode='Markdown'
    )

async def get_location(query):
    """Get GPS location"""
    await query.edit_message_text("📍 Getting GPS location...")
    
    result = run_termux_command("termux-location -p gps")
    
    try:
        location_data = json.loads(result)
        latitude = location_data.get('latitude', 'N/A')
        longitude = location_data.get('longitude', 'N/A')
        accuracy = location_data.get('accuracy', 'N/A')
        
        maps_url = f"https://maps.google.com/?q={latitude},{longitude}"
        
        await query.edit_message_text(
            f"📍 *GPS Location*\n\n"
            f"🌐 Latitude: `{latitude}`\n"
            f"🌐 Longitude: `{longitude}`\n"
            f"🎯 Accuracy: `{accuracy}m`\n\n"
            f"🗺️ [View on Google Maps]({maps_url})",
            parse_mode='Markdown'
        )
    except:
        await query.edit_message_text(
            f"📍 *GPS Location*\n\n"
            f"❌ Failed to get location\n"
            f"Error: `{result}`",
            parse_mode='Markdown'
        )

async def show_system_info(query):
    """Show system information"""
    # Get system info
    cpu_info = run_termux_command("cat /proc/cpuinfo | grep 'model name' | head -1")
    memory_info = run_termux_command("free -h")
    storage_info = run_termux_command("df -h")
    battery_info = run_termux_command("termux-battery-status")
    wifi_info = run_termux_command("termux-wifi-connectioninfo")
    
    # Get additional info using psutil
    try:
        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)
        disk_usage = psutil.disk_usage('/')
    except:
        ram_percent = "N/A"
        cpu_percent = "N/A" 
        disk_usage = None
    
    info_text = f"💻 *System Information*\n\n"
    info_text += f"🔧 CPU: `{cpu_info.strip() if cpu_info else 'N/A'}`\n"
    info_text += f"📊 CPU Usage: `{cpu_percent}%`\n"
    info_text += f"🧠 RAM Usage: `{ram_percent}%`\n\n"
    
    if disk_usage:
        total_gb = disk_usage.total / (1024**3)
        used_gb = disk_usage.used / (1024**3) 
        free_gb = disk_usage.free / (1024**3)
        info_text += f"💾 Storage:\n"
        info_text += f"  Total: `{total_gb:.1f} GB`\n"
        info_text += f"  Used: `{used_gb:.1f} GB`\n"
        info_text += f"  Free: `{free_gb:.1f} GB`\n\n"
    
    # Battery info
    try:
        battery_data = json.loads(battery_info)
        battery_level = battery_data.get('percentage', 'N/A')
        battery_temp = battery_data.get('temperature', 'N/A')
        info_text += f"🔋 Battery: `{battery_level}%` (Temp: `{battery_temp}°C`)\n\n"
    except:
        info_text += f"🔋 Battery: `N/A`\n\n"
    
    # WiFi info
    try:
        wifi_data = json.loads(wifi_info)
        wifi_ssid = wifi_data.get('ssid', 'N/A')
        wifi_bssid = wifi_data.get('bssid', 'N/A')
        info_text += f"📶 WiFi: `{wifi_ssid}`\n"
        info_text += f"📡 BSSID: `{wifi_bssid}`"
    except:
        info_text += f"📶 WiFi: `N/A`"
    
    await query.edit_message_text(info_text, parse_mode='Markdown')

async def show_media_menu(query):
    """Show media files menu"""
    keyboard = [
        [InlineKeyboardButton("📸 Get All Media", callback_data="media_getall")],
        [InlineKeyboardButton("🖼️ Get Single Media", callback_data="media_get_single")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📸 *Media Files*\n\n"
        "Kelola file gambar dan video:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def get_all_media(query):
    """Get all media files info"""
    await query.edit_message_text("📸 Scanning media files...")
    
    media_paths = ["/sdcard/DCIM", "/storage/emulated/0/DCIM", "/sdcard/Pictures"]
    media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.3gp']
    
    media_files = []
    
    for path in media_paths:
        if os.path.exists(path):
            for ext in media_extensions:
                files = glob.glob(f"{path}/**/*{ext}", recursive=True)
                files.extend(glob.glob(f"{path}/**/*{ext.upper()}", recursive=True))
                media_files.extend(files)
    
    if not media_files:
        await query.edit_message_text(
            "📸 *Media Files*\n\n"
            "❌ No media files found",
            parse_mode='Markdown'
        )
        return
    
    # Limit to first 20 files
    media_files = media_files[:20]
    
    info_text = f"📸 *Media Files* ({len(media_files)} files)\n\n"
    
    for i, file_path in enumerate(media_files, 1):
        try:
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            file_name = os.path.basename(file_path)
            
            # Get image dimensions if it's an image
            dimensions = ""
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                try:
                    with Image.open(file_path) as img:
                        dimensions = f" ({img.width}x{img.height})"
                except:
                    pass
            
            info_text += f"`{i}.` {file_name}{dimensions}\n"
            info_text += f"   Size: `{file_size_mb:.1f} MB`\n"
            info_text += f"   Path: `{file_path}`\n\n"
            
        except Exception as e:
            info_text += f"`{i}.` Error reading file: `{str(e)}`\n\n"
    
    await query.edit_message_text(info_text, parse_mode='Markdown')

async def show_tts_menu(query):
    """Show TTS menu"""
    await query.edit_message_text(
        "🔊 *Text to Speech*\n\n"
        "Ketik pesan yang ingin diubah menjadi suara.\n"
        "Format: `/tts your message here`",
        parse_mode='Markdown'
    )

async def show_main_menu(query):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("📱 Open Apps", callback_data="apps")],
        [InlineKeyboardButton("🔦 Flashlight", callback_data="flashlight")],
        [InlineKeyboardButton("📩 Notifications", callback_data="notifications")],
        [InlineKeyboardButton("📍 GPS Location", callback_data="gps")],
        [InlineKeyboardButton("💻 System Info", callback_data="sysinfo")],
        [InlineKeyboardButton("📸 Media Files", callback_data="media")],
        [InlineKeyboardButton("🔊 Text to Speech", callback_data="tts")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🤖 *Termux Control Bot*\n\n"
        "Pilih fitur yang ingin digunakan:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TTS command"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized access!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "🔊 *Text to Speech*\n\n"
            "Usage: `/tts your message here`",
            parse_mode='Markdown'
        )
        return
    
    text = " ".join(context.args)
    
    # Use termux-tts-speak
    command = f'termux-tts-speak "{text}"'
    result = run_termux_command(command)
    
    await update.message.reply_text(
        f"🔊 *Text to Speech*\n\n"
        f"Text: `{text}`\n"
        f"Status: {'✅ Playing' if not result or 'Error' not in result else '❌ Failed'}\n"
        f"Output: `{result if result else 'TTS executed'}`",
        parse_mode='Markdown'
    )

async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle custom termux commands"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized access!")
        return
    
    command = update.message.text[1:]  # Remove /
    result = run_termux_command(command)
    
    await update.message.reply_text(
        f"💻 *Command Output*\n\n"
        f"Command: `{command}`\n"
        f"Output:\n```\n{result}\n```",
        parse_mode='Markdown'
    )

def main():
    """Main function"""
    print("🤖 Starting Termux Control Bot...")
    print(f"🔐 Authorized User ID: {AUTHORIZED_USER_ID}")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tts", handle_tts))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Handle unknown commands as termux commands
    application.add_handler(MessageHandler(filters.COMMAND, handle_command))
    
    print("✅ Bot started successfully!")
    print("🚀 Bot is running... Press Ctrl+C to stop")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
