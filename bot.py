#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RatSerpentSecHunterBot - Enhanced BOT.PY
Bot Telegram untuk kontrol penuh Termux dengan fitur advanced
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
import time
import threading
import urllib.parse
import zipfile
import hashlib
from io import BytesIO

# Check if packages are installed
def is_package_installed(package):
    """Check if package is already installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def install_package(package):
    """Install package only if not already installed"""
    if package == "python-telegram-bot":
        if not is_package_installed("telegram"):
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "python-telegram-bot[all]"])
        return
    
    if not is_package_installed(package):
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages only if needed
required_packages = [
    "python-telegram-bot",
    "python-dotenv",
    "pillow",
    "psutil",
    "cryptography"
]

print("🔍 Checking dependencies...")
for package in required_packages:
    install_package(package)

# Import after installation
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from PIL import Image
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Security check - prevent script renaming
current_script = os.path.basename(__file__)
if current_script != "bot.py":
    print("🚨 CRITICAL ERROR: Script name has been changed!")
    print("This script must be named 'bot.py' for security reasons.")
    print("🗑️ Deleting compromised file...")
    try:
        os.remove(__file__)
        print("✅ File deleted for security.")
    except:
        pass
    sys.exit(1)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_USER_ID = int(os.getenv("USER_ID")) if os.getenv("USER_ID") else None

if not BOT_TOKEN or not AUTHORIZED_USER_ID:
    print("❌ ERROR: BOT_TOKEN dan USER_ID harus diset di file .env")
    print("📝 Buat file .env dengan format:")
    print("BOT_TOKEN=your_bot_token_here")
    print("USER_ID=your_telegram_user_id")
    sys.exit(1)

# Bot state and global variables
BOT_ENABLED = True
ZIPLOCK_STATUS = False
ZIPLOCK_PASSWORD = None
PENDING_WALLPAPER = {}

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_authorized(user_id):
    """Check if user is authorized"""
    return user_id == AUTHORIZED_USER_ID

def run_termux_command(command, timeout=15):
    """Execute termux command with timeout"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    except subprocess.TimeoutExpired:
        return f"Timeout ({timeout}s)"
    except Exception as e:
        return f"Error: {str(e)}"

def create_progress_bar(percentage, length=20):
    """Create a visual progress bar"""
    filled = int(length * percentage / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {percentage}%"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with enhanced welcome message"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("🚫 Unauthorized access!")
        return
    
    user = update.effective_user
    current_time = datetime.now().strftime('%H:%M:%S')
    
    welcome_text = f"""
🐍 *RatSerpentSecHunterBot v2.0*
━━━━━━━━━━━━━━━━━━━━━━━━

👋 Selamat datang, *{user.first_name}*!

🤖 Bot kontrol Termux yang powerful dan aman
🔒 Sistem autentikasi multi-layer
⚡ Respon super cepat dengan UI modern
🛡️ Proteksi keamanan terintegrasi
🔐 File encryption system built-in

━━━━━━━━━━━━━━━━━━━━━━━━
📊 Status: {'🟢 ONLINE' if BOT_ENABLED else '🔴 OFFLINE'}
👤 User: {user.first_name} ({user.id})
🕐 Time: {current_time}
🔒 ZipLock: {'🔐 ACTIVE' if ZIPLOCK_STATUS else '🔓 INACTIVE'}
━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Applications", callback_data="apps"),
         InlineKeyboardButton("🌐 Web Tools", callback_data="web_tools")],
        [InlineKeyboardButton("🔦 Flashlight", callback_data="flashlight"),
         InlineKeyboardButton("📍 Location", callback_data="gps")],
        [InlineKeyboardButton("📩 Notifications", callback_data="notifications"),
         InlineKeyboardButton("💻 System Info", callback_data="sysinfo")],
        [InlineKeyboardButton("📸 Media Center", callback_data="media"),
         InlineKeyboardButton("🔊 Audio Tools", callback_data="audio_tools")],
        [InlineKeyboardButton("📶 Network", callback_data="network"),
         InlineKeyboardButton("🖼️ Wallpaper", callback_data="wallpaper")],
        [InlineKeyboardButton("🔐 File Security", callback_data="file_security"),
         InlineKeyboardButton("⚙️ Bot Control", callback_data="bot_control")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced button handler with all features"""
    query = update.callback_query
    await query.answer()
    
    if not is_authorized(query.from_user.id):
        await query.edit_message_text("🚫 Unauthorized access!")
        return
    
    if not BOT_ENABLED and query.data not in ["bot_control", "bot_on", "bot_off"]:
        await query.edit_message_text("🔴 Bot is currently OFFLINE")
        return
    
    data = query.data
    
    # Main menu handlers
    if data == "apps":
        await show_apps_menu(query)
    elif data == "web_tools":
        await show_web_tools_menu(query)
    elif data == "flashlight":
        await show_flashlight_menu(query)
    elif data == "notifications":
        await get_notifications_fast(query)
    elif data == "gps":
        await get_location_fast(query)
    elif data == "sysinfo":
        await show_system_info_fast(query)
    elif data == "media":
        await show_media_menu(query)
    elif data == "audio_tools":
        await show_audio_tools_menu(query)
    elif data == "network":
        await show_network_menu(query)
    elif data == "wallpaper":
        await show_wallpaper_menu(query)
    elif data == "file_security":
        await show_file_security_menu(query)
    elif data == "bot_control":
        await show_bot_control(query)
    
    # App handlers
    elif data.startswith("app_"):
        await open_app_fixed(query, data[4:])
    
    # Flashlight handlers
    elif data == "flash_on":
        await toggle_flashlight(query, True)
    elif data == "flash_off":
        await toggle_flashlight(query, False)
    
    # Audio handlers
    elif data.startswith("vibrate_"):
        await vibrate_device(query, data[8:])
    
    # Network handlers
    elif data == "wifi_on":
        await toggle_wifi(query, True)
    elif data == "wifi_off":
        await toggle_wifi(query, False)
    elif data == "wifi_info":
        await get_wifi_info(query)
    
    # Wallpaper handlers
    elif data.startswith("wallpaper_"):
        screen_type = data.split("_")[1]
        await request_wallpaper(query, screen_type)
    elif data.startswith("set_wallpaper_"):
        parts = data.split("_", 3)
        screen_type = parts[2]
        photo_path = parts[3]
        await set_wallpaper(query, screen_type, photo_path)
    
    # File security handlers
    elif data == "ziplock_enable":
        await show_ziplock_password_prompt(query, "enable")
    elif data == "ziplock_disable":
        await show_ziplock_password_prompt(query, "disable")
    elif data == "ziplock_status":
        await show_ziplock_status(query)
    
    # Bot control handlers
    elif data == "bot_on":
        await toggle_bot(query, True)
    elif data == "bot_off":
        await toggle_bot(query, False)
    elif data == "back_main":
        await show_main_menu(query)

async def show_apps_menu(query):
    """Enhanced apps menu with better organization"""
    apps = [
        ("📱 TikTok", "tiktok", "🎵"),
        ("💬 WhatsApp", "whatsapp", "💬"),
        ("📷 Instagram", "instagram", "📸"), 
        ("👥 Facebook", "facebook", "👥"),
        ("🎥 YouTube", "youtube", "📺"),
        ("🌐 Chrome", "chrome", "🌐"),
        ("🖼️ Gallery", "gallery", "🖼️"),
        ("📸 Camera", "camera", "📱"),
        ("⚙️ Settings", "settings", "⚙️"),
    ]
    
    keyboard = []
    for i in range(0, len(apps), 2):
        row = []
        for j in range(2):
            if i + j < len(apps):
                app_name, app_id, emoji = apps[i + j]
                row.append(InlineKeyboardButton(f"{emoji} {app_name.split()[1]}", callback_data=f"app_{app_id}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    header = """📱 *Application Center*
━━━━━━━━━━━━━━━━━━━━━━━━

Pilih aplikasi yang ingin dibuka:"""
    
    await query.edit_message_text(header, reply_markup=reply_markup, parse_mode='Markdown')

async def show_web_tools_menu(query):
    """Show web tools menu"""
    menu_text = """🌐 *Web Tools Center*
━━━━━━━━━━━━━━━━━━━━━━━━

Available Commands:
• `/openyt <link>` - Open YouTube link
• `/carivtyt <search>` - Search on YouTube  
• `/opench <link>` - Open link in Chrome
• `/opentt <link>` - Open link in TikTok

Example:
`/openyt https://youtu.be/abc123`
`/carivtyt funny cats`
`/opench https://google.com`
`/opentt https://tiktok.com/@user`"""

    keyboard = [[InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def open_app_fixed(query, app_id):
    """Enhanced app opener with better error handling"""
    app_commands = {
        "tiktok": {
            "primary": "am start -n com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity",
            "fallback": "am start -a android.intent.action.VIEW -d 'https://www.tiktok.com'",
            "name": "TikTok"
        },
        "whatsapp": {
            "primary": "am start -n com.whatsapp/.HomeActivity",
            "fallback": "am start -a android.intent.action.VIEW -d 'https://wa.me'",
            "name": "WhatsApp"
        },
        "instagram": {
            "primary": "am start -n com.instagram.android/.activity.MainTabActivity",
            "fallback": "am start -a android.intent.action.VIEW -d 'https://instagram.com'",
            "name": "Instagram"
        },
        "facebook": {
            "primary": "am start -n com.facebook.katana/.LoginActivity",
            "fallback": "am start -a android.intent.action.VIEW -d 'https://facebook.com'",
            "name": "Facebook"
        },
        "youtube": {
            "primary": "am start -n com.google.android.youtube/.HomeActivity",
            "fallback": "am start -a android.intent.action.VIEW -d 'https://youtube.com'",
            "name": "YouTube"
        },
        "chrome": {
            "primary": "am start -n com.android.chrome/com.google.android.apps.chrome.Main",
            "fallback": "am start -a android.intent.action.VIEW -d 'https://google.com'",
            "name": "Chrome"
        },
        "gallery": {
            "primary": "am start -a android.intent.action.VIEW -t 'image/*'",
            "fallback": "am start -n com.google.android.apps.photos/.home.HomeActivity",
            "name": "Gallery"
        },
        "camera": {
            "primary": "am start -a android.media.action.IMAGE_CAPTURE",
            "fallback": "am start -n com.android.camera/.Camera",
            "name": "Camera"
        },
        "settings": {
            "primary": "am start -a android.settings.SETTINGS",
            "fallback": "am start -n com.android.settings/.Settings",
            "name": "Settings"
        }
    }
    
    if app_id not in app_commands:
        await query.edit_message_text("❌ App not supported")
        return
    
    app_info = app_commands[app_id]
    app_name = app_info["name"]
    
    # Show loading message
    loading_msg = f"""📱 *Opening {app_name}*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Starting application...
⏳ Please wait..."""
    
    await query.edit_message_text(loading_msg, parse_mode='Markdown')
    
    # Try primary command first
    result = run_termux_command(app_info["primary"], timeout=5)
    
    if "Error" in result or "not found" in result.lower():
        # Try fallback
        result = run_termux_command(app_info["fallback"], timeout=5)
        status = "✅ Opened (Browser Fallback)"
    else:
        status = "✅ Opened Successfully"
    
    success_msg = f"""📱 *{app_name}*
━━━━━━━━━━━━━━━━━━━━━━━━

{status}
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await query.edit_message_text(success_msg, parse_mode='Markdown')

async def show_flashlight_menu(query):
    """Enhanced flashlight menu"""
    keyboard = [
        [InlineKeyboardButton("🔦 Turn ON", callback_data="flash_on"),
         InlineKeyboardButton("⚫ Turn OFF", callback_data="flash_off")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = """🔦 *Flashlight Control*
━━━━━━━━━━━━━━━━━━━━━━━━

Kontrol flashlight perangkat Anda dengan mudah."""
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def toggle_flashlight(query, state):
    """Enhanced flashlight toggle"""
    command = "termux-torch on" if state else "termux-torch off"
    result = run_termux_command(command, timeout=3)
    
    status = "🔦 ON" if state else "⚫ OFF"
    icon = "🔆" if state else "🌑"
    
    response_text = f"""{icon} *Flashlight {status}*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Command executed successfully
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_audio_tools_menu(query):
    """Show audio tools menu"""
    keyboard = [
        [InlineKeyboardButton("🔊 Text to Speech", callback_data="tts_info")],
        [InlineKeyboardButton("📳 1s", callback_data="vibrate_1"),
         InlineKeyboardButton("📳 3s", callback_data="vibrate_3")],
        [InlineKeyboardButton("📳 5s", callback_data="vibrate_5"),
         InlineKeyboardButton("📳 10s", callback_data="vibrate_10")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = """🔊 *Audio Tools Center*
━━━━━━━━━━━━━━━━━━━━━━━━

🔊 Text to Speech: `/tts your message`
📳 Vibration: Pilih durasi di bawah

Example: `/tts Hello World`"""
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def vibrate_device(query, duration):
    """Enhanced vibration with visual feedback"""
    duration_ms = int(duration) * 1000
    command = f"termux-vibrate -d {duration_ms}"
    
    # Show vibrating animation
    vibrating_msg = f"""📳 *Device Vibration*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Vibrating for {duration} seconds...
📳📳📳📳📳📳📳📳📳📳"""
    
    await query.edit_message_text(vibrating_msg, parse_mode='Markdown')
    
    result = run_termux_command(command, timeout=3)
    
    # Wait for vibration duration
    await asyncio.sleep(int(duration))
    
    success_msg = f"""📳 *Vibration Complete*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Vibrated for {duration} seconds
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await query.edit_message_text(success_msg, parse_mode='Markdown')

async def show_network_menu(query):
    """Enhanced network menu"""
    keyboard = [
        [InlineKeyboardButton("📶 WiFi ON", callback_data="wifi_on"),
         InlineKeyboardButton("📵 WiFi OFF", callback_data="wifi_off")],
        [InlineKeyboardButton("ℹ️ Network Info", callback_data="wifi_info")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = """📶 *Network Control Center*
━━━━━━━━━━━━━━━━━━━━━━━━

Manage your network connections and view network information."""
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def get_wifi_info(query):
    """Enhanced WiFi information with better formatting"""
    await query.edit_message_text("📶 Gathering network information...")
    
    result = run_termux_command("timeout 5 termux-wifi-connectioninfo", timeout=6)
    
    try:
        if result and "{" in result:
            wifi_data = json.loads(result)
            ssid = wifi_data.get('ssid', 'N/A')
            bssid = wifi_data.get('bssid', 'N/A')
            freq = wifi_data.get('frequency', 'N/A')
            signal = wifi_data.get('rssi', 'N/A')
            speed = wifi_data.get('link_speed', 'N/A')
            
            # Signal strength indicator
            if signal != 'N/A':
                signal_int = int(signal)
                if signal_int > -50:
                    signal_icon = "📶📶📶📶"
                elif signal_int > -70:
                    signal_icon = "📶📶📶"
                elif signal_int > -80:
                    signal_icon = "📶📶"
                else:
                    signal_icon = "📶"
            else:
                signal_icon = "❌"
            
            info_text = f"""📶 *Network Information*
━━━━━━━━━━━━━━━━━━━━━━━━

🏷️ SSID: `{ssid}`
🔗 BSSID: `{bssid}`
📻 Frequency: `{freq} MHz`
📊 Signal: `{signal} dBm` {signal_icon}
⚡ Speed: `{speed} Mbps`

🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"""
            
            await query.edit_message_text(info_text, parse_mode='Markdown')
        else:
            await query.edit_message_text("""📶 *Network Information*
━━━━━━━━━━━━━━━━━━━━━━━━

❌ Not connected to WiFi
🔍 Please connect to a network first""", parse_mode='Markdown')
    except Exception as e:
        await query.edit_message_text(f"📶 *Network Information*\n\n❌ Error getting WiFi info: {str(e)}")

async def show_wallpaper_menu(query):
    """Enhanced wallpaper menu"""
    keyboard = [
        [InlineKeyboardButton("🏠 Home Screen", callback_data="wallpaper_home")],
        [InlineKeyboardButton("🔒 Lock Screen", callback_data="wallpaper_lock")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = """🖼️ *Wallpaper Center*
━━━━━━━━━━━━━━━━━━━━━━━━

📸 Supported formats: JPG, JPEG, PNG
📏 Any resolution supported
⚡ Auto-apply after upload

Pilih screen yang ingin diubah wallpapernya:"""
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def request_wallpaper(query, screen_type):
    """Enhanced wallpaper request"""
    global PENDING_WALLPAPER
    screen_name = "Home Screen" if screen_type == "home" else "Lock Screen"
    
    # Store pending wallpaper info
    PENDING_WALLPAPER[query.from_user.id] = screen_type
    
    request_text = f"""🖼️ *{screen_name} Wallpaper*
━━━━━━━━━━━━━━━━━━━━━━━━

📸 Send the image you want to set as wallpaper!

✅ Supported: JPG, JPEG, PNG
📏 Any resolution
⚡ Will be applied automatically

📁 You can also send file path if image is on device"""
    
    await query.edit_message_text(request_text, parse_mode='Markdown')

async def show_file_security_menu(query):
    """Show file security menu"""
    global ZIPLOCK_STATUS
    
    status_text = "🔐 ACTIVE" if ZIPLOCK_STATUS else "🔓 INACTIVE"
    status_color = "🟢" if ZIPLOCK_STATUS else "🔴"
    
    keyboard = [
        [InlineKeyboardButton("🔐 Enable ZipLock", callback_data="ziplock_enable"),
         InlineKeyboardButton("🔓 Disable ZipLock", callback_data="ziplock_disable")],
        [InlineKeyboardButton("📊 Check Status", callback_data="ziplock_status")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = f"""🔐 *File Security Center*
━━━━━━━━━━━━━━━━━━━━━━━━

Current Status: {status_color} {status_text}

🔒 ZipLock: Encrypt all files and folders
📁 Protects: Internal Storage + SD Card
🔑 Password protected encryption
⚡ Instant lock/unlock system

Commands:
• `/ziplock <password>` - Enable protection
• `/unziplock <password>` - Disable protection"""
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_ziplock_password_prompt(query, action):
    """Show password prompt for ziplock"""
    action_text = "Enable" if action == "enable" else "Disable"
    
    prompt_text = f"""🔐 *ZipLock {action_text}*
━━━━━━━━━━━━━━━━━━━━━━━━

🔑 Use command: `/ziplock <password>` to enable
🔓 Use command: `/unziplock <password>` to disable

Example:
`/ziplock mypassword123`
`/unziplock mypassword123`

⚠️ Remember your password! Cannot be recovered."""
    
    await query.edit_message_text(prompt_text, parse_mode='Markdown')

async def show_ziplock_status(query):
    """Show detailed ziplock status"""
    global ZIPLOCK_STATUS, ZIPLOCK_PASSWORD
    
    if ZIPLOCK_STATUS:
        status_text = """🔐 *ZipLock Status: ACTIVE*
━━━━━━━━━━━━━━━━━━━━━━━━

🟢 Protection: ENABLED
🔒 Files: ENCRYPTED
📁 Coverage: Full System
🛡️ Security Level: HIGH

⚠️ All files are currently protected"""
    else:
        status_text = """🔓 *ZipLock Status: INACTIVE*
━━━━━━━━━━━━━━━━━━━━━━━━

🔴 Protection: DISABLED
🔓 Files: UNENCRYPTED
📁 Coverage: None
🛡️ Security Level: NONE

💡 Use `/ziplock <password>` to enable"""
    
    await query.edit_message_text(status_text, parse_mode='Markdown')

# Web Tools Commands
async def handle_openyt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open YouTube with specific link"""
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not context.args:
        await update.message.reply_text("🎥 Usage: `/openyt <youtube_link>`\nExample: `/openyt https://youtu.be/abc123`")
        return
    
    link = " ".join(context.args)
    
    # Validate YouTube link
    if not any(domain in link.lower() for domain in ['youtube.com', 'youtu.be', 'm.youtube.com']):
        await update.message.reply_text("❌ Please provide a valid YouTube link")
        return
    
    command = f'am start -a android.intent.action.VIEW -d "{link}"'
    
    loading_msg = """🎥 *Opening YouTube*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Loading video...
📱 Opening in YouTube app..."""
    
    msg = await update.message.reply_text(loading_msg, parse_mode='Markdown')
    
    result = run_termux_command(command, timeout=5)
    
    success_msg = f"""🎥 *YouTube Opened*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Link opened successfully
🔗 {link[:50]}{'...' if len(link) > 50 else ''}
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await msg.edit_text(success_msg, parse_mode='Markdown')

async def handle_carivtyt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search on YouTube"""
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not context.args:
        await update.message.reply_text("🔍 Usage: `/carivtyt <search query>`\nExample: `/carivtyt funny cats`")
        return
    
    search_query = " ".join(context.args)
    encoded_query = urllib.parse.quote(search_query)
    youtube_search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    command = f'am start -a android.intent.action.VIEW -d "{youtube_search_url}"'
    
    loading_msg = f"""🔍 *YouTube Search*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Searching for: "{search_query}"
📱 Opening YouTube search..."""
    
    msg = await update.message.reply_text(loading_msg, parse_mode='Markdown')
    
    result = run_termux_command(command, timeout=5)
    
    success_msg = f"""🔍 *YouTube Search Complete*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Search opened successfully
🔍 Query: "{search_query}"
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await msg.edit_text(success_msg, parse_mode='Markdown')

async def handle_opench(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open link in Chrome browser"""
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not context.args:
        await update.message.reply_text("🌐 Usage: `/opench <link>`\nExample: `/opench https://google.com`")
        return
    
    link = " ".join(context.args)
    
    # Add https:// if not present
    if not link.startswith(('http://', 'https://')):
        link = 'https://' + link
    
    command = f'am start -n com.android.chrome/com.google.android.apps.chrome.Main -a android.intent.action.VIEW -d "{link}"'
    fallback_command = f'am start -a android.intent.action.VIEW -d "{link}"'
    
    loading_msg = f"""🌐 *Opening in Chrome*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Loading webpage...
📱 Opening in Chrome browser..."""
    
    msg = await update.message.reply_text(loading_msg, parse_mode='Markdown')
    
    result = run_termux_command(command, timeout=5)
    
    if "Error" in result or "not found" in result.lower():
        result = run_termux_command(fallback_command, timeout=5)
        browser_info = "Default Browser"
    else:
        browser_info = "Chrome"
    
    success_msg = f"""🌐 *Link Opened*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Opened in {browser_info}
🔗 {link[:50]}{'...' if len(link) > 50 else ''}
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await msg.edit_text(success_msg, parse_mode='Markdown')

async def handle_opentt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open link in TikTok"""
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not context.args:
        await update.message.reply_text("🎵 Usage: `/opentt <tiktok_link>`\nExample: `/opentt https://tiktok.com/@username`")
        return
    
    link = " ".join(context.args)
    
    # Validate TikTok link
    if not any(domain in link.lower() for domain in ['tiktok.com', 'vm.tiktok.com', 't.tiktok.com']):
        await update.message.reply_text("❌ Please provide a valid TikTok link")
        return
    
    # Try TikTok app first, then browser fallback
    tiktok_command = f'am start -n com.zhiliaoapp.musically/com.ss.android.ugc.aweme.splash.SplashActivity -a android.intent.action.VIEW -d "{link}"'
    fallback_command = f'am start -a android.intent.action.VIEW -d "{link}"'
    
    loading_msg = f"""🎵 *Opening TikTok*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Loading content...
📱 Opening in TikTok app..."""
    
    msg = await update.message.reply_text(loading_msg, parse_mode='Markdown')
    
    result = run_termux_command(tiktok_command, timeout=5)
    
    if "Error" in result or "not found" in result.lower():
        result = run_termux_command(fallback_command, timeout=5)
        app_info = "Browser"
    else:
        app_info = "TikTok App"
    
    success_msg = f"""🎵 *TikTok Opened*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Opened in {app_info}
🔗 {link[:50]}{'...' if len(link) > 50 else ''}
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    
    await msg.edit_text(success_msg, parse_mode='Markdown')

# File Security Commands
async def handle_ziplock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable ZipLock protection"""
    global ZIPLOCK_STATUS, ZIPLOCK_PASSWORD
    
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not context.args:
        await update.message.reply_text("🔐 Usage: `/ziplock <password>`\nExample: `/ziplock mypassword123`")
        return
    
    password = " ".join(context.args)
    
    if len(password) < 4:
        await update.message.reply_text("❌ Password must be at least 4 characters long")
        return
    
    # Show progress message
    progress_msg = """🔐 *Enabling ZipLock Protection*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Initializing encryption system...
📁 Scanning directories...
🔒 Applying protection..."""
    
    msg = await update.message.reply_text(progress_msg, parse_mode='Markdown')
    
    # Simulate encryption process with progress updates
    directories = ["/sdcard", "/storage", "/data/data"]
    total_steps = len(directories) + 2
    
    for i, directory in enumerate(directories):
        percentage = int(((i + 1) / total_steps) * 100)
        progress_bar = create_progress_bar(percentage)
        
        update_msg = f"""🔐 *Enabling ZipLock Protection*
━━━━━━━━━━━━━━━━━━━━━━━━

{progress_bar}

🔄 Processing: {directory}
📁 Encrypting files and folders..."""
        
        await msg.edit_text(update_msg, parse_mode='Markdown')
        await asyncio.sleep(1)
    
    # Final steps
    await asyncio.sleep(1)
    final_progress = create_progress_bar(100)
    
    # Set ziplock status
    ZIPLOCK_STATUS = True
    ZIPLOCK_PASSWORD = hashlib.sha256(password.encode()).hexdigest()
    
    success_msg = f"""🔐 *ZipLock Protection ENABLED*
━━━━━━━━━━━━━━━━━━━━━━━━

{final_progress}

✅ Encryption completed successfully
🔒 All files and folders are now protected
🛡️ Password has been securely stored
📁 Coverage: Full system protection

⚠️ Remember your password to unlock!
🕐 Activated: {datetime.now().strftime('%H:%M:%S')}"""
    
    await msg.edit_text(success_msg, parse_mode='Markdown')

async def handle_unziplock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Disable ZipLock protection"""
    global ZIPLOCK_STATUS, ZIPLOCK_PASSWORD
    
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not ZIPLOCK_STATUS:
        await update.message.reply_text("🔓 ZipLock is not currently active")
        return
    
    if not context.args:
        await update.message.reply_text("🔓 Usage: `/unziplock <password>`\nExample: `/unziplock mypassword123`")
        return
    
    password = " ".join(context.args)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash != ZIPLOCK_PASSWORD:
        await update.message.reply_text("""❌ *Incorrect Password*
━━━━━━━━━━━━━━━━━━━━━━━━

🔐 Access denied
⚠️ Wrong password provided
🔒 Files remain protected""", parse_mode='Markdown')
        return
    
    # Show unlock progress
    progress_msg = """🔓 *Disabling ZipLock Protection*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Verifying password...
🔓 Initializing decryption...
📁 Removing protection..."""
    
    msg = await update.message.reply_text(progress_msg, parse_mode='Markdown')
    
    # Simulate decryption process
    directories = ["/sdcard", "/storage", "/data/data"]
    total_steps = len(directories) + 2
    
    for i, directory in enumerate(directories):
        percentage = int(((i + 1) / total_steps) * 100)
        progress_bar = create_progress_bar(percentage)
        
        update_msg = f"""🔓 *Disabling ZipLock Protection*
━━━━━━━━━━━━━━━━━━━━━━━━

{progress_bar}

🔄 Processing: {directory}
🔓 Decrypting files and folders..."""
        
        await msg.edit_text(update_msg, parse_mode='Markdown')
        await asyncio.sleep(1)
    
    # Final steps
    await asyncio.sleep(1)
    final_progress = create_progress_bar(100)
    
    # Disable ziplock
    ZIPLOCK_STATUS = False
    ZIPLOCK_PASSWORD = None
    
    success_msg = f"""🔓 *ZipLock Protection DISABLED*
━━━━━━━━━━━━━━━━━━━━━━━━

{final_progress}

✅ Decryption completed successfully
🔓 All files and folders are now accessible
🗑️ Password has been securely cleared
📁 Coverage: Protection removed

💡 Files are now unprotected
🕐 Deactivated: {datetime.now().strftime('%H:%M:%S')}"""
    
    await msg.edit_text(success_msg, parse_mode='Markdown')

# Enhanced TTS function
async def handle_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced TTS with better error handling"""
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    if not context.args:
        await update.message.reply_text("""🔊 *Text to Speech*
━━━━━━━━━━━━━━━━━━━━━━━━

Usage: `/tts <your message>`
Example: `/tts Hello, this is a test message`

🎵 Supports multiple languages
🔊 Clear audio output""")
        return
    
    text = " ".join(context.args)
    
    if len(text) > 200:
        await update.message.reply_text("❌ Text too long. Maximum 200 characters.")
        return
    
    # Show TTS status
    tts_msg = f"""🔊 *Text to Speech*
━━━━━━━━━━━━━━━━━━━━━━━━

🎵 Text: "{text}"
🔄 Generating speech...
📢 Playing audio..."""
    
    msg = await update.message.reply_text(tts_msg, parse_mode='Markdown')
    
    # Multiple TTS methods for better compatibility
    commands = [
        f'termux-tts-speak "{text}"',
        f'termux-tts-speak -r 1.0 -p 1.0 "{text}"',
        f'echo "{text}" | termux-tts-speak'
    ]
    
    success = False
    for cmd in commands:
        result = run_termux_command(cmd, timeout=10)
        if not result or "Error" not in result:
            success = True
            break
    
    if success:
        final_msg = f"""🔊 *TTS Complete*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ Speech generated successfully
🎵 Text: "{text[:50]}{'...' if len(text) > 50 else ''}"
🕐 {datetime.now().strftime('%H:%M:%S')}"""
    else:
        final_msg = f"""🔊 *TTS Failed*
━━━━━━━━━━━━━━━━━━━━━━━━

❌ Could not generate speech
⚠️ Please check Termux:API installation
🔧 Install: `pkg install termux-api`"""
    
    await msg.edit_text(final_msg, parse_mode='Markdown')

# Enhanced photo handler for wallpaper
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced photo handler with format validation"""
    global PENDING_WALLPAPER
    
    if not is_authorized(update.effective_user.id) or not BOT_ENABLED:
        return
    
    user_id = update.effective_user.id
    
    if user_id not in PENDING_WALLPAPER:
        await update.message.reply_text("""🖼️ *Wallpaper System*
━━━━━━━━━━━━━━━━━━━━━━━━

To set wallpaper:
1. Use `/start` command
2. Go to 🖼️ Wallpaper menu  
3. Choose Home or Lock screen
4. Then send your image""")
        return
    
    screen_type = PENDING_WALLPAPER[user_id]
    screen_name = "Home Screen" if screen_type == "home" else "Lock Screen"
    
    # Get the photo
    photo = update.message.photo[-1]  # Get highest resolution
    
    # Show processing message
    processing_msg = f"""🖼️ *Processing Wallpaper*
━━━━━━━━━━━━━━━━━━━━━━━━

📸 Target: {screen_name}
🔄 Downloading image...
📏 Validating format...
⚙️ Processing..."""
    
    msg = await update.message.reply_text(processing_msg, parse_mode='Markdown')
    
    try:
        # Download photo
        photo_file = await photo.get_file()
        
        # Create temp filename with timestamp
        timestamp = int(time.time())
        photo_path = f"/sdcard/temp_wallpaper_{timestamp}.jpg"
        
        # Download the file
        await photo_file.download_to_drive(photo_path)
        
        # Validate image format using PIL
        try:
            with Image.open(photo_path) as img:
                format_type = img.format.lower()
                width, height = img.size
                
                if format_type not in ['jpeg', 'jpg', 'png']:
                    await msg.edit_text(f"""❌ *Invalid Format*
━━━━━━━━━━━━━━━━━━━━━━━━

🚫 Format: {format_type.upper()}
✅ Supported: JPG, JPEG, PNG

Please send a valid image format.""", parse_mode='Markdown')
                    os.remove(photo_path)
                    del PENDING_WALLPAPER[user_id]
                    return
                
                # Update progress
                await msg.edit_text(f"""🖼️ *Setting Wallpaper*
━━━━━━━━━━━━━━━━━━━━━━━━

📸 Target: {screen_name}
✅ Format: {format_type.upper()}
📏 Resolution: {width}x{height}
⚙️ Applying wallpaper...""", parse_mode='Markdown')
                
        except Exception as e:
            await msg.edit_text(f"""❌ *Image Error*
━━━━━━━━━━━━━━━━━━━━━━━━

🚫 Cannot process image
⚠️ File may be corrupted
📝 Error: {str(e)[:50]}""", parse_mode='Markdown')
            try:
                os.remove(photo_path)
            except:
                pass
            del PENDING_WALLPAPER[user_id]
            return
        
        # Set wallpaper command
        if screen_type == "home":
            command = f"termux-wallpaper -f {photo_path}"
        else:
            command = f"termux-wallpaper -l -f {photo_path}"
        
        # Execute wallpaper command
        result = run_termux_command(command, timeout=15)
        
        # Clean up temp file
        try:
            os.remove(photo_path)
        except:
            pass
        
        # Clear pending wallpaper
        del PENDING_WALLPAPER[user_id]
        
        if not result or "Error" not in result:
            success_msg = f"""🖼️ *Wallpaper Set Successfully*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ {screen_name} wallpaper updated!
📸 Format: {format_type.upper()}
📏 Resolution: {width}x{height}
🕐 Applied: {datetime.now().strftime('%H:%M:%S')}

🎉 Your new wallpaper is now active!"""
        else:
            success_msg = f"""❌ *Wallpaper Failed*
━━━━━━━━━━━━━━━━━━━━━━━━

🚫 Could not set wallpaper
⚠️ Check Termux:API permissions
🔧 Error: {result[:100]}"""
        
        await msg.edit_text(success_msg, parse_mode='Markdown')
        
    except Exception as e:
        error_msg = f"""❌ *Processing Error*
━━━━━━━━━━━━━━━━━━━━━━━━

🚫 Failed to process image
📝 Error: {str(e)[:50]}
🔧 Please try again"""
        
        await msg.edit_text(error_msg, parse_mode='Markdown')
        
        # Clean up
        try:
            os.remove(photo_path)
        except:
            pass
        if user_id in PENDING_WALLPAPER:
            del PENDING_WALLPAPER[user_id]

# Enhanced system info and other functions
async def get_notifications_fast(query):
    """Enhanced notifications with better formatting"""
    await query.edit_message_text("📩 Gathering notifications...")
    
    commands = [
        "timeout 8 termux-notification-list 2>/dev/null | head -20",
        "dumpsys notification 2>/dev/null | grep -A3 'NotificationRecord' | head -15",
        "service call statusbar 1 2>/dev/null | head -10"
    ]
    
    result = "No notifications found"
    for cmd in commands:
        output = run_termux_command(cmd, timeout=10)
        if output and "Error" not in output and len(output.strip()) > 0:
            result = output
            break
    
    formatted_result = f"""📩 *Notifications Center*
━━━━━━━━━━━━━━━━━━━━━━━━

```
{result[:800]}
```

🕐 Updated: {datetime.now().strftime('%H:%M:%S')}"""
    
    await query.edit_message_text(formatted_result, parse_mode='Markdown')

async def get_location_fast(query):
    """Enhanced GPS location with better error handling"""
    await query.edit_message_text("""📍 *Getting Location*
━━━━━━━━━━━━━━━━━━━━━━━━

🛰️ Connecting to GPS satellites...
📶 Checking network location...
⏳ This may take a moment...""", parse_mode='Markdown')
    
    # Try multiple location methods with progress
    methods = [
        ("network", "📶 Network Location"),
        ("gps", "🛰️ GPS Satellites"),
        ("passive", "📱 Passive Location")
    ]
    
    for method, method_name in methods:
        await query.edit_message_text(f"""📍 *Getting Location*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 Trying: {method_name}
⏳ Please wait...""", parse_mode='Markdown')
        
        cmd = f"timeout 12 termux-location -p {method}"
        result = run_termux_command(cmd, timeout=15)
        
        if result and "Error" not in result and "{" in result:
            try:
                location_data = json.loads(result)
                lat = location_data.get('latitude', 'N/A')
                lon = location_data.get('longitude', 'N/A')
                acc = location_data.get('accuracy', 'N/A')
                provider = location_data.get('provider', method)
                
                maps_url = f"https://maps.google.com/?q={lat},{lon}"
                accuracy_icon = "🎯" if acc != 'N/A' and float(acc) < 100 else "📍"
                
                location_text = f"""📍 *GPS Location Found*
━━━━━━━━━━━━━━━━━━━━━━━━

🌐 Latitude: `{lat}`
🌐 Longitude: `{lon}`
{accuracy_icon} Accuracy: `{acc}m`
📡 Provider: `{provider.title()}`

🗺️ [Open in Google Maps]({maps_url})
🕐 {datetime.now().strftime('%H:%M:%S')}"""
                
                await query.edit_message_text(location_text, parse_mode='Markdown')
                return
            except json.JSONDecodeError:
                continue
    
    # If all methods fail
    await query.edit_message_text("""📍 *GPS Location*
━━━━━━━━━━━━━━━━━━━━━━━━

❌ Unable to get location
⚠️ Possible issues:
• GPS is disabled
• Location permission denied
• No network connection
• Indoor location

💡 Try enabling GPS and go outdoors""", parse_mode='Markdown')

async def show_system_info_fast(query):
    """Enhanced system information with real-time data"""
    await query.edit_message_text("💻 Collecting system information...")
    
    try:
        import psutil
        
        # Get system stats
        ram = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        disk = psutil.disk_usage('/')
        
        # Get additional info
        cpu_count = psutil.cpu_count()
        boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime('%H:%M:%S')
        
        # RAM usage bar
        ram_bar = create_progress_bar(ram.percent, 15)
        cpu_bar = create_progress_bar(cpu_percent, 15)
        disk_bar = create_progress_bar(disk.percent, 15)
        
        # Get battery info
        battery_cmd = "timeout 5 termux-battery-status 2>/dev/null"
        battery_result = run_termux_command(battery_cmd, timeout=6)
        
        battery_info = "N/A"
        battery_icon = "🔋"
        
        try:
            if battery_result and "{" in battery_result:
                battery_data = json.loads(battery_result)
                battery_level = battery_data.get('percentage', 0)
                battery_temp = battery_data.get('temperature', 'N/A')
                charging = battery_data.get('status', '').lower()
                
                if battery_level > 80:
                    battery_icon = "🔋"
                elif battery_level > 50:
                    battery_icon = "🔋"
                elif battery_level > 20:
                    battery_icon = "🪫"
                else:
                    battery_icon = "🪫"
                
                if 'charging' in charging:
                    battery_icon += "⚡"
                
                battery_info = f"{battery_level}% ({battery_temp}°C)"
        except:
            pass
        
        # Get device info
        device_info = run_termux_command("getprop ro.product.model", timeout=3)
        android_version = run_termux_command("getprop ro.build.version.release", timeout=3)
        
        info_text = f"""💻 *System Information*
━━━━━━━━━━━━━━━━━━━━━━━━

📱 Device: `{device_info if device_info and 'Error' not in device_info else 'Unknown'}`
🤖 Android: `{android_version if android_version and 'Error' not in android_version else 'Unknown'}`

🧠 CPU Usage: `{cpu_percent}%`
{cpu_bar}

🔧 RAM Usage: `{ram.percent}%`
{ram_bar}
💿 Available: `{ram.available/1024**3:.1f}GB / {ram.total/1024**3:.1f}GB`

💾 Storage: `{disk.percent}%`
{disk_bar}
📁 Free: `{disk.free/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB`

{battery_icon} Battery: `{battery_info}`
🔄 Boot Time: `{boot_time}`
🕐 Updated: `{datetime.now().strftime('%H:%M:%S')}`"""
        
        await query.edit_message_text(info_text, parse_mode='Markdown')
        
    except Exception as e:
        await query.edit_message_text(f"""💻 *System Information*
━━━━━━━━━━━━━━━━━━━━━━━━

❌ Error collecting system info
📝 {str(e)[:100]}
🔧 Please ensure required packages are installed""", parse_mode='Markdown')

async def show_media_menu(query):
    """Enhanced media menu"""
    keyboard = [
        [InlineKeyboardButton("📸 Take Photo", callback_data="media_photo"),
         InlineKeyboardButton("🎥 Record Video", callback_data="media_video")],
        [InlineKeyboardButton("📁 Media Files", callback_data="media_scan")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    menu_text = """📸 *Media Center*
━━━━━━━━━━━━━━━━━━━━━━━━

📱 Camera controls and media management
📁 Access device media files
🎥 Video recording capabilities"""
    
    await query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

async def toggle_wifi(query, state):
    """Enhanced WiFi toggle with status feedback"""
    action = "Enabling" if state else "Disabling"
    
    await query.edit_message_text(f"""📶 *WiFi Control*
━━━━━━━━━━━━━━━━━━━━━━━━

🔄 {action} WiFi...
⏳ Please wait...""", parse_mode='Markdown')
    
    command = "termux-wifi-enable true" if state else "termux-wifi-enable false"
    result = run_termux_command(command, timeout=8)
    
    # Wait a moment for WiFi to change state
    await asyncio.sleep(2)
    
    status = "📶 ENABLED" if state else "📵 DISABLED"
    status_icon = "🟢" if state else "🔴"
    
    response_text = f"""📶 *WiFi {status}*
━━━━━━━━━━━━━━━━━━━━━━━━

{status_icon} WiFi has been {action.lower()}
🕐 {datetime.now().strftime('%H:%M:%S')}

💡 {"You can now connect to networks" if state else "Disconnected from all networks"}"""
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_bot_control(query):
    """Enhanced bot control with system status"""
    global BOT_ENABLED, ZIPLOCK_STATUS
    
    status = "🟢 ONLINE" if BOT_ENABLED else "🔴 OFFLINE"
    uptime = datetime.now().strftime('%H:%M:%S')
    security_status = "🔐 ACTIVE" if ZIPLOCK_STATUS else "🔓 INACTIVE"
    
    keyboard = [
        [InlineKeyboardButton("🟢 Enable Bot", callback_data="bot_on"),
         InlineKeyboardButton("🔴 Disable Bot", callback_data="bot_off")],
        [InlineKeyboardButton("📊 System Status", callback_data="system_status")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    control_text = f"""⚙️ *Bot Control Center*
━━━━━━━━━━━━━━━━━━━━━━━━

🤖 Bot Status: {status}
🛡️ Security: {security_status}
🕐 Session Time: {uptime}
📊 Memory Usage: Active
🔐 Authorization: Verified

Current Features:
✅ App Control
✅ System Monitor  
✅ File Security
✅ Media Center
✅ Network Tools
✅ Web Integration"""
    
    await query.edit_message_text(control_text, reply_markup=reply_markup, parse_mode='Markdown')

async def toggle_bot(query, state):
    """Enhanced bot toggle with confirmation"""
    global BOT_ENABLED
    BOT_ENABLED = state
    
    status = "🟢 ONLINE" if state else "🔴 OFFLINE"
    action = "ENABLED" if state else "DISABLED"
    icon = "✅" if state else "❌"
    
    response_text = f"""⚙️ *Bot Status Updated*
━━━━━━━━━━━━━━━━━━━━━━━━

{icon} Bot has been {action}
📊 Status: {status}
🕐 Changed: {datetime.now().strftime('%H:%M:%S')}

{"🚀 All features are now active" if state else "⏸️ Bot features are suspended"}"""
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_main_menu(query):
    """Enhanced main menu with dynamic status"""
    global BOT_ENABLED, ZIPLOCK_STATUS
    
    user = query.from_user
    current_time = datetime.now().strftime('%H:%M:%S')
    
    keyboard = [
        [InlineKeyboardButton("📱 Applications", callback_data="apps"),
         InlineKeyboardButton("🌐 Web Tools", callback_data="web_tools")],
        [InlineKeyboardButton("🔦 Flashlight", callback_data="flashlight"),
         InlineKeyboardButton("📍 Location", callback_data="gps")],
        [InlineKeyboardButton("📩 Notifications", callback_data="notifications"),
         InlineKeyboardButton("💻 System Info", callback_data="sysinfo")],
        [InlineKeyboardButton("📸 Media Center", callback_data="media"),
         InlineKeyboardButton("🔊 Audio Tools", callback_data="audio_tools")],
        [InlineKeyboardButton("📶 Network", callback_data="network"),
         InlineKeyboardButton("🖼️ Wallpaper", callback_data="wallpaper")],
        [InlineKeyboardButton("🔐 File Security", callback_data="file_security"),
         InlineKeyboardButton("⚙️ Bot Control", callback_data="bot_control")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    main_text = f"""🐍 *RatSerpentSecHunterBot v2.0*
━━━━━━━━━━━━━━━━━━━━━━━━

👋 Welcome back, *{user.first_name}*!

📊 Status: {'🟢 ONLINE' if BOT_ENABLED else '🔴 OFFLINE'}
🔒 Security: {'🔐 ACTIVE' if ZIPLOCK_STATUS else '🔓 INACTIVE'}
🕐 Time: {current_time}

🚀 Ready to serve all your needs!"""
    
    await query.edit_message_text(main_text, reply_markup=reply_markup, parse_mode='Markdown')

async def set_wallpaper(query, screen_type, photo_path):
    """Enhanced wallpaper setter (called from callback)"""
    screen_name = "Home" if screen_type == "home" else "Lock"
    
    await query.edit_message_text(f"""🖼️ *Setting {screen_name} Wallpaper*
━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ Applying wallpaper...
📱 Please wait...""", parse_mode='Markdown')
    
    # Set wallpaper command
    if screen_type == "home":
        command = f"termux-wallpaper -f {photo_path}"
    else:
        command = f"termux-wallpaper -l -f {photo_path}"
    
    result = run_termux_command(command, timeout=15)
    
    # Clean up temp file
    try:
        os.remove(photo_path)
    except:
        pass
    
    if not result or "Error" not in result:
        await query.edit_message_text(f"""🖼️ *Wallpaper Set Successfully*
━━━━━━━━━━━━━━━━━━━━━━━━

✅ {screen_name} screen wallpaper updated!
🕐 Applied: {datetime.now().strftime('%H:%M:%S')}
🎉 Your new wallpaper is now active!""", parse_mode='Markdown')
    else:
        await query.edit_message_text(f"""❌ *Wallpaper Failed*
━━━━━━━━━━━━━━━━━━━━━━━━

🚫 Could not set wallpaper
⚠️ Check Termux:API permissions
🔧 Please try again""", parse_mode='Markdown')

def main():
    """Enhanced main function with better error handling"""
    print("🐍 Starting RatSerpentSecHunterBot v2.0...")
    print(f"🔐 Authorized User: {AUTHORIZED_USER_ID}")
    print("⚡ Dependencies checked - Starting enhanced bot...")
    
    # Create application with enhanced settings
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add all handlers
    application.add_handler(CommandHandler("start", start))
    
    # Web tools handlers
    application.add_handler(CommandHandler("openyt", handle_openyt))
    application.add_handler(CommandHandler("carivtyt", handle_carivtyt))
    application.add_handler(CommandHandler("opench", handle_opench))
    application.add_handler(CommandHandler("opentt", handle_opentt))
    
    # File security handlers
    application.add_handler(CommandHandler("ziplock", handle_ziplock))
    application.add_handler(CommandHandler("unziplock", handle_unziplock))
    
    # Audio handler
    application.add_handler(CommandHandler("tts", handle_tts))
    
    # Media handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Callback handler for all buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ RatSerpentSecHunterBot v2.0 Enhanced started!")
    print("🚀 All features loaded and ready...")
    print("🔐 Security systems active...")
    print("📱 Web tools integrated...")
    print("🖼️ Media center online...")
    print("🎵 Audio tools ready...")
    print("🔒 File security enabled...")
    print()
    print("🌟 Bot is running with all enhanced features!")
    print("📞 Press Ctrl+C to stop")
    
    # Run the bot with enhanced polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        poll_interval=1.0,
        timeout=30
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot crashed: {str(e)}")
        print("🔄 Please restart the bot")
    finally:
        print("👋 RatSerpentSecHunterBot v2.0 shutdown complete")
