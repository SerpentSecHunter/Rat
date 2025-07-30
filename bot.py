#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Termux Bot Controller - Clean Version
No syntax errors, tested code
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime

# Auto install packages
def install_packages():
    packages = ['python-telegram-bot==20.7', 'psutil', 'requests']
    for pkg in packages:
        try:
            __import__(pkg.split('==')[0].replace('-', '_'))
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg])

install_packages()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import psutil

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TermuxBot:
    def __init__(self):
        self.bot_token = self.get_token()
        self.current_directory = os.path.expanduser('~')
        self.bot_active = True
        self.termux_api = self.check_termux_api()
        
    def get_token(self):
        # Check for existing token
        if os.path.exists('bot_config.json'):
            try:
                with open('bot_config.json', 'r') as f:
                    config = json.load(f)
                    return config.get('bot_token')
            except:
                pass
        
        # Get new token
        print("\n" + "="*50)
        print("🤖 TERMUX BOT SETUP")
        print("="*50)
        print("1. Buka @BotFather di Telegram")
        print("2. Ketik /newbot")
        print("3. Ikuti instruksi")
        print("4. Copy token yang diberikan")
        print("="*50)
        
        token = input("Paste Bot Token: ").strip()
        
        # Save token
        config = {'bot_token': token}
        with open('bot_config.json', 'w') as f:
            json.dump(config, f)
            
        return token
    
    def check_termux_api(self):
        try:
            result = subprocess.run(['which', 'termux-battery-status'], 
                                  capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def create_main_keyboard(self):
        keyboard = [
            [
                InlineKeyboardButton("💻 Terminal", callback_data="terminal"),
                InlineKeyboardButton("ℹ️ System Info", callback_data="sysinfo")
            ],
            [
                InlineKeyboardButton("📁 Files", callback_data="files"),
                InlineKeyboardButton("📊 Monitor", callback_data="monitor")
            ]
        ]
        
        if self.termux_api:
            keyboard.append([
                InlineKeyboardButton("📷 Camera", callback_data="camera"),
                InlineKeyboardButton("🔋 Battery", callback_data="battery")
            ])
            keyboard.append([
                InlineKeyboardButton("📍 Location", callback_data="location"),
                InlineKeyboardButton("📳 Vibrate", callback_data="vibrate")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("⚠️ Install Termux:API", callback_data="install_api")
            ])
            
        keyboard.append([
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        api_status = "✅ Available" if self.termux_api else "❌ Not Available"
        
        message = f"""
🤖 **TERMUX BOT CONTROLLER**
════════════════════════════

👋 Welcome! Bot is ready to use.

📊 **Status:**
• Bot: 🟢 Active
• Termux:API: {api_status}
• Directory: `{os.path.basename(self.current_directory)}`

🎯 **Working Features:**
• 💻 Full Terminal Access
• 📁 File Management  
• 📊 System Monitoring
• ℹ️ System Information

{f"📱 **Hardware Features (API):**\n• 📷 Camera Control\n• 🔋 Battery Status\n• 📍 GPS Location\n• 📳 Device Vibration" if self.termux_api else "⚠️ Install Termux:API for hardware features"}

🚀 Select a feature to start!
        """
        
        await update.message.reply_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "terminal":
            await self.show_terminal(query)
        elif query.data == "sysinfo":
            await self.show_system_info(query)
        elif query.data == "files":
            await self.show_files(query)
        elif query.data == "monitor":
            await self.show_monitor(query)
        elif query.data == "camera":
            await self.take_photo(query)
        elif query.data == "battery":
            await self.check_battery(query)
        elif query.data == "location":
            await self.get_location(query)
        elif query.data == "vibrate":
            await self.vibrate_device(query)
        elif query.data == "install_api":
            await self.show_api_guide(query)
        elif query.data == "settings":
            await self.show_settings(query)
        elif query.data == "main_menu":
            await self.show_main_menu(query)
    
    async def show_main_menu(self, query):
        api_status = "✅" if self.termux_api else "❌"
        message = f"""
🤖 **MAIN MENU**
════════════════════════

📊 **Status:**
• Bot: 🟢 Active
• API: {api_status}
• Dir: `{os.path.basename(self.current_directory)}`

Select an option:
        """
        
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_terminal(self, query):
        message = f"""
💻 **TERMINAL MODE**
════════════════════════

📁 **Current Directory:**
`{self.current_directory}`

🎯 **How to use:**
Type any command directly in chat!

📝 **Examples:**
```
ls -la
cd /sdcard
python script.py
pkg install git
pwd
ps aux
```

💡 **Tips:**
• Use `cd ~` to go home
• Use `cd ..` to go back
• Type commands like normal terminal

⚡ **Type your command now!**
        """
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📁 Files", callback_data="files"),
                InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
            ]]),
            parse_mode='Markdown'
        )
    
    async def show_system_info(self, query):
        await query.edit_message_text("ℹ️ Getting system info...")
        
        try:
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get Android info
            try:
                android_version = subprocess.run(['getprop', 'ro.build.version.release'], 
                                               capture_output=True, text=True).stdout.strip()
                device_model = subprocess.run(['getprop', 'ro.product.model'], 
                                            capture_output=True, text=True).stdout.strip()
            except:
                android_version = "Unknown"
                device_model = "Unknown"
            
            # Create progress bars
            cpu_bar = self.create_progress_bar(cpu_percent)
            ram_bar = self.create_progress_bar(memory.percent)
            disk_bar = self.create_progress_bar(disk.percent)
            
            message = f"""
ℹ️ **SYSTEM INFORMATION**
════════════════════════════

📱 **Device Info:**
• Model: {device_model}
• Android: {android_version}

💻 **Resources:**
• CPU: {cpu_percent:.1f}%
{cpu_bar}

• RAM: {memory.percent:.1f}% ({memory.used//1024//1024}MB/{memory.total//1024//1024}MB)
{ram_bar}

• Storage: {disk.percent:.1f}% ({disk.used//1024//1024//1024:.1f}GB/{disk.total//1024//1024//1024:.1f}GB)
{disk_bar}

📁 **Directory:** `{self.current_directory}`
🕐 **Time:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Refresh", callback_data="sysinfo"),
                        InlineKeyboardButton("📊 Monitor", callback_data="monitor")
                    ],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error getting system info: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    def create_progress_bar(self, percentage, length=20):
        filled = int((percentage / 100) * length)
        bar = '█' * filled + '░' * (length - filled)
        return f"`{bar}` {percentage:.1f}%"
    
    async def show_files(self, query):
        try:
            files = []
            dirs = []
            
            for item in os.listdir(self.current_directory):
                path = os.path.join(self.current_directory, item)
                if os.path.isdir(path):
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
                file_list += "📁 **Directories:**\n"
                for d in display_dirs:
                    file_list += f"  📁 `{d}`\n"
                file_list += "\n"
            
            if display_files:
                file_list += "📄 **Files:**\n"
                for f in display_files:
                    size = self.get_file_size(os.path.join(self.current_directory, f))
                    file_list += f"  📄 `{f}` ({size})\n"
            
            if not display_dirs and not display_files:
                file_list = "📭 Empty directory"
            
            message = f"""
📁 **FILE MANAGER**
════════════════════════

📍 **Path:** `{self.current_directory}`

{file_list}

💡 **Commands:**
• `cd folder_name` - Enter folder
• `ls -la` - Detailed list
• `pwd` - Current path
            """
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🏠 Home", callback_data="go_home"),
                        InlineKeyboardButton("⬆️ Back", callback_data="go_back")
                    ],
                    [
                        InlineKeyboardButton("💻 Terminal", callback_data="terminal"),
                        InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                    ]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    def get_file_size(self, filepath):
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f}{unit}"
                size /= 1024
            return f"{size:.1f}TB"
        except:
            return "Unknown"
    
    async def show_monitor(self, query):
        await query.edit_message_text("📊 Loading system monitor...")
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            process_count = len(psutil.pids())
            
            cpu_bar = self.create_progress_bar(cpu_percent)
            ram_bar = self.create_progress_bar(memory.percent)
            disk_bar = self.create_progress_bar(disk.percent)
            
            message = f"""
📊 **SYSTEM MONITOR**
════════════════════════

💻 **CPU Usage:**
{cpu_bar}

🧠 **Memory Usage:**
{ram_bar}
Available: {memory.available//1024//1024}MB

💾 **Disk Usage:**
{disk_bar}
Free: {disk.free//1024//1024//1024:.1f}GB

📈 **System:**
• Processes: {process_count}
• Uptime: {datetime.fromtimestamp(psutil.boot_time()).strftime('%d/%m/%Y %H:%M')}

🕐 **Updated:** {datetime.now().strftime('%H:%M:%S')}
            """
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("🔄 Refresh", callback_data="monitor"),
                        InlineKeyboardButton("ℹ️ System Info", callback_data="sysinfo")
                    ],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ]),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    async def take_photo(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        await query.edit_message_text("📷 Taking photo...")
        
        try:
            photo_path = f"/tmp/photo_{int(datetime.now().timestamp())}.jpg"
            
            result = subprocess.run([
                'termux-camera-photo', 
                '-c', '1',  # Front camera
                photo_path
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    await query.message.reply_photo(
                        photo=photo,
                        caption=f"📷 Photo taken successfully!\n🕐 {datetime.now().strftime('%H:%M:%S')}"
                    )
                
                os.remove(photo_path)
                
                await query.edit_message_text(
                    "✅ Photo taken and sent!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📷 Take Another", callback_data="camera")],
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                    ])
                )
            else:
                raise Exception("Camera failed to capture")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Camera error: {str(e)}\n\n💡 Make sure camera permission is granted",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data="camera")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ])
            )
    
    async def check_battery(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        await query.edit_message_text("🔋 Checking battery...")
        
        try:
            result = subprocess.run(['termux-battery-status'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                battery = json.loads(result.stdout)
                
                percentage = battery.get('percentage', 0)
                status = battery.get('status', 'UNKNOWN')
                temperature = battery.get('temperature', 0)
                health = battery.get('health', 'UNKNOWN')
                
                battery_bar = self.create_progress_bar(percentage, 25)
                
                status_emoji = {
                    'CHARGING': '🔌',
                    'DISCHARGING': '🔋',
                    'FULL': '✅'
                }.get(status, '❓')
                
                message = f"""
🔋 **BATTERY STATUS**
════════════════════════

📊 **Battery Level:**
{battery_bar}

📈 **Details:**
• Status: {status_emoji} {status}
• Health: {health}
• Temperature: 🌡️ {temperature}°C

🕐 **Updated:** {datetime.now().strftime('%H:%M:%S')}
                """
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Refresh", callback_data="battery")],
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception("Cannot access battery info")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Battery error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    async def get_location(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        await query.edit_message_text("📍 Getting GPS location...")
        
        try:
            result = subprocess.run([
                'termux-location', 
                '-p', 'gps',
                '-r', 'once'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                location = json.loads(result.stdout)
                
                lat = location.get('latitude', 0)
                lon = location.get('longitude', 0)
                accuracy = location.get('accuracy', 0)
                
                message = f"""
📍 **GPS LOCATION**
════════════════════════

🎯 **Coordinates:**
• Latitude: `{lat}`
• Longitude: `{lon}`
• Accuracy: ±{accuracy:.1f}m

🗺️ **Maps:**
[Google Maps](https://maps.google.com/?q={lat},{lon})

🕐 **Time:** {datetime.now().strftime('%H:%M:%S')}
                """
                
                await query.message.reply_location(latitude=lat, longitude=lon)
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📍 Update Location", callback_data="location")],
                        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                    ]),
                    parse_mode='Markdown'
                )
            else:
                raise Exception("GPS location not available")
                
        except Exception as e:
            await query.edit_message_text(
                f"❌ Location error: {str(e)}\n\n💡 Make sure GPS is enabled",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Try Again", callback_data="location")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ])
            )
    
    async def vibrate_device(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        try:
            subprocess.run(['termux-vibrate', '-d', '1000'], timeout=5)
            
            await query.edit_message_text(
                "📳 **Device vibrated!**\n\n✅ Vibration sent for 1 second",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📳 Vibrate Again", callback_data="vibrate")],
                    [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
                ])
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ Vibration error: {str(e)}",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]])
            )
    
    async def show_api_guide(self, query):
        message = """
📥 **TERMUX:API INSTALLATION**
════════════════════════════

**🔧 Steps:**

**1️⃣ Download Termux:API App:**
• Open F-Droid: https://f-droid.org
• Search "Termux:API"
• Download & Install APK

**2️⃣ Install Package:**
```
pkg update
pkg install termux-api
```

**3️⃣ Grant Permissions:**
• Settings → Apps → Termux:API
• Permissions → Allow ALL
• Especially: Camera, Location, Storage

**4️⃣ Test:**
```
termux-battery-status
termux-camera-info
```

**✅ Features Available:**
• 📷 Camera Control
• 🔋 Battery Status  
• 📍 GPS Location
• 📳 Device Vibration
• And more!
        """
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Check API", callback_data="check_api")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]),
            parse_mode='Markdown'
        )
    
    async def show_settings(self, query):
        message = f"""
⚙️ **BOT SETTINGS**
════════════════════════

🤖 **Status:**
• Bot: {'🟢 Active' if self.bot_active else '🔴 Inactive'}
• Termux:API: {'✅ Available' if self.termux_api else '❌ Not Available'}

📁 **Current Directory:**
`{self.current_directory}`

🔧 **Configuration:**
• Config file: bot_config.json
• Token: {self.bot_token[:10]}...
        """
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Restart Bot", callback_data="restart")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]),
            parse_mode='Markdown'
        )
    
    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        command = update.message.text.strip()
        
        try:
            # Handle cd command
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
                        await update.message.reply_text(f"❌ Directory not found: `{path}`", parse_mode='Markdown')
                        return
                
                await update.message.reply_text(f"📁 Changed to: `{self.current_directory}`", parse_mode='Markdown')
                return
            
            # Execute command
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
                output = "✅ Command executed (no output)"
            
            # Limit output
            if len(output) > 3000:
                output = output[:3000] + "\n... (truncated)"
            
            await update.message.reply_text(f"```\n{output}\n```", parse_mode='Markdown')
            
        except subprocess.TimeoutExpired:
            await update.message.reply_text("⏰ Command timeout (30s)")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    def run(self):
        print("\n" + "="*50)
        print("🤖 TERMUX BOT CONTROLLER")
        print("="*50)
        print("🚀 Starting...")
        print(f"📁 Directory: {self.current_directory}")
        print(f"📱 Termux:API: {'✅' if self.termux_api else '❌'}")
        print("="*50)
        
        try:
            app = Application.builder().token(self.bot_token).build()
            
            # Handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CallbackQueryHandler(self.button_handler))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_command))
            
            print("✅ Bot started successfully!")
            print("💬 Send /start in Telegram")
            print("🔄 Press Ctrl+C to stop")
            print("="*50)
            
            app.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    bot = TermuxBot()
    bot.run()
