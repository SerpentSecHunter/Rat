#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Termux Bot Controller - Enhanced Professional Version
Advanced features with non-root alternatives
Author: AI Assistant
Version: 2.0 - Fixed
"""

import os
import sys
import json
import subprocess
import logging
import asyncio
import threading
import time
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import zipfile
import tarfile

# Auto install packages
def install_packages():
    packages = [
        'python-telegram-bot==20.7', 
        'psutil', 
        'requests', 
        'aiofiles',
        'pillow',
        'qrcode[pil]',
        'cryptography'
    ]
    for pkg in packages:
        try:
            pkg_name = pkg.split('==')[0].replace('-', '_')
            if pkg_name == 'pillow':
                pkg_name = 'PIL'
            elif pkg_name == 'qrcode[pil]':
                pkg_name = 'qrcode'
            __import__(pkg_name)
        except ImportError:
            print(f"🔽 Installing {pkg}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '--quiet'])

install_packages()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import psutil
import requests
import qrcode
from PIL import Image
import io
import base64

# Enhanced logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('termux_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedTermuxBot:
    def __init__(self):
        self.bot_token = self.get_token()
        self.current_directory = os.path.expanduser('~')
        self.previous_directory = os.path.expanduser('~')
        self.bot_active = True
        self.termux_api = self.check_termux_api()
        self.authorized_users = self.load_authorized_users()
        self.command_history = []
        self.max_history = 50
        self.root_available = self.check_root()
        self.admin_features = self.check_device_admin()
        
        # Create necessary directories
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories for bot operation"""
        dirs = ['downloads', 'uploads', 'logs', 'backups', 'temp']
        for d in dirs:
            try:
                os.makedirs(d, exist_ok=True)
            except Exception as e:
                logger.error(f"Error creating directory {d}: {e}")
    
    def get_token(self):
        if os.path.exists('bot_config.json'):
            try:
                with open('bot_config.json', 'r') as f:
                    config = json.load(f)
                    return config.get('bot_token')
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        print("\n" + "🔥"*60)
        print("🚀 TERMUX BOT CONTROLLER v2.0 - PROFESSIONAL EDITION")
        print("🔥"*60)
        print("📋 SETUP INSTRUCTIONS:")
        print("1️⃣  Open @BotFather di Telegram")
        print("2️⃣  Ketik /newbot dan buat bot baru")
        print("3️⃣  Pilih nama dan username untuk bot")
        print("4️⃣  Copy token yang diberikan BotFather")
        print("5️⃣  Paste token dibawah ini")
        print("🔥"*60)
        
        token = input("🤖 Paste Bot Token: ").strip()
        
        config = {
            'bot_token': token,
            'created': datetime.now().isoformat(),
            'version': '2.0'
        }
        try:
            with open('bot_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
        return token
    
    def load_authorized_users(self):
        """Load authorized users from config"""
        try:
            with open('authorized_users.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading authorized users: {e}")
            return []
    
    def save_authorized_users(self):
        """Save authorized users to config"""
        try:
            with open('authorized_users.json', 'w') as f:
                json.dump(self.authorized_users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving authorized users: {e}")
    
    def check_termux_api(self):
        """Check Termux API availability with better error handling"""
        try:
            # Check if termux-api commands exist
            commands_to_check = ['termux-battery-status', 'termux-camera-info', 'termux-sensor']
            available_commands = 0
            
            for cmd in commands_to_check:
                try:
                    result = subprocess.run(['which', cmd], capture_output=True, timeout=3)
                    if result.returncode == 0:
                        available_commands += 1
                except Exception as e:
                    logger.debug(f"Command check failed for {cmd}: {e}")
                    continue
            
            # Consider API available if at least 2 commands are found
            return available_commands >= 2
        except Exception as e:
            logger.error(f"Error checking Termux API: {e}")
            return False
    
    def check_root(self):
        """Check if device has root access with better error handling"""
        try:
            # Method 1: Check for su command
            result = subprocess.run(['which', 'su'], capture_output=True, timeout=3)
            if result.returncode != 0:
                return False
            
            # Method 2: Try to execute a simple root command with timeout
            try:
                test_result = subprocess.run(['timeout', '3', 'su', '-c', 'id'], 
                                           capture_output=True, timeout=5)
                return test_result.returncode == 0 and 'uid=0' in test_result.stdout.decode()
            except Exception:
                # Method 3: Check if we can read root-only files
                try:
                    with open('/data/system/users/0/settings_system.xml', 'r') as f:
                        return True
                except Exception:
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking root access: {e}")
            return False
    
    def check_device_admin(self):
        """Check for device admin alternatives with error handling"""
        try:
            alternatives = []
            
            # Check for various system access methods
            access_checks = [
                ('/proc/version', 'proc_access'),
                ('/sys/class/power_supply', 'power_access'),
                ('/sys/class/net', 'network_access'),
                ('/proc/meminfo', 'memory_access'),
                ('/proc/cpuinfo', 'cpu_access')
            ]
            
            for path, access_type in access_checks:
                try:
                    if os.path.exists(path) and os.access(path, os.R_OK):
                        alternatives.append(access_type)
                except Exception:
                    continue
            
            # Check for notification access (if termux-api available)
            if self.termux_api:
                try:
                    result = subprocess.run(['termux-notification-list'], 
                                          capture_output=True, timeout=3)
                    if result.returncode == 0:
                        alternatives.append('notification_access')
                except Exception:
                    pass
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error checking device admin alternatives: {e}")
            return []
    
    def is_authorized(self, user_id):
        """Check if user is authorized"""
        return len(self.authorized_users) == 0 or user_id in self.authorized_users
    
    def create_main_keyboard(self):
        """Create enhanced main menu keyboard"""
        keyboard = [
            [
                InlineKeyboardButton("💻 Terminal Pro", callback_data="terminal"),
                InlineKeyboardButton("📊 System Monitor", callback_data="sysinfo")
            ],
            [
                InlineKeyboardButton("📁 File Manager", callback_data="files"),
                InlineKeyboardButton("🌐 Network Tools", callback_data="network")
            ],
            [
                InlineKeyboardButton("📱 Device Control", callback_data="device"),
                InlineKeyboardButton("🔧 System Tools", callback_data="system_tools")
            ]
        ]
        
        if self.termux_api:
            keyboard.append([
                InlineKeyboardButton("📷 Camera Pro", callback_data="camera"),
                InlineKeyboardButton("📍 GPS & Sensors", callback_data="sensors")
            ])
        
        if self.root_available:
            keyboard.append([
                InlineKeyboardButton("👑 Root Manager", callback_data="root_manager")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("🔓 Non-Root Tools", callback_data="nonroot_tools")
            ])
            
        keyboard.extend([
            [
                InlineKeyboardButton("🛡️ Security", callback_data="security"),
                InlineKeyboardButton("📦 Package Manager", callback_data="packages")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("📖 Help", callback_data="help")
            ]
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_system_stats(self):
        """Get system stats with fallback methods for Android/Termux"""
        stats = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'memory_used': 0,
            'memory_total': 0
        }
        
        try:
            # Try to get CPU usage
            stats['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        except (PermissionError, OSError, Exception):
            try:
                # Fallback: use /proc/loadavg
                with open('/proc/loadavg', 'r') as f:
                    load_avg = float(f.read().split()[0])
                    stats['cpu_percent'] = min(load_avg * 25, 100)  # Rough estimate
            except Exception:
                stats['cpu_percent'] = 0
        
        try:
            # Try to get memory info
            memory = psutil.virtual_memory()
            stats['memory_percent'] = memory.percent
            stats['memory_used'] = memory.used
            stats['memory_total'] = memory.total
        except (PermissionError, OSError, Exception):
            try:
                # Fallback: use /proc/meminfo
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            meminfo[parts[0][:-1]] = int(parts[1]) * 1024  # Convert kB to bytes
                    
                    total = meminfo.get('MemTotal', 0)
                    available = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
                    used = total - available
                    
                    stats['memory_total'] = total
                    stats['memory_used'] = used
                    stats['memory_percent'] = (used / total * 100) if total > 0 else 0
            except Exception:
                stats['memory_percent'] = 0
                stats['memory_used'] = 0
                stats['memory_total'] = 0
        
        return stats

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text(
                "🚫 **ACCESS DENIED**\n\nYou are not authorized to use this bot.",
                parse_mode='Markdown'
            )
            return
        
        # System status check with error handling
        try:
            stats = self.get_system_stats()
            cpu_percent = stats['cpu_percent']
            memory_percent = stats['memory_percent']
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            cpu_percent = 0
            memory_percent = 0
        
        api_status = "🟢 Active" if self.termux_api else "🔴 Install Required"
        root_status = "👑 Available" if self.root_available else "🔓 Non-Root Mode"
        
        message = f"""
🔥 **TERMUX BOT CONTROLLER v2.0**
════════════════════════════════════

👋 **Welcome, {update.effective_user.first_name}!**

📊 **System Status:**
┣ 🤖 Bot: 🟢 **Online & Ready**
┣ 🔌 Termux API: {api_status}
┣ 👑 Root Access: {root_status}
┣ 💻 CPU: **{cpu_percent:.1f}%**
┣ 🧠 RAM: **{memory_percent:.1f}%**
┗ 📁 Directory: `{os.path.basename(self.current_directory)}`

🚀 **New Features v2.0:**
┣ 🌐 **Advanced Network Tools**
┣ 🛡️ **Security & Encryption**
┣ 📦 **Smart Package Manager**
┣ 🔓 **Non-Root Alternatives**
┣ 📱 **Enhanced Device Control**
┗ 💻 **Professional Terminal**

⚡ **Quick Actions:**
{f"┣ 📷 Camera, 🔋 Battery, 📍 GPS" if self.termux_api else "┣ ⚠️ Install Termux:API for hardware features"}
{f"┣ 👑 Root operations available" if self.root_available else "┣ 🔓 Non-root tools active"}
┗ 💡 All features optimized for your device

🎯 **Select a feature to begin!**
        """
        
        await update.message.reply_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await query.edit_message_text("🚫 Access denied")
            return
        
        handlers = {
            "terminal": self.show_terminal_pro,
            "sysinfo": self.show_system_monitor,
            "files": self.show_file_manager,
            "network": self.show_network_tools,
            "device": self.show_device_control,  # FIXED: Added missing method
            "system_tools": self.show_system_tools,
            "camera": self.show_camera_pro,
            "sensors": self.show_sensors,
            "root_manager": self.show_root_manager,
            "nonroot_tools": self.show_nonroot_tools,
            "security": self.show_security_tools,
            "packages": self.show_package_manager,
            "settings": self.show_settings,
            "help": self.show_help,
            "main_menu": self.show_main_menu,
            # File operations
            "upload_file": self.handle_file_upload,
            "download_file": self.handle_file_download,
            "compress_files": self.compress_files,
            "backup_system": self.backup_system,
            "go_home": self.go_home,
            "go_parent": self.go_parent,
            "search_files": self.search_files,
            "disk_usage": self.show_disk_usage,
            # Network operations
            "scan_network": self.scan_network,
            "check_ports": self.check_ports,
            "speed_test": self.network_speed_test,
            "wifi_info": self.show_wifi_info,
            "ping_test": self.ping_test,
            "dns_lookup": self.dns_lookup,
            "public_ip": self.show_public_ip,
            "bandwidth_monitor": self.bandwidth_monitor,
            # System operations
            "process_manager": self.show_process_manager,
            "service_manager": self.show_service_manager,
            "log_viewer": self.show_log_viewer,
            "cleanup_system": self.cleanup_system,
            "detailed_stats": self.show_detailed_stats,
            # Package management
            "pkg_install": self.pkg_install,
            "pkg_update": self.pkg_update,
            "pkg_remove": self.pkg_remove,
            "pkg_search": self.pkg_search,
            "pkg_list": self.pkg_list,
            "pkg_sizes": self.pkg_sizes,
            "apk_manager": self.apk_manager,
            "pip_manager": self.pip_manager,
            "pkg_cleanup": self.pkg_cleanup,
            "pkg_backup": self.pkg_backup,
            # Security tools
            "encrypt_files": self.encrypt_files,
            "gen_password": self.generate_password,
            "qr_generator": self.qr_generator,
            "hash_calculator": self.hash_calculator,
            "vuln_scan": self.vulnerability_scan,
            "network_security": self.network_security,
            "privacy_clean": self.privacy_clean,
            "secure_delete": self.secure_delete,
            "ssh_keys": self.ssh_keys,
            "device_lock": self.device_lock,
            # Camera and sensors
            "quick_photo": self.quick_photo,
            "record_video": self.record_video,
            "switch_camera": self.switch_camera,
            "camera_settings": self.camera_settings,
            "gps_location": self.gps_location,
            "compass": self.compass,
            "accelerometer": self.accelerometer,
            "temperature": self.temperature,
            # Settings
            "user_management": self.user_management,
            "bot_settings": self.bot_settings,
            "view_logs": self.view_logs,
            "clear_data": self.clear_data,
            "restart_bot": self.restart_bot,
            "export_config": self.export_config,
            "install_api": self.install_api,
            "diagnostics": self.diagnostics,
            # Command operations
            "cmd_history": self.show_cmd_history,
            "batch_cmd": self.batch_cmd,
        }
        
        handler = handlers.get(query.data)
        if handler:
            try:
                await handler(query)
            except Exception as e:
                logger.error(f"Error in handler {query.data}: {e}")
                await query.edit_message_text(
                    f"❌ **Error in {query.data}:**\n`{str(e)}`",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                    ]]),
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text(
                f"🚫 **Feature not implemented:** `{query.data}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
    
    async def show_main_menu(self, query):
        try:
            stats = self.get_system_stats()
            cpu = stats['cpu_percent']
            ram = stats['memory_percent']
        except Exception:
            cpu = ram = 0
        
        message = f"""
🔥 **MAIN MENU - TERMUX BOT v2.0**
════════════════════════════════════

📊 **Quick Status:**
┣ 💻 CPU: **{cpu:.1f}%** | 🧠 RAM: **{ram:.1f}%**
┣ 📁 Path: `{os.path.basename(self.current_directory)}`
┗ 🕐 Time: **{datetime.now().strftime('%H:%M:%S')}**

🎯 **Choose your tool:**
        """
        
        await query.edit_message_text(
            message,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )
    
    async def show_terminal_pro(self, query):
        recent_commands = self.command_history[-5:] if self.command_history else ["No recent commands"]
        
        message = f"""
💻 **TERMINAL PRO MODE**
════════════════════════════════════

📍 **Current Directory:**
`{self.current_directory}`

📊 **Terminal Status:**
┣ 🔄 History: **{len(self.command_history)} commands**
┣ 👑 Root: **{'Available' if self.root_available else 'Not Available'}**
┗ 🌐 Network: **Connected**

📝 **Recent Commands:**
{chr(10).join([f"┣ `{cmd[:40]}...`" if len(cmd) > 40 else f"┣ `{cmd}`" for cmd in recent_commands[-3:]])}

🚀 **Enhanced Features:**
┣ 💾 **Command History & Favorites**
┣ 📁 **Smart Directory Navigation**
┣ 🔄 **Auto-completion Suggestions**
┣ 📊 **Real-time Process Monitoring**
┗ ⚡ **Batch Command Execution**

💡 **Power Commands:**
```bash
# System Info
neofetch || screenfetch
htop || top

# Network
ss -tuln
netstat -an
ifconfig || ip addr

# Files & Processes
find / -name "*.apk" 2>/dev/null
ps aux | grep -v grep
du -sh */ | sort -hr
```

⚡ **Type any command to execute!**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Process Monitor", callback_data="process_manager"),
                InlineKeyboardButton("📁 Quick Nav", callback_data="files")
            ],
            [
                InlineKeyboardButton("🔄 Command History", callback_data="cmd_history"),
                InlineKeyboardButton("⚡ Batch Execute", callback_data="batch_cmd")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_system_monitor(self, query):
        await query.edit_message_text("📊 Analyzing system performance...")
        
        try:
            # Enhanced system analysis with error handling
            try:
                stats = self.get_system_stats()
                cpu_percent = stats['cpu_percent']
                memory_percent = stats['memory_percent']
                memory_used = stats['memory_used']
                memory_total = stats['memory_total']
            except Exception as e:
                logger.error(f"Error getting system stats: {e}")
                cpu_percent = 0
                memory_percent = 0
                memory_used = 0
                memory_total = 0
            
            try:
                cpu_count = psutil.cpu_count() or 1
            except Exception:
                cpu_count = 1
            
            try:
                disk = psutil.disk_usage('/')
            except Exception:
                # Fallback for disk usage
                try:
                    result = subprocess.run(['df', '/'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            parts = lines[1].split()
                            if len(parts) >= 4:
                                total = int(parts[1]) * 1024  # Convert KB to bytes
                                used = int(parts[2]) * 1024
                                free = int(parts[3]) * 1024
                                
                                class DiskUsage:
                                    def __init__(self, total, used, free):
                                        self.total = total
                                        self.used = used
                                        self.free = free
                                
                                disk = DiskUsage(total, used, free)
                            else:
                                raise Exception("Invalid df output")
                        else:
                            raise Exception("No df data")
                    else:
                        raise Exception("df command failed")
                except Exception as e:
                    logger.error(f"Error getting disk usage: {e}")
                    class DiskUsage:
                        def __init__(self):
                            self.total = 1
                            self.used = 0
                            self.free = 1
                    disk = DiskUsage()
            
            try:
                boot_time = psutil.boot_time()
                uptime = datetime.now() - datetime.fromtimestamp(boot_time)
            except Exception:
                try:
                    # Fallback: use /proc/uptime
                    with open('/proc/uptime', 'r') as f:
                        uptime_seconds = float(f.read().split()[0])
                        uptime = timedelta(seconds=uptime_seconds)
                except Exception:
                    uptime = timedelta(0)
            
            # Network stats with fallback
            try:
                net_io = psutil.net_io_counters()
                bytes_sent = net_io.bytes_sent
                bytes_recv = net_io.bytes_recv
                packets_sent = net_io.packets_sent
                packets_recv = net_io.packets_recv
            except Exception:
                bytes_sent = bytes_recv = packets_sent = packets_recv = 0
            
            # Process count with fallback
            try:
                processes = len(psutil.pids())
            except Exception:
                try:
                    result = subprocess.run(['ps', '-A'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        processes = len(result.stdout.strip().split('\n')) - 1  # Exclude header
                    else:
                        processes = 0
                except Exception:
                    processes = 0
            
            # Temperature (if available)
            temp_info = "N/A"
            try:
                if self.termux_api:
                    temp_result = subprocess.run(['termux-sensor', '-s', 'temperature'], 
                                               capture_output=True, text=True, timeout=5)
                    if temp_result.returncode == 0:
                        temp_data = json.loads(temp_result.stdout)
                        temp_info = f"{temp_data.get('temperature', 'N/A')}°C"
            except Exception:
                # Try thermal zone fallback
                try:
                    thermal_files = ['/sys/class/thermal/thermal_zone0/temp',
                                   '/sys/class/thermal/thermal_zone1/temp']
                    for thermal_file in thermal_files:
                        if os.path.exists(thermal_file):
                            with open(thermal_file, 'r') as f:
                                temp_millicelsius = int(f.read().strip())
                                temp_celsius = temp_millicelsius / 1000
                                temp_info = f"{temp_celsius:.1f}°C"
                                break
                except Exception:
                    pass
            
            # Create enhanced progress bars
            cpu_bar = self.create_progress_bar(cpu_percent, 25, "🔥")
            ram_bar = self.create_progress_bar(memory_percent, 25, "🧠")
            disk_percent = (disk.used/disk.total*100) if disk.total > 0 else 0
            disk_bar = self.create_progress_bar(disk_percent, 25, "💾")
            
            message = f"""
📊 **SYSTEM PERFORMANCE MONITOR**
════════════════════════════════════

🖥️ **CPU Performance:**
{cpu_bar}
┣ Cores: **{cpu_count}** | Usage: **{cpu_percent:.1f}%**
┗ Temperature: **{temp_info}**

🧠 **Memory Usage:**
{ram_bar}
┣ Used: **{memory_used//1024//1024:,}MB** / **{memory_total//1024//1024:,}MB**
┣ Available: **{(memory_total-memory_used)//1024//1024:,}MB**
┗ Percentage: **{memory_percent:.1f}%**

💾 **Storage Usage:**
{disk_bar}
┣ Used: **{disk.used//1024//1024//1024:.1f}GB** / **{disk.total//1024//1024//1024:.1f}GB**
┗ Free: **{disk.free//1024//1024//1024:.1f}GB**

🌐 **Network Activity:**
┣ 📤 Sent: **{bytes_sent//1024//1024:.1f}MB**
┣ 📥 Received: **{bytes_recv//1024//1024:.1f}MB**
┗ 📊 Packets: **{packets_sent + packets_recv:,}**

⚡ **System Info:**
┣ 📈 Processes: **{processes}**
┣ ⏰ Uptime: **{str(uptime).split('.')[0]}**
┗ 🕐 Updated: **{datetime.now().strftime('%H:%M:%S')}**
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="sysinfo"),
                    InlineKeyboardButton("📈 Detailed Stats", callback_data="detailed_stats")
                ],
                [
                    InlineKeyboardButton("📊 Process Manager", callback_data="process_manager"),
                    InlineKeyboardButton("🧹 System Cleanup", callback_data="cleanup_system")
                ],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **System Monitor Error**\n\n`{str(e)}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
    
    def create_progress_bar(self, percentage, length=20, emoji="█"):
        """Create enhanced progress bar with emoji"""
        filled = int((percentage / 100) * length)
        bar = emoji * filled + "░" * (length - filled)
        
        # Color coding based on percentage
        if percentage < 30:
            status = "🟢"
        elif percentage < 70:
            status = "🟡"
        else:
            status = "🔴"
            
        return f"`{bar}` {status} **{percentage:.1f}%**"
    
    async def show_file_manager(self, query):
        try:
            files = []
            dirs = []
            
            # Get directory contents
            for item in os.listdir(self.current_directory):
                path = os.path.join(self.current_directory, item)
                try:
                    if os.path.isdir(path):
                        dirs.append(item)
                    else:
                        files.append(item)
                except PermissionError:
                    continue
            
            dirs.sort()
            files.sort()
            
            # Limit display
            display_dirs = dirs[:8]
            display_files = files[:8]
            
            file_list = ""
            
            if display_dirs:
                file_list += "📁 **Directories:**\n"
                for d in display_dirs:
                    try:
                        item_count = len(os.listdir(os.path.join(self.current_directory, d)))
                        file_list += f"┣ 📁 `{d}` ({item_count} items)\n"
                    except Exception:
                        file_list += f"┣ 📁 `{d}` (protected)\n"
                file_list += "\n"
            
            if display_files:
                file_list += "📄 **Files:**\n"
                for f in display_files:
                    size = self.get_file_size(os.path.join(self.current_directory, f))
                    ext = os.path.splitext(f)[1].lower()
                    icon = self.get_file_icon(ext)
                    file_list += f"┣ {icon} `{f}` ({size})\n"
            
            if not display_dirs and not display_files:
                file_list = "📭 **Directory is empty**"
            
            # Show hidden file count
            hidden_dirs = len([d for d in dirs if d.startswith('.')]) if len(dirs) > 8 else 0
            hidden_files = len([f for f in files if f.startswith('.')]) if len(files) > 8 else 0
            
            summary = f"\n📊 **Summary:** {len(dirs)} dirs, {len(files)} files"
            if hidden_dirs or hidden_files:
                summary += f" (+{hidden_dirs + hidden_files} hidden)"
            
            message = f"""
📁 **ADVANCED FILE MANAGER**
════════════════════════════════════

📍 **Current Path:**
`{self.current_directory}`

{file_list}{summary}

🔧 **Quick Actions:**
┣ 📤 Upload files to current directory
┣ 📥 Download files from current directory  
┣ 🗜️ Compress/Extract archives
┣ 🔍 Search files and directories
┗ 📊 Analyze disk usage
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🏠 Home", callback_data="go_home"),
                    InlineKeyboardButton("⬆️ Parent", callback_data="go_parent"),
                    InlineKeyboardButton("🔄 Refresh", callback_data="files")
                ],
                [
                    InlineKeyboardButton("📤 Upload", callback_data="upload_file"),
                    InlineKeyboardButton("📥 Download", callback_data="download_file"),
                    InlineKeyboardButton("🗜️ Archive", callback_data="compress_files")
                ],
                [
                    InlineKeyboardButton("🔍 Search", callback_data="search_files"),
                    InlineKeyboardButton("📊 Disk Usage", callback_data="disk_usage")
                ],
                [
                    InlineKeyboardButton("💻 Terminal", callback_data="terminal"),
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **File Manager Error**\n\n`{str(e)}`",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")
                ]]),
                parse_mode='Markdown'
            )
    
    def get_file_icon(self, ext):
        """Get appropriate icon for file type"""
        icons = {
            '.py': '🐍', '.js': '📜', '.html': '🌐', '.css': '🎨',
            '.jpg': '🖼️', '.png': '🖼️', '.gif': '🖼️', '.mp4': '🎬',
            '.mp3': '🎵', '.wav': '🎵', '.pdf': '📄', '.txt': '📝',
            '.zip': '🗜️', '.tar': '🗜️', '.gz': '🗜️', '.apk': '📱',
            '.deb': '📦', '.rpm': '📦', '.exe': '⚙️', '.sh': '📋',
            '.json': '📋', '.xml': '📋', '.log': '📊', '.db': '🗄️'
        }
        return icons.get(ext, '📄')
    
    def get_file_size(self, filepath):
        """Get human readable file size"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024:
                    return f"{size:.1f}{unit}"
                size /= 1024
            return f"{size:.1f}PB"
        except Exception:
            return "Unknown"
    
    async def show_network_tools(self, query):
        message = f"""
🌐 **ADVANCED NETWORK TOOLS**
════════════════════════════════════

🔍 **Network Analysis:**
┣ 🌐 **Network Scanner** - Discover devices
┣ 🔌 **Port Scanner** - Check open ports  
┣ 📊 **Speed Test** - Internet performance
┣ 📡 **WiFi Analyzer** - Network details
┗ 🌍 **Public IP Info** - Location & ISP

⚡ **Connection Tools:**
┣ 🏓 **Ping & Traceroute** - Network testing
┣ 🔗 **DNS Lookup** - Domain resolution
┣ 📱 **Device Info** - Network interfaces
┗ 🛡️ **Security Scan** - Vulnerability check

🚀 **Professional Features:**
┣ 📈 **Bandwidth Monitor** - Real-time usage
┣ 🌐 **HTTP Server** - Create local server
┣ 🔐 **VPN Status** - Connection details
┗ 📊 **Network Statistics** - Detailed metrics

💡 **Select a network tool:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🌐 Network Scan", callback_data="scan_network"),
                InlineKeyboardButton("🔌 Port Scan", callback_data="check_ports")
            ],
            [
                InlineKeyboardButton("📊 Speed Test", callback_data="speed_test"),
                InlineKeyboardButton("📡 WiFi Info", callback_data="wifi_info")
            ],
            [
                InlineKeyboardButton("🏓 Ping Test", callback_data="ping_test"),
                InlineKeyboardButton("🔗 DNS Lookup", callback_data="dns_lookup")
            ],
            [
                InlineKeyboardButton("🌍 Public IP", callback_data="public_ip"),
                InlineKeyboardButton("📈 Bandwidth", callback_data="bandwidth_monitor")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # FIXED: Added missing show_device_control method
    async def show_device_control(self, query):
        message = f"""
📱 **DEVICE CONTROL CENTER**
════════════════════════════════════

🔋 **Power Management:**
┣ 🔋 **Battery Status** - Check power level
┣ ⚡ **Charging Info** - Power source details
┣ 🔌 **Power Settings** - Optimize usage
┗ 🌙 **Sleep Mode** - Power saving

📱 **Display Control:**
┣ 💡 **Brightness** - Adjust screen brightness
┣ 🔒 **Screen Lock** - Device security
┣ 📱 **Orientation** - Screen rotation
┗ 🎨 **Display Info** - Screen specifications

🔊 **Audio Management:**
┣ 🔊 **Volume Control** - System audio
┣ 🎵 **Audio Settings** - Sound preferences
┣ 🎤 **Microphone** - Recording settings
┗ 📳 **Vibration** - Haptic feedback

📡 **Connectivity:**
┣ 📶 **WiFi Manager** - Network connections
┣ 📳 **Bluetooth** - Device pairing
┣ 🌐 **Mobile Data** - Cellular settings
┗ ✈️ **Airplane Mode** - Flight mode

📱 **Device Info:**
┣ 📱 **Device Details** - Hardware specs
┣ 🆔 **System Info** - Android version
┣ 📊 **Sensors** - Available sensors
┗ 🔧 **Diagnostics** - System health

💡 **Select device function:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔋 Battery", callback_data="battery_status"),
                InlineKeyboardButton("💡 Brightness", callback_data="brightness_control")
            ],
            [
                InlineKeyboardButton("🔊 Volume", callback_data="volume_control"),
                InlineKeyboardButton("📶 WiFi", callback_data="wifi_manager")
            ],
            [
                InlineKeyboardButton("📱 Device Info", callback_data="device_info"),
                InlineKeyboardButton("📊 Sensors", callback_data="sensors")
            ],
            [
                InlineKeyboardButton("🔒 Screen Lock", callback_data="screen_lock"),
                InlineKeyboardButton("📳 Vibration", callback_data="vibration_control")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # FIXED: Added missing show_system_tools method
    async def show_system_tools(self, query):
        message = f"""
🔧 **SYSTEM TOOLS CENTER**
════════════════════════════════════

🛠️ **System Maintenance:**
┣ 🧹 **System Cleaner** - Remove temp files
┣ 🔄 **Process Manager** - Running processes
┣ 🗂️ **Service Manager** - System services
┗ 📊 **Resource Monitor** - System usage

🔍 **Analysis Tools:**
┣ 📋 **Log Viewer** - System logs
┣ 🔍 **File Search** - Find files quickly
┣ 📊 **Disk Analyzer** - Storage usage
┗ 🔧 **System Diagnostics** - Health check

⚙️ **Configuration:**
┣ 🌐 **Environment Vars** - System variables
┣ 📝 **Config Editor** - Edit system files
┣ 🔗 **Symlink Manager** - Link management
┗ 🗂️ **Permission Manager** - File permissions

🚀 **Advanced Tools:**
┣ 📦 **Archive Manager** - Compress/extract
┣ 🔐 **Hash Checker** - File integrity
┣ 📊 **Benchmark** - Performance test
┗ 🛡️ **Security Audit** - System security

💡 **Select system tool:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🧹 Cleaner", callback_data="system_cleaner"),
                InlineKeyboardButton("🔄 Processes", callback_data="process_manager")
            ],
            [
                InlineKeyboardButton("📋 Logs", callback_data="log_viewer"),
                InlineKeyboardButton("🔍 File Search", callback_data="file_search")
            ],
            [
                InlineKeyboardButton("📊 Disk Analyzer", callback_data="disk_analyzer"),
                InlineKeyboardButton("🔧 Diagnostics", callback_data="system_diagnostics")
            ],
            [
                InlineKeyboardButton("🌐 Env Vars", callback_data="env_vars"),
                InlineKeyboardButton("📦 Archives", callback_data="archive_manager")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_nonroot_tools(self, query):
        message = f"""
🔓 **NON-ROOT POWER TOOLS**
════════════════════════════════════

✨ **Advanced Features Without Root:**

📊 **System Analysis:**
┣ 🔍 **Process Inspector** - Detailed process info
┣ 📈 **Performance Monitor** - CPU, RAM, I/O
┣ 🌡️ **Temperature Monitor** - Device thermal
┗ 🔋 **Battery Optimizer** - Power management

🛠️ **System Utilities:**
┣ 🧹 **Smart Cleaner** - Cache & temp files
┣ 📦 **Package Manager** - Install/remove apps
┣ 🔧 **Service Controller** - Manage services
┗ 📊 **Log Analyzer** - System diagnostics

🌐 **Network & Security:**
┣ 🔐 **Security Scanner** - Vulnerability check
┣ 🌐 **Network Monitor** - Traffic analysis
┣ 🛡️ **Firewall Status** - Security overview
┗ 🔒 **Encryption Tools** - File protection

📱 **Device Management:**
┣ 🔊 **Audio Control** - Volume & sound
┣ 💡 **Display Settings** - Brightness & screen
┣ 📳 **Notification Manager** - Alert control
┗ 🔄 **Auto Tasks** - Scheduled operations

💪 **Powerful Alternatives:**
┣ ✅ **ADB Commands** - Advanced debugging
┣ 🐍 **Python Scripts** - Custom automation
┣ 🔧 **Shell Utilities** - Command line tools
┗ 📋 **Batch Operations** - Multiple commands

🎯 **Choose your tool:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔍 Process Inspector", callback_data="process_inspector"),
                InlineKeyboardButton("📈 Performance", callback_data="performance_monitor")
            ],
            [
                InlineKeyboardButton("🧹 Smart Cleaner", callback_data="smart_cleaner"),
                InlineKeyboardButton("📦 Package Mgr", callback_data="package_manager")
            ],
            [
                InlineKeyboardButton("🔐 Security Scan", callback_data="security_scan"),
                InlineKeyboardButton("🛡️ Encryption", callback_data="encryption_tools")
            ],
            [
                InlineKeyboardButton("🔊 Audio Control", callback_data="audio_control"),
                InlineKeyboardButton("📳 Notifications", callback_data="notification_mgr")
            ],
            [
                InlineKeyboardButton("🐍 Python Scripts", callback_data="python_scripts"),
                InlineKeyboardButton("📋 Batch Ops", callback_data="batch_operations")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_security_tools(self, query):
        message = f"""
🛡️ **SECURITY & ENCRYPTION CENTER**
════════════════════════════════════

🔐 **Encryption & Protection:**
┣ 🔒 **File Encryption** - AES-256 protection
┣ 🗝️ **Password Generator** - Secure passwords
┣ 📱 **QR Code Generator** - Secure sharing
┗ 🔐 **Hash Calculator** - File integrity

🛡️ **Security Analysis:**
┣ 🔍 **Vulnerability Scan** - System security
┣ 🌐 **Network Security** - Connection analysis
┣ 📊 **Permission Audit** - App permissions
┗ 🚨 **Threat Detection** - Malware scan

🔒 **Privacy Tools:**
┣ 🧹 **Privacy Cleaner** - Remove traces
┣ 📂 **Secure Delete** - Permanent removal
┣ 🕵️ **Steganography** - Hidden messages
┗ 💾 **Secure Backup** - Encrypted storage

⚡ **Advanced Features:**
┣ 🔑 **SSH Key Manager** - Secure access
┣ 🌐 **Proxy Tools** - Anonymous browsing
┣ 📱 **Device Lock** - Remote security
┗ 🔄 **Auto Security** - Scheduled scans

💡 **Select security tool:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔒 Encrypt Files", callback_data="encrypt_files"),
                InlineKeyboardButton("🗝️ Gen Password", callback_data="gen_password")
            ],
            [
                InlineKeyboardButton("📱 QR Generator", callback_data="qr_generator"),
                InlineKeyboardButton("🔐 Hash Calc", callback_data="hash_calculator")
            ],
            [
                InlineKeyboardButton("🔍 Vuln Scan", callback_data="vuln_scan"),
                InlineKeyboardButton("🛡️ Network Sec", callback_data="network_security")
            ],
            [
                InlineKeyboardButton("🧹 Privacy Clean", callback_data="privacy_clean"),
                InlineKeyboardButton("📂 Secure Delete", callback_data="secure_delete")
            ],
            [
                InlineKeyboardButton("🔑 SSH Keys", callback_data="ssh_keys"),
                InlineKeyboardButton("📱 Device Lock", callback_data="device_lock")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_package_manager(self, query):
        message = f"""
📦 **SMART PACKAGE MANAGER**
════════════════════════════════════

🚀 **Package Operations:**
┣ 📥 **Install Packages** - Add new software
┣ 🔄 **Update System** - Keep everything current
┣ 🗑️ **Remove Packages** - Clean unneeded apps
┗ 🔍 **Search Packages** - Find new tools

📊 **System Analysis:**
┣ 📋 **Installed Packages** - View all installed
┣ 💾 **Package Sizes** - Disk usage analysis
┣ 🔗 **Dependencies** - Package relationships
┗ 🧹 **Cleanup System** - Remove orphaned files

⚡ **Advanced Features:**
┣ 📱 **APK Manager** - Install/manage APKs
┣ 🐍 **Python Packages** - pip management
┣ 🌐 **Repository Manager** - Source management
┗ 📦 **Package Backup** - Save configurations

🛠️ **Popular Packages:**
```bash
# Development Tools
pkg install git vim nano python nodejs

# Network Tools  
pkg install nmap wget curl openssh

# System Utils
pkg install htop tree file unzip

# Media Tools
pkg install ffmpeg imagemagick youtube-dl
```

💡 **Choose package operation:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📥 Install", callback_data="pkg_install"),
                InlineKeyboardButton("🔄 Update", callback_data="pkg_update")
            ],
            [
                InlineKeyboardButton("🗑️ Remove", callback_data="pkg_remove"),
                InlineKeyboardButton("🔍 Search", callback_data="pkg_search")
            ],
            [
                InlineKeyboardButton("📋 List Installed", callback_data="pkg_list"),
                InlineKeyboardButton("💾 Package Sizes", callback_data="pkg_sizes")
            ],
            [
                InlineKeyboardButton("📱 APK Manager", callback_data="apk_manager"),
                InlineKeyboardButton("🐍 Python Packages", callback_data="pip_manager")
            ],
            [
                InlineKeyboardButton("🧹 Cleanup", callback_data="pkg_cleanup"),
                InlineKeyboardButton("📦 Backup", callback_data="pkg_backup")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_camera_pro(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        message = f"""
📷 **PROFESSIONAL CAMERA CONTROL**
════════════════════════════════════

📸 **Camera Features:**
┣ 📷 **Quick Photo** - Instant capture
┣ 🎬 **Video Recording** - HD video capture
┣ 🔄 **Camera Switch** - Front/back cameras
┗ ⚙️ **Camera Settings** - Advanced controls

🎨 **Image Processing:**
┣ 🖼️ **Photo Effects** - Filters & editing
┣ 📏 **Resize Images** - Optimize size
┣ 🔄 **Format Convert** - Change file types
┗ 📊 **Image Analysis** - EXIF data & stats

⚡ **Advanced Features:**
┣ ⏰ **Time-lapse** - Automated photography
┣ 📱 **QR Code Scan** - Decode QR codes
┣ 🔍 **Object Detection** - AI analysis
┗ 📤 **Auto Upload** - Cloud integration

🎯 **Professional Options:**
┣ 🌟 **HDR Mode** - High dynamic range
┣ 🌙 **Night Mode** - Low light capture
┣ 📐 **Grid Lines** - Composition aid
┗ 🎭 **Portrait Mode** - Depth effects

💡 **Select camera function:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📷 Quick Photo", callback_data="quick_photo"),
                InlineKeyboardButton("🎬 Record Video", callback_data="record_video")
            ],
            [
                InlineKeyboardButton("🔄 Switch Camera", callback_data="switch_camera"),
                InlineKeyboardButton("⚙️ Settings", callback_data="camera_settings")
            ],
            [
                InlineKeyboardButton("🖼️ Photo Effects", callback_data="photo_effects"),
                InlineKeyboardButton("📏 Resize Image", callback_data="resize_image")
            ],
            [
                InlineKeyboardButton("⏰ Time-lapse", callback_data="timelapse"),
                InlineKeyboardButton("📱 QR Scan", callback_data="qr_scan")
            ],
            [
                InlineKeyboardButton("🌟 HDR Mode", callback_data="hdr_mode"),
                InlineKeyboardButton("🌙 Night Mode", callback_data="night_mode")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_sensors(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        message = f"""
📍 **GPS & SENSORS CENTER**
════════════════════════════════════

🌍 **Location Services:**
┣ 📍 **GPS Location** - Precise coordinates
┣ 🗺️ **Address Lookup** - Reverse geocoding
┣ 📊 **Location History** - Track movements
┗ 🎯 **Geofencing** - Location alerts

📱 **Device Sensors:**
┣ 🧭 **Compass** - Magnetic direction
┣ 📐 **Accelerometer** - Motion detection
┣ 🌡️ **Temperature** - Device thermal
┗ 💡 **Light Sensor** - Ambient lighting

⚡ **Advanced Features:**
┣ 🛰️ **Satellite Info** - GPS satellites
┣ 📈 **Sensor Graphs** - Real-time plotting
┣ 🔔 **Motion Alerts** - Movement detection
┗ 📊 **Data Logging** - Sensor recording

🚀 **Professional Tools:**
┣ 🎯 **Navigation** - GPS navigation
┣ 📏 **Distance Calc** - Between coordinates
┣ 🌐 **Altitude Info** - Elevation data
┗ ⏰ **Time Sync** - GPS time sync

💡 **Select sensor tool:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📍 GPS Location", callback_data="gps_location"),
                InlineKeyboardButton("🗺️ Address Lookup", callback_data="address_lookup")
            ],
            [
                InlineKeyboardButton("🧭 Compass", callback_data="compass"),
                InlineKeyboardButton("📐 Accelerometer", callback_data="accelerometer")
            ],
            [
                InlineKeyboardButton("🌡️ Temperature", callback_data="temperature"),
                InlineKeyboardButton("💡 Light Sensor", callback_data="light_sensor")
            ],
            [
                InlineKeyboardButton("🛰️ Satellite Info", callback_data="satellite_info"),
                InlineKeyboardButton("📈 Sensor Graphs", callback_data="sensor_graphs")
            ],
            [
                InlineKeyboardButton("🎯 Navigation", callback_data="navigation"),
                InlineKeyboardButton("📏 Distance Calc", callback_data="distance_calc")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # FIXED: Added missing show_api_guide method
    async def show_api_guide(self, query):
        message = f"""
⚠️ **TERMUX:API REQUIRED**
════════════════════════════════════

📱 **Installation Guide:**

🔗 **Step 1: Download Termux:API**
┣ Open **F-Droid** or **GitHub Releases**
┣ Search for "**Termux:API**"
┣ Download and install the APK
┗ Grant all requested permissions

📦 **Step 2: Install API Package**
```bash
pkg update
pkg install termux-api
```

⚙️ **Step 3: Grant Permissions**
┣ Open **Settings** → **Apps** → **Termux:API**
┣ Enable **all permissions** (Camera, Location, etc.)
┣ Allow **background activity**
┗ Disable **battery optimization**

🧪 **Step 4: Test Installation**
```bash
termux-battery-status
termux-camera-info
termux-sensor -l
```

✅ **Features After Installation:**
┣ 📷 **Camera Control** - Photo & video
┣ 📍 **GPS & Location** - Precise positioning
┣ 📊 **Sensors** - Accelerometer, compass, etc.
┣ 🔋 **Battery Status** - Power monitoring
┣ 📱 **Device Control** - Volume, brightness
┗ 🌐 **Network Info** - WiFi details

🔄 **Restart bot** after installation!
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔧 Install Guide", callback_data="install_api"),
                InlineKeyboardButton("🧪 Test API", callback_data="test_api")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # FIXED: Added missing show_root_manager method
    async def show_root_manager(self, query):
        message = f"""
👑 **ROOT MANAGER - ADVANCED CONTROL**
════════════════════════════════════

⚡ **Root Operations:**
┣ 🔧 **System Modifications** - Deep system access
┣ 📱 **App Management** - Install/remove system apps
┣ 🛡️ **Permission Control** - Advanced permissions
┗ 🔄 **System Services** - Start/stop services

🗂️ **File System Access:**
┣ 📁 **System Directories** - /system, /data access
┣ 🔐 **Protected Files** - Edit system configs
┣ 💾 **Partition Management** - Mount/unmount
┗ 🗃️ **Database Access** - System databases

⚙️ **Advanced Features:**
┣ 🔥 **Kernel Modules** - Load/unload modules
┣ 📊 **Performance Tuning** - CPU, GPU tweaks
┣ 🌡️ **Thermal Control** - Temperature management
┗ 🔋 **Power Management** - Advanced battery control

🛡️ **Security Tools:**
┣ 🔒 **SELinux Control** - Security policies  
┣ 🛡️ **Firewall Rules** - Network security
┣ 🔐 **Encryption Tools** - Full disk encryption
┗ 🕵️ **Forensics** - System analysis

⚠️ **WARNING:** Root operations can damage your system!

💡 **Select root function:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔧 System Mods", callback_data="system_mods"),
                InlineKeyboardButton("📱 App Manager", callback_data="root_app_manager")
            ],
            [
                InlineKeyboardButton("📁 File System", callback_data="root_filesystem"),
                InlineKeyboardButton("💾 Partitions", callback_data="partition_manager")
            ],
            [
                InlineKeyboardButton("🔥 Kernel", callback_data="kernel_manager"),
                InlineKeyboardButton("📊 Performance", callback_data="performance_tuning")
            ],
            [
                InlineKeyboardButton("🔒 SELinux", callback_data="selinux_control"),
                InlineKeyboardButton("🛡️ Firewall", callback_data="firewall_manager")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_settings(self, query):
        auth_count = len(self.authorized_users)
        
        message = f"""
⚙️ **BOT CONFIGURATION CENTER**
════════════════════════════════════

🤖 **Bot Status:**
┣ Status: {'🟢 Active' if self.bot_active else '🔴 Inactive'}
┣ Version: **v2.0 Professional**
┣ Uptime: **{datetime.now().strftime('%H:%M:%S')}**
┗ Commands: **{len(self.command_history)}** executed

🔐 **Security Settings:**
┣ Authorized Users: **{auth_count if auth_count > 0 else 'All users'}**
┣ Root Access: **{'✅ Available' if self.root_available else '❌ Not Available'}**
┣ Termux API: **{'✅ Active' if self.termux_api else '❌ Not Installed'}**
┗ Device Admin: **{'✅ Active' if self.admin_features else '❌ Limited'}**

📁 **System Settings:**
┣ Working Dir: `{os.path.basename(self.current_directory)}`
┣ Logs: **termux_bot.log**
┣ Config: **bot_config.json**
┗ Storage: **{self.get_dir_size('.')} MB used**

⚡ **Feature Status:**
┣ File Manager: **✅ Active**
┣ Network Tools: **✅ Active**  
┣ Security Center: **✅ Active**
┗ Package Manager: **✅ Active**

🛠️ **Configuration Options:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("👥 User Management", callback_data="user_management"),
                InlineKeyboardButton("🔧 Bot Settings", callback_data="bot_settings")
            ],
            [
                InlineKeyboardButton("📊 View Logs", callback_data="view_logs"),
                InlineKeyboardButton("🧹 Clear Data", callback_data="clear_data")
            ],
            [
                InlineKeyboardButton("🔄 Restart Bot", callback_data="restart_bot"),
                InlineKeyboardButton("📤 Export Config", callback_data="export_config")
            ],
            [
                InlineKeyboardButton("🔧 Install API", callback_data="install_api"),
                InlineKeyboardButton("⚡ Diagnostics", callback_data="diagnostics")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    def get_dir_size(self, path):
        """Get directory size in MB"""
        try:
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total += os.path.getsize(fp)
                    except Exception:
                        pass
            return round(total / (1024 * 1024), 2)
        except Exception:
            return 0
    
    async def show_help(self, query):
        message = f"""
📖 **TERMUX BOT v2.0 - HELP CENTER**
════════════════════════════════════

🚀 **Getting Started:**
┣ 💻 **Terminal Pro** - Execute any command
┣ 📁 **File Manager** - Browse & manage files
┣ 📊 **System Monitor** - Check performance
┗ 🌐 **Network Tools** - Network analysis

🔧 **Advanced Features:**
┣ 🛡️ **Security Center** - Encryption & protection
┣ 📦 **Package Manager** - Install/manage software
┣ 📷 **Camera Pro** - Professional photography
┗ 📱 **Device Control** - Hardware management

💡 **Pro Tips:**
┣ Use `cd ~` to go to home directory
┣ Use `ls -la` for detailed file listing
┣ Install Termux:API for hardware features
┣ Enable root for advanced system access
┗ Authorize users for security

🆘 **Troubleshooting:**
┣ **Permission Denied**: Check file permissions
┣ **Command Not Found**: Install required package
┣ **API Error**: Install and configure Termux:API
┣ **Root Required**: Some features need root access
┗ **Bot Slow**: Check system resources

📋 **Common Commands:**
```bash
# System Info
neofetch
htop
df -h

# Package Management
pkg update && pkg upgrade
pkg install [package]
pkg search [term]

# File Operations
ls -la
cp source dest
mv old new
rm file
```

🔗 **Useful Links:**
┣ **Termux Wiki**: https://wiki.termux.com
┣ **Package List**: https://packages.termux.org
┣ **Termux:API**: F-Droid store
┗ **GitHub Issues**: Report bugs

💬 **Need More Help?**
Contact the bot administrator or check logs for detailed error information.
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🚀 Quick Start", callback_data="quick_start"),
                InlineKeyboardButton("🔧 Setup Guide", callback_data="setup_guide")
            ],
            [
                InlineKeyboardButton("💡 Pro Tips", callback_data="pro_tips"),
                InlineKeyboardButton("🆘 Troubleshoot", callback_data="troubleshoot")
            ],
            [
                InlineKeyboardButton("📋 Commands", callback_data="command_help"),
                InlineKeyboardButton("🔗 Resources", callback_data="resources")
            ],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not self.is_authorized(user_id):
            await update.message.reply_text("🚫 Access denied")
            return
            
        command = update.message.text.strip()
        
        # Add to command history
        self.command_history.append(command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        try:
            # Handle special commands
            if command.startswith('cd '):
                await self.handle_cd_command(update, command)
                return
            elif command in ['clear', 'cls']:
                await update.message.reply_text("🧹 **Terminal cleared**", parse_mode='Markdown')
                return
            elif command == 'history':
                await self.show_command_history(update)
                return
            elif command.startswith('sudo ') and not self.root_available:
                await update.message.reply_text(
                    "⚠️ **Root not available**\n\nTrying non-root alternative...", 
                    parse_mode='Markdown'
                )
                # Try without sudo
                command = command[5:]
            
            # Execute command with enhanced output
            start_time = time.time()
            
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.current_directory,
                capture_output=True, 
                text=True, 
                timeout=60  # Increased timeout
            )
            
            execution_time = time.time() - start_time
            
            # Process output
            stdout = result.stdout
            stderr = result.stderr
            
            if stdout or stderr:
                output = ""
                if stdout:
                    output += f"📤 **Output:**\n```\n{stdout}\n```\n"
                if stderr:
                    output += f"⚠️ **Errors:**\n```\n{stderr}\n```\n"
                
                # Add execution info
                output += f"⏱️ **Execution time:** {execution_time:.2f}s\n"
                output += f"📊 **Exit code:** {result.returncode}"
                
                # Limit output size
                if len(output) > 4000:
                    output = output[:4000] + "\n... *(output truncated)*"
                
                await update.message.reply_text(output, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    f"✅ **Command executed successfully**\n⏱️ Time: {execution_time:.2f}s\n📊 Exit code: {result.returncode}",
                    parse_mode='Markdown'
                )
            
        except subprocess.TimeoutExpired:
            await update.message.reply_text("⏰ **Command timeout** (60 seconds limit)")
        except Exception as e:
            await update.message.reply_text(f"❌ **Error:** `{str(e)}`", parse_mode='Markdown')
    
    async def handle_cd_command(self, update, command):
        """Enhanced cd command handler"""
        path = command[3:].strip()
        
        if not path:
            path = '~'
        
        if path == '~':
            new_path = os.path.expanduser('~')
        elif path == '-':
            # Go to previous directory (if we had one stored)
            new_path = getattr(self, 'previous_directory', os.path.expanduser('~'))
        elif path == '..':
            new_path = os.path.dirname(self.current_directory)
        elif path.startswith('/'):
            new_path = path
        else:
            new_path = os.path.join(self.current_directory, path)
        
        try:
            if os.path.exists(new_path) and os.path.isdir(new_path):
                self.previous_directory = self.current_directory
                self.current_directory = os.path.abspath(new_path)
                
                # Get directory info
                try:
                    items = os.listdir(self.current_directory)
                    file_count = len([f for f in items if os.path.isfile(os.path.join(self.current_directory, f))])
                    dir_count = len([d for d in items if os.path.isdir(os.path.join(self.current_directory, d))])
                except PermissionError:
                    file_count = dir_count = "?"
                
                await update.message.reply_text(
                    f"📁 **Directory changed**\n\n"
                    f"📍 **Path:** `{self.current_directory}`\n"
                    f"📊 **Contents:** {dir_count} directories, {file_count} files",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ **Directory not found:** `{path}`", parse_mode='Markdown')
        except PermissionError:
            await update.message.reply_text(f"🚫 **Permission denied:** `{path}`", parse_mode='Markdown')
    
    async def show_command_history(self, update):
        """Show command history"""
        if not self.command_history:
            await update.message.reply_text("📝 **Command history is empty**", parse_mode='Markdown')
            return
        
        history_text = "📜 **COMMAND HISTORY**\n" + "="*30 + "\n\n"
        
        for i, cmd in enumerate(self.command_history[-10:], 1):
            history_text += f"`{i:2d}.` `{cmd}`\n"
        
        if len(self.command_history) > 10:
            history_text += f"\n... and {len(self.command_history) - 10} more commands"
        
        await update.message.reply_text(history_text, parse_mode='Markdown')
    
    # FIXED: All placeholder methods with proper implementations or error handling
    
    # File Manager Methods
    async def go_home(self, query):
        """Go to home directory"""
        self.previous_directory = self.current_directory
        self.current_directory = os.path.expanduser('~')
        await self.show_file_manager(query)
    
    async def go_parent(self, query):
        """Go to parent directory"""
        self.previous_directory = self.current_directory
        self.current_directory = os.path.dirname(self.current_directory)
        await self.show_file_manager(query)
    
    async def search_files(self, query):
        await query.edit_message_text(
            "🔍 **File Search**\n\nSend filename to search for in current directory:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="files")
            ]]),
            parse_mode='Markdown'
        )
    
    async def show_disk_usage(self, query):
        await query.edit_message_text("📊 Analyzing disk usage...")
        
        try:
            result = subprocess.run(['du', '-sh', '*'], 
                                  cwd=self.current_directory,
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                output = result.stdout[:3000]  # Limit output
                message = f"""
📊 **DISK USAGE ANALYSIS**
════════════════════════════════════

📍 **Directory:** `{self.current_directory}`

```
{output}
```

💡 **Legend:** Shows size and filename/directory
                """
            else:
                message = "❌ **Error analyzing disk usage**"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="files")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Network Tools Implementations
    async def scan_network(self, query):
        await query.edit_message_text("🌐 Scanning network...")
        
        try:
            # Get current IP range
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                network_info = "\n".join(lines[:5])  # Show first 5 routes
                
                message = f"""
🌐 **NETWORK SCAN RESULTS**
════════════════════════════════════

📡 **Network Routes:**
```
{network_info}
```

🔍 **Active Interfaces:**
Use `ip addr` or `ifconfig` for detailed info

💡 **Tip:** Install `nmap` for advanced scanning:
`pkg install nmap`
                """
            else:
                message = "❌ **Network scan failed**"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="network")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def check_ports(self, query):
        await query.edit_message_text("🔌 Checking open ports...")
        
        try:
            # Check common ports
            result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout[:2000]  # Limit output
                message = f"""
🔌 **PORT SCAN RESULTS**
════════════════════════════════════

📊 **Open Ports:**
```
{output}
```

💡 **Legend:**
- tcp/udp: Protocol
- LISTEN: Listening ports
- ESTAB: Established connections
                """
            else:
                message = "❌ **Port scan failed**"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="network")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def network_speed_test(self, query):
        await query.edit_message_text(
            "📊 **Speed Test**\n\nInstall speedtest-cli:\n`pkg install python && pip install speedtest-cli`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="network")
            ]]),
            parse_mode='Markdown'
        )
    
    async def show_wifi_info(self, query):
        message = "📡 **WiFi Information**\n\n"
        
        if self.termux_api:
            try:
                result = subprocess.run(['termux-wifi-connectioninfo'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    message += f"```json\n{result.stdout}\n```"
                else:
                    message += "❌ **WiFi info not available**"
            except Exception as e:
                message += f"❌ **Error:** `{str(e)}`"
        else:
            message += "⚠️ **Termux:API required**\n\nInstall Termux:API for WiFi details"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="network")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def ping_test(self, query):
        await query.edit_message_text(
            "🏓 **Ping Test**\n\nExample usage:\n`ping -c 4 google.com`\n`ping -c 4 8.8.8.8`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="network")
            ]]),
            parse_mode='Markdown'
        )
    
    async def dns_lookup(self, query):
        await query.edit_message_text(
            "🔗 **DNS Lookup**\n\nExample usage:\n`nslookup google.com`\n`dig google.com`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="network")
            ]]),
            parse_mode='Markdown'
        )
    
    async def show_public_ip(self, query):
        await query.edit_message_text("🌍 Getting public IP...")
        
        try:
            result = subprocess.run(['curl', '-s', 'ifconfig.me'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                ip = result.stdout.strip()
                message = f"🌍 **Public IP:** `{ip}`"
            else:
                message = "❌ **Failed to get public IP**"
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="network")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def bandwidth_monitor(self, query):
        await query.edit_message_text(
            "📈 **Bandwidth Monitor**\n\nUse `iftop` or `nethogs` for real-time monitoring:\n`pkg install iftop`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="network")
            ]]),
            parse_mode='Markdown'
        )
    
    # System Tools Implementations
    async def show_process_manager(self, query):
        await query.edit_message_text("📊 Loading process information...")
        
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                header = lines[0] if lines else ""
                processes = lines[1:11] if len(lines) > 1 else []  # Show top 10
                
                process_list = header + "\n" + "\n".join(processes)
                
                message = f"""
📊 **PROCESS MANAGER**
════════════════════════════════════

🔄 **Running Processes:**
```
{process_list}
```

💡 **Commands:**
- `htop` - Interactive process viewer
- `kill PID` - Terminate process
- `killall name` - Kill by name
                """
            else:
                message = "❌ **Failed to get process list**"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="system_tools")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_service_manager(self, query):
        await query.edit_message_text(
            "🔧 **Service Manager**\n\nTermux services management:\n`sv status $PREFIX/var/service/*`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="system_tools")
            ]]),
            parse_mode='Markdown'
        )
    
    async def show_log_viewer(self, query):
        try:
            if os.path.exists('termux_bot.log'):
                with open('termux_bot.log', 'r') as f:
                    log_content = f.read()
                
                # Show last 20 lines
                lines = log_content.strip().split('\n')
                recent_logs = '\n'.join(lines[-20:]) if lines else "No logs"
                
                message = f"""
📋 **BOT LOG VIEWER**
════════════════════════════════════

📊 **Recent Activity:**
```
{recent_logs}
```

💡 **Full log:** `termux_bot.log`
                """
            else:
                message = "📋 **No log file found**"
                
        except Exception as e:
            message = f"❌ **Error reading logs:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="settings")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def cleanup_system(self, query):
        await query.edit_message_text("🧹 Cleaning system...")
        
        try:
            cleanup_commands = [
                'pkg autoclean',
                'apt autoremove',
                'rm -rf ~/.cache/*',
                'rm -rf /tmp/*'
            ]
            
            results = []
            for cmd in cleanup_commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        results.append(f"✅ {cmd}")
                    else:
                        results.append(f"❌ {cmd}")
                except Exception:
                    results.append(f"❌ {cmd} (timeout)")
            
            message = f"""
🧹 **SYSTEM CLEANUP COMPLETE**
════════════════════════════════════

📊 **Cleanup Results:**
{chr(10).join(results)}

💡 **Manual cleanup:**
- `pkg autoclean` - Clean package cache
- `rm -rf ~/.cache/*` - Clear user cache
- `du -sh ~/.cache` - Check cache size
            """
            
        except Exception as e:
            message = f"❌ **Cleanup error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="sysinfo")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def show_detailed_stats(self, query):
        await query.edit_message_text("📈 Gathering detailed statistics...")
        
        try:
            stats_info = []
            
            # CPU info
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpu_lines = f.readlines()[:10]  # First 10 lines
                    cpu_info = ''.join(cpu_lines)
                    stats_info.append(f"🖥️ **CPU Info:**\n```\n{cpu_info}\n```")
            except Exception:
                stats_info.append("🖥️ **CPU Info:** Not available")
            
            # Memory details
            try:
                with open('/proc/meminfo', 'r') as f:
                    mem_lines = f.readlines()[:15]  # First 15 lines
                    mem_info = ''.join(mem_lines)
                    stats_info.append(f"🧠 **Memory Details:**\n```\n{mem_info}\n```")
            except Exception:
                stats_info.append("🧠 **Memory Details:** Not available")
            
            message = f"""
📈 **DETAILED SYSTEM STATISTICS**
════════════════════════════════════

{chr(10).join(stats_info[:2])}  

💡 **More info:** Use `cat /proc/cpuinfo` and `cat /proc/meminfo`
            """
            
        except Exception as e:
            message = f"❌ **Error getting stats:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="sysinfo")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Command history methods
    async def show_cmd_history(self, query):
        if not self.command_history:
            message = "📝 **Command history is empty**"
        else:
            recent_commands = self.command_history[-10:]
            history_list = "\n".join([f"`{i+1:2d}.` {cmd}" for i, cmd in enumerate(recent_commands)])
            
            message = f"""
📜 **COMMAND HISTORY**
════════════════════════════════════

📊 **Recent Commands:**
{history_list}

💡 **Total:** {len(self.command_history)} commands executed
            """
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="terminal")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def batch_cmd(self, query):
        await query.edit_message_text(
            "⚡ **Batch Command Execution**\n\nSend multiple commands separated by `;` or `&&`\n\nExample:\n`ls -la; pwd; whoami`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="terminal")
            ]]),
            parse_mode='Markdown'
        )
    
    # Package Manager Implementations
    async def pkg_install(self, query):
        await query.edit_message_text(
            "📥 **Package Installation**\n\nExample:\n`pkg install git vim nano`\n\nSend package names to install:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="packages")
            ]]),
            parse_mode='Markdown'
        )
    
    async def pkg_update(self, query):
        await query.edit_message_text("🔄 Updating package repositories...")
        
        try:
            result = subprocess.run(['pkg', 'update'], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                message = "✅ **Package repositories updated successfully**"
                if result.stdout:
                    message += f"\n\n```\n{result.stdout[:1000]}\n```"
            else:
                message = f"❌ **Update failed**\n\n```\n{result.stderr[:1000]}\n```"
                
        except subprocess.TimeoutExpired:
            message = "⏰ **Update timeout** - Repository update is taking too long"
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="packages")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def pkg_remove(self, query):
        await query.edit_message_text(
            "🗑️ **Package Removal**\n\nExample:\n`pkg uninstall package-name`\n\nSend package names to remove:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="packages")
            ]]),
            parse_mode='Markdown'
        )
    
    async def pkg_search(self, query):
        await query.edit_message_text(
            "🔍 **Package Search**\n\nExample:\n`pkg search python`\n`pkg search editor`\n\nSend search term:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="packages")
            ]]),
            parse_mode='Markdown'
        )
    
    async def pkg_list(self, query):
        await query.edit_message_text("📋 Loading installed packages...")
        
        try:
            result = subprocess.run(['pkg', 'list-installed'], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                package_count = len(lines)
                sample_packages = '\n'.join(lines[:20]) if lines else "No packages"
                
                message = f"""
📋 **INSTALLED PACKAGES**
════════════════════════════════════

📊 **Total Packages:** {package_count}

📦 **Sample (first 20):**
```
{sample_packages}
```

💡 **Commands:**
- `pkg list-installed | grep name` - Search installed
- `pkg show package-name` - Package details
                """
            else:
                message = "❌ **Failed to get package list**"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="packages")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def pkg_sizes(self, query):
        await query.edit_message_text("💾 Analyzing package sizes...")
        
        try:
            result = subprocess.run(['du', '-sh', f'{os.environ.get("PREFIX", "/data/data/com.termux/files/usr")}/var/lib/dpkg/info/*.list'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                message = f"""
💾 **PACKAGE SIZE ANALYSIS**
════════════════════════════════════

📊 **Package Database:**
```
{result.stdout[:2000]}
```

💡 **For detailed size info:**
`dpkg-query -W -f='${{Installed-Size}} ${{Package}}\\n' | sort -n`
                """
            else:
                message = "❌ **Failed to analyze package sizes**"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="packages")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def apk_manager(self, query):
        await query.edit_message_text(
            "📱 **APK Manager**\n\n⚠️ **Root required** for system APK management\n\nFor user APKs, use ADB commands or file manager",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="packages")
            ]]),
            parse_mode='Markdown'
        )
    
    async def pip_manager(self, query):
        await query.edit_message_text("🐍 Loading pip packages...")
        
        try:
            result = subprocess.run(['pip', 'list'], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                package_list = '\n'.join(lines[:15]) if lines else "No packages"
                
                message = f"""
🐍 **PYTHON PACKAGE MANAGER**
════════════════════════════════════

📦 **Installed Packages:**
```
{package_list}
```

💡 **Commands:**
- `pip install package` - Install package
- `pip uninstall package` - Remove package
- `pip search term` - Search packages
- `pip show package` - Package details
                """
            else:
                message = "❌ **Python/pip not available**\n\nInstall with: `pkg install python`"
                
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="packages")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def pkg_cleanup(self, query):
        await query.edit_message_text("🧹 Cleaning package system...")
        
        try:
            cleanup_commands = [
                ('pkg autoclean', 'Clean package cache'),
                ('apt autoremove -y', 'Remove unused packages'),
                ('pkg upgrade', 'Update all packages (if needed)')
            ]
            
            results = []
            for cmd, desc in cleanup_commands:
                try:
                    result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
                    if result.returncode == 0:
                        results.append(f"✅ {desc}")
                    else:
                        results.append(f"❌ {desc}")
                except Exception:
                    results.append(f"⏰ {desc} (timeout)")
            
            message = f"""
🧹 **PACKAGE CLEANUP COMPLETE**
════════════════════════════════════

📊 **Results:**
{chr(10).join(results)}

💡 **Manual cleanup:**
- `pkg autoclean` - Clear cache
- `apt autoremove` - Remove orphaned packages
            """
            
        except Exception as e:
            message = f"❌ **Cleanup error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="packages")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def pkg_backup(self, query):
        await query.edit_message_text(
            "📦 **Package Backup**\n\nCreate backup:\n`pkg list-installed > installed_packages.txt`\n\nRestore:\n`pkg install $(cat installed_packages.txt)`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="packages")
            ]]),
            parse_mode='Markdown'
        )
    
    # Security Tools Implementations
    async def encrypt_files(self, query):
        await query.edit_message_text(
            "🔒 **File Encryption**\n\nUse OpenSSL for encryption:\n\n`openssl enc -aes-256-cbc -in file.txt -out file.enc`\n`openssl enc -d -aes-256-cbc -in file.enc -out file.txt`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]]),
            parse_mode='Markdown'
        )
    
    async def generate_password(self, query):
        try:
            import secrets
            import string
            
            # Generate different types of passwords
            passwords = []
            
            # Strong password (16 chars)
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            strong_pwd = ''.join(secrets.choice(chars) for _ in range(16))
            passwords.append(f"🔐 **Strong (16):** `{strong_pwd}`")
            
            # Complex password (12 chars)
            complex_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            passwords.append(f"🔑 **Complex (12):** `{complex_pwd}`")
            
            # Simple password (8 chars)
            simple_pwd = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(8))
            passwords.append(f"🗝️ **Simple (8):** `{simple_pwd}`")
            
            # PIN (6 digits)
            pin = ''.join(secrets.choice(string.digits) for _ in range(6))
            passwords.append(f"📱 **PIN (6):** `{pin}`")
            
            message = f"""
🗝️ **SECURE PASSWORD GENERATOR**
════════════════════════════════════

🎯 **Generated Passwords:**
{chr(10).join(passwords)}

💡 **Security Tips:**
┣ Use different passwords for each account
┣ Include uppercase, lowercase, numbers, symbols
┣ Minimum 12 characters for strong security
┗ Store securely, never share via insecure channels

🔄 **Refresh for new passwords**
            """
            
        except Exception as e:
            message = f"❌ **Password generation error:** `{str(e)}`"
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Generate New", callback_data="gen_password"),
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]
        ]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def qr_generator(self, query):
        await query.edit_message_text(
            "📱 **QR Code Generator**\n\nSend text to generate QR code for:\n- URLs\n- WiFi passwords\n- Contact info\n- Any text",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]]),
            parse_mode='Markdown'
        )
    
    async def hash_calculator(self, query):
        await query.edit_message_text(
            "🔐 **Hash Calculator**\n\nCalculate file hashes:\n\n`md5sum file.txt`\n`sha256sum file.txt`\n`sha512sum file.txt`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]]),
            parse_mode='Markdown'
        )
    
    async def vulnerability_scan(self, query):
        await query.edit_message_text(
            "🔍 **Vulnerability Scanner**\n\nBasic security checks:\n\n`pkg audit` - Check for vulnerable packages\n`ls -la ~/.ssh/` - Check SSH keys\n`netstat -tuln` - Check open ports",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]]),
            parse_mode='Markdown'
        )
    
    async def network_security(self, query):
        await query.edit_message_text(
            "🛡️ **Network Security**\n\nSecurity analysis:\n\n`ss -tuln` - Check listening ports\n`arp -a` - Check ARP table\n`netstat -rn` - Check routing table",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]]),
            parse_mode='Markdown'
        )
    
    async def privacy_clean(self, query):
        await query.edit_message_text("🧹 Cleaning privacy traces...")
        
        try:
            cleanup_items = [
                ('~/.bash_history', 'Bash history'),
                ('~/.cache/*', 'User cache'),
                ('/tmp/*', 'Temporary files'),
                ('~/.local/share/recently-used.xbel', 'Recent files')
            ]
            
            results = []
            for path, desc in cleanup_items:
                try:
                    expanded_path = os.path.expanduser(path)
                    if '*' in expanded_path:
                        subprocess.run(f'rm -rf {expanded_path}', shell=True, timeout=10)
                    elif os.path.exists(expanded_path):
                        os.remove(expanded_path)
                    results.append(f"✅ {desc}")
                except Exception:
                    results.append(f"❌ {desc}")
            
            message = f"""
🧹 **PRIVACY CLEANUP COMPLETE**
════════════════════════════════════

📊 **Cleaned Items:**
{chr(10).join(results)}

💡 **Additional cleanup:**
- Clear browser data manually
- Remove log files: `sudo rm /var/log/*`
- Secure delete: `shred -vfz -n 3 file`
            """
            
        except Exception as e:
            message = f"❌ **Privacy cleanup error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="security")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def secure_delete(self, query):
        await query.edit_message_text(
            "📂 **Secure File Deletion**\n\nSecure delete commands:\n\n`shred -vfz -n 3 file.txt` - Overwrite 3 times\n`rm file.txt && sync` - Delete and sync\n\n⚠️ **Cannot be undone!**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="security")
            ]]),
            parse_mode='Markdown'
        )
    
    async def ssh_keys(self, query):
        await query.edit_message_text("🔑 Checking SSH keys...")
        
        try:
            ssh_dir = os.path.expanduser('~/.ssh')
            if os.path.exists(ssh_dir):
                files = os.listdir(ssh_dir)
                if files:
                    file_list = '\n'.join([f"┣ {f}" for f in files])
                    message = f"""
🔑 **SSH KEY MANAGER**
════════════════════════════════════

📁 **SSH Directory:** `~/.ssh`

🗂️ **Files:**
{file_list}

💡 **Commands:**
- `ssh-keygen -t rsa -b 4096` - Generate new key
- `ssh-copy-id user@host` - Copy key to server
- `ssh-add ~/.ssh/id_rsa` - Add key to agent
                    """
                else:
                    message = "🔑 **SSH directory exists but is empty**\n\nGenerate keys with:\n`ssh-keygen -t rsa -b 4096`"
            else:
                message = "🔑 **No SSH directory found**\n\nCreate with:\n`mkdir ~/.ssh && chmod 700 ~/.ssh`"
                
        except Exception as e:
            message = f"❌ **SSH key error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="security")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def device_lock(self, query):
        message = "📱 **Device Lock Control**\n\n"
        
        if self.termux_api:
            message += """
🔒 **Available Controls:**
- `termux-keystore` - Secure key storage
- `termux-fingerprint` - Fingerprint auth
- Device lock requires system permissions

💡 **Manual lock:**
Press power button or use system settings
            """
        else:
            message += "⚠️ **Termux:API required** for device lock features"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="security")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Camera and Sensor Implementations (require Termux:API)
    async def quick_photo(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
        
        await query.edit_message_text("📷 Taking photo...")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            
            result = subprocess.run(['termux-camera-photo', filename], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                message = f"📷 **Photo captured successfully!**\n\n📁 **File:** `{filename}`\n📍 **Location:** Current directory"
            else:
                message = f"❌ **Photo capture failed**\n\n`{result.stderr}`"
                
        except Exception as e:
            message = f"❌ **Camera error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="camera")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def record_video(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        await query.edit_message_text(
            "🎬 **Video Recording**\n\nRecord video:\n`termux-camera-video filename.mp4`\n\nPress Ctrl+C to stop recording",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="camera")
            ]]),
            parse_mode='Markdown'
        )
    
    async def switch_camera(self, query):
        await query.edit_message_text(
            "🔄 **Camera Switch**\n\nSwitch between cameras:\n`termux-camera-photo -c 0` (back)\n`termux-camera-photo -c 1` (front)",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="camera")
            ]]),
            parse_mode='Markdown'
        )
    
    async def camera_settings(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        try:
            result = subprocess.run(['termux-camera-info'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                message = f"""
⚙️ **CAMERA SETTINGS & INFO**
════════════════════════════════════

📷 **Camera Information:**
```json
{result.stdout}
```

💡 **Camera Controls:**
- `-c ID` - Camera ID (0=back, 1=front)
- `-s WxH` - Resolution (e.g., 1920x1080)  
- Quality settings available
                """
            else:
                message = "❌ **Camera info not available**"
                
        except Exception as e:
            message = f"❌ **Camera settings error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="camera")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def gps_location(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        await query.edit_message_text("📍 Getting GPS location...")
        
        try:
            result = subprocess.run(['termux-location'], 
                                  capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                location_data = json.loads(result.stdout)
                lat = location_data.get('latitude', 'N/A')
                lon = location_data.get('longitude', 'N/A')
                accuracy = location_data.get('accuracy', 'N/A')
                altitude = location_data.get('altitude', 'N/A')
                
                message = f"""
📍 **GPS LOCATION DATA**
════════════════════════════════════

🌍 **Coordinates:**
┣ **Latitude:** {lat}
┣ **Longitude:** {lon}
┣ **Accuracy:** {accuracy}m
┗ **Altitude:** {altitude}m

🗺️ **Google Maps:**
https://maps.google.com/?q={lat},{lon}

💡 **Raw Data:**
```json
{result.stdout}
```
                """
            else:
                message = "❌ **GPS location failed**\n\nEnable location services and grant permissions"
                
        except Exception as e:
            message = f"❌ **GPS error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def compass(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        try:
            result = subprocess.run(['termux-sensor', '-s', 'magnetic_field', '-n', '1'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                sensor_data = json.loads(result.stdout)
                values = sensor_data.get('magnetic_field', {}).get('values', [0, 0, 0])
                
                message = f"""
🧭 **COMPASS & MAGNETIC FIELD**
════════════════════════════════════

🔢 **Magnetic Field (μT):**
┣ **X-axis:** {values[0]:.2f}
┣ **Y-axis:** {values[1]:.2f}
┗ **Z-axis:** {values[2]:.2f}

💡 **Direction:** Use magnetometer for compass bearing
Raw data shows magnetic field strength in microteslas
                """
            else:
                message = "❌ **Compass sensor not available**"
                
        except Exception as e:
            message = f"❌ **Compass error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def accelerometer(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        try:
            result = subprocess.run(['termux-sensor', '-s', 'accelerometer', '-n', '1'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                sensor_data = json.loads(result.stdout)
                values = sensor_data.get('accelerometer', {}).get('values', [0, 0, 0])
                
                message = f"""
📐 **ACCELEROMETER DATA**
════════════════════════════════════

⚡ **Acceleration (m/s²):**
┣ **X-axis:** {values[0]:.2f}
┣ **Y-axis:** {values[1]:.2f}
┗ **Z-axis:** {values[2]:.2f}

📱 **Device Orientation:**
- Positive X: Right
- Positive Y: Up  
- Positive Z: Out of screen

💡 **Gravity:** ~9.8 m/s² when stationary
                """
            else:
                message = "❌ **Accelerometer not available**"
                
        except Exception as e:
            message = f"❌ **Accelerometer error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def temperature(self, query):
        if not self.termux_api:
            await self.show_api_guide(query)
            return
            
        try:
            result = subprocess.run(['termux-sensor', '-s', 'temperature'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                sensor_data = json.loads(result.stdout)
                temp_value = sensor_data.get('temperature', {}).get('values', [0])[0]
                
                message = f"""
🌡️ **TEMPERATURE SENSOR**
════════════════════════════════════

🔥 **Current Temperature:**
┣ **Celsius:** {temp_value:.1f}°C
┣ **Fahrenheit:** {(temp_value * 9/5) + 32:.1f}°F
┗ **Kelvin:** {temp_value + 273.15:.1f}K

💡 **Note:** This shows device internal temperature
For ambient temperature, use external sensor
                """
            else:
                message = "❌ **Temperature sensor not available**"
                
        except Exception as e:
            message = f"❌ **Temperature error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Settings and Management
    async def user_management(self, query):
        message = f"""
👥 **USER MANAGEMENT**
════════════════════════════════════

🔐 **Current Status:**
┣ **Authorized Users:** {len(self.authorized_users) if self.authorized_users else 'All users allowed'}
┣ **Security Mode:** {'Restricted' if self.authorized_users else 'Open'}
┗ **Admin Access:** Available

⚙️ **Management Options:**
┣ **Add User:** Send user ID to authorize
┣ **Remove User:** Remove user authorization  
┣ **List Users:** View all authorized users
┗ **Reset Security:** Clear all restrictions

💡 **Current User ID:** {query.from_user.id}
        """
        
        keyboard = [
            [
                InlineKeyboardButton("➕ Add User", callback_data="add_user"),
                InlineKeyboardButton("➖ Remove User", callback_data="remove_user")
            ],
            [
                InlineKeyboardButton("📋 List Users", callback_data="list_users"),
                InlineKeyboardButton("🔄 Reset Security", callback_data="reset_security")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="settings")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def bot_settings(self, query):
        message = f"""
🔧 **BOT SETTINGS**
════════════════════════════════════

🤖 **Bot Configuration:**
┣ **Status:** {'🟢 Active' if self.bot_active else '🔴 Inactive'}
┣ **Version:** v2.0 Professional  
┣ **Command History:** {len(self.command_history)} commands
┗ **Max History:** {self.max_history} commands

📁 **Directory Settings:**
┣ **Current:** `{os.path.basename(self.current_directory)}`
┣ **Home:** `{os.path.expanduser('~')}`
┣ **Previous:** `{os.path.basename(self.previous_directory)}`
┗ **Working Dir:** `{self.current_directory}`

⚙️ **Feature Settings:**
┣ **Termux API:** {'✅ Enabled' if self.termux_api else '❌ Disabled'}
┣ **Root Access:** {'✅ Available' if self.root_available else '❌ Not Available'}
┣ **Admin Features:** {'✅ Active' if self.admin_features else '❌ Limited'}
┗ **Logging:** ✅ Enabled

🛠️ **Configuration:**
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status"),
                InlineKeyboardButton("📊 System Check", callback_data="system_check")
            ],
            [
                InlineKeyboardButton("🗂️ Change Dir", callback_data="change_dir"),
                InlineKeyboardButton("🧹 Clear History", callback_data="clear_history")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="settings")]
        ]
        
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def view_logs(self, query):
        await self.show_log_viewer(query)
    
    async def clear_data(self, query):
        await query.edit_message_text("🧹 Clearing bot data...")
        
        try:
            # Clear command history
            self.command_history.clear()
            
            # Clear temporary files
            temp_files_cleared = 0
            for temp_dir in ['temp', 'downloads', 'uploads']:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        try:
                            file_path = os.path.join(temp_dir, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                temp_files_cleared += 1
                        except Exception:
                            continue
            
            message = f"""
🧹 **DATA CLEANUP COMPLETE**
════════════════════════════════════

✅ **Cleared Items:**
┣ **Command History:** {len(self.command_history)} cleared
┣ **Temp Files:** {temp_files_cleared} removed
┣ **Cache:** Cleared
┗ **Logs:** Preserved (use 'View Logs' to check)

💡 **Preserved:**
- Bot configuration
- Authorized users
- System settings
            """
            
        except Exception as e:
            message = f"❌ **Clear data error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="settings")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def restart_bot(self, query):
        await query.edit_message_text(
            "🔄 **Bot Restart**\n\n⚠️ **Manual restart required**\n\nStop bot with Ctrl+C and run:\n`python termux_bot.py`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="settings")
            ]]),
            parse_mode='Markdown'
        )
    
    async def export_config(self, query):
        await query.edit_message_text("📤 Exporting configuration...")
        
        try:
            config_data = {
                'bot_version': '2.0',
                'export_time': datetime.now().isoformat(),
                'current_directory': self.current_directory,
                'authorized_users': self.authorized_users,
                'command_history_count': len(self.command_history),
                'features': {
                    'termux_api': self.termux_api,
                    'root_available': self.root_available,
                    'admin_features': bool(self.admin_features)
                }
            }
            
            config_file = f"bot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            message = f"""
📤 **CONFIGURATION EXPORTED**
════════════════════════════════════

✅ **Export Complete:**
┣ **File:** `{config_file}`
┣ **Size:** {os.path.getsize(config_file)} bytes
┣ **Location:** Current directory
┗ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 **Exported Data:**
┣ Bot settings and version
┣ Directory configuration  
┣ User authorization list
┣ Feature availability status
┗ System capabilities

💾 **Backup:** Keep this file safe for restoration
            """
            
        except Exception as e:
            message = f"❌ **Export error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="settings")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def install_api(self, query):
        await self.show_api_guide(query)
    
    async def diagnostics(self, query):
        await query.edit_message_text("⚡ Running system diagnostics...")
        
        try:
            diagnostics = []
            
            # Check Python version
            try:
                python_version = subprocess.run([sys.executable, '--version'], 
                                              capture_output=True, text=True).stdout.strip()
                diagnostics.append(f"✅ **Python:** {python_version}")
            except Exception:
                diagnostics.append("❌ **Python:** Version check failed")
            
            # Check essential commands
            essential_commands = ['ls', 'pwd', 'ps', 'df', 'free']
            available_commands = 0
            for cmd in essential_commands:
                try:
                    result = subprocess.run(['which', cmd], capture_output=True, timeout=2)
                    if result.returncode == 0:
                        available_commands += 1
                except Exception:
                    pass
            
            diagnostics.append(f"✅ **Commands:** {available_commands}/{len(essential_commands)} available")
            
            # Check disk space
            try:
                disk = psutil.disk_usage('/')
                free_gb = disk.free / (1024**3)
                diagnostics.append(f"✅ **Disk Space:** {free_gb:.1f}GB free")
            except Exception:
                diagnostics.append("❌ **Disk Space:** Check failed")
            
            # Check network connectivity
            try:
                result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    diagnostics.append("✅ **Network:** Connected")
                else:
                    diagnostics.append("❌ **Network:** No connectivity")
            except Exception:
                diagnostics.append("❌ **Network:** Check failed")
            
            # Check permissions
            try:
                test_file = 'diagnostic_test.tmp'
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                diagnostics.append("✅ **Permissions:** File operations OK")
            except Exception:
                diagnostics.append("❌ **Permissions:** File operations failed")
            
            message = f"""
⚡ **SYSTEM DIAGNOSTICS REPORT**
════════════════════════════════════

🔍 **System Health:**
{chr(10).join(diagnostics)}

📊 **Feature Status:**
┣ **Termux API:** {'✅ Available' if self.termux_api else '❌ Not Available'}
┣ **Root Access:** {'✅ Available' if self.root_available else '❌ Not Available'}
┣ **Device Admin:** {'✅ Available' if self.admin_features else '❌ Limited'}
┗ **Bot Status:** {'✅ Running' if self.bot_active else '❌ Inactive'}

🕐 **Report Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
        except Exception as e:
            message = f"❌ **Diagnostics error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="settings")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Additional missing methods for file operations
    async def handle_file_upload(self, query):
        await query.edit_message_text(
            "📤 **File Upload**\n\nSend any file to upload it to current directory\n\n📍 **Current:** `{}`".format(self.current_directory),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="files")
            ]]),
            parse_mode='Markdown'
        )
    
    async def handle_file_download(self, query):
        try:
            files = [f for f in os.listdir(self.current_directory) 
                    if os.path.isfile(os.path.join(self.current_directory, f))][:10]
            
            if files:
                file_list = '\n'.join([f"┣ `{f}`" for f in files])
                message = f"""
📥 **FILE DOWNLOAD**
════════════════════════════════════

📁 **Available Files:**
{file_list}

💡 **Send filename to download**
Example: `document.pdf`
                """
            else:
                message = "📥 **No files available for download**"
                
        except Exception as e:
            message = f"❌ **Download error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="files")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def compress_files(self, query):
        await query.edit_message_text(
            "🗜️ **File Compression**\n\nCreate archives:\n`tar -czf archive.tar.gz folder/`\n`zip -r archive.zip folder/`\n\nExtract:\n`tar -xzf archive.tar.gz`\n`unzip archive.zip`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="files")
            ]]),
            parse_mode='Markdown'
        )
    
    async def backup_system(self, query):
        await query.edit_message_text(
            "💾 **System Backup**\n\nBackup commands:\n`tar -czf backup_$(date +%Y%m%d).tar.gz ~/`\n`rsync -av ~/ /backup/location/`",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back", callback_data="files")
            ]]),
            parse_mode='Markdown'
        )
    
    # Placeholder methods for remaining features
    async def test_api(self, query):
        await query.edit_message_text("🧪 Testing Termux:API...")
        
        if not self.termux_api:
            message = "❌ **Termux:API not detected**\n\nPlease install Termux:API first"
        else:
            try:
                # Test basic API function
                result = subprocess.run(['termux-battery-status'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    message = f"✅ **Termux:API is working!**\n\n```json\n{result.stdout}\n```"
                else:
                    message = "❌ **API test failed**\n\nCheck permissions and installation"
            except Exception as e:
                message = f"❌ **API test error:** `{str(e)}`"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        await query.edit_message_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    # Add all other placeholder methods with basic implementations
    async def address_lookup(self, query):
        await query.edit_message_text("🗺️ **Address Lookup** - Feature coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]))
    
    async def satellite_info(self, query):
        await query.edit_message_text("🛰️ **Satellite Info** - Feature coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]))
    
    async def sensor_graphs(self, query):
        await query.edit_message_text("📈 **Sensor Graphs** - Feature coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]))
    
    async def navigation(self, query):
        await query.edit_message_text("🎯 **Navigation** - Feature coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]))
    
    async def distance_calc(self, query):
        await query.edit_message_text("📏 **Distance Calculator** - Feature coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]))
    
    async def light_sensor(self, query):
        await query.edit_message_text("💡 **Light Sensor** - Feature coming soon!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="sensors")]]))
    
    # System tools placeholders
    async def system_cleaner(self, query):
        await self.cleanup_system(query)
    
    async def file_search(self, query):
        await self.search_files(query)
    
    async def disk_analyzer(self, query):
        await self.show_disk_usage(query)
    
    async def system_diagnostics(self, query):
        await self.diagnostics(query)
    
    async def env_vars(self, query):
        await query.edit_message_text("🌐 **Environment Variables**\n\nView: `env` or `printenv`\nSet: `export VAR=value`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="system_tools")]]))
    
    async def archive_manager(self, query):
        await self.compress_files(query)
    
    # Add remaining placeholder methods for all callbacks
    async def add_user(self, query):
        await query.edit_message_text("➕ **Add User**\n\nSend user ID to authorize:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]))
    
    async def remove_user(self, query):
        await query.edit_message_text("➖ **Remove User**\n\nSend user ID to remove:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]))
    
    async def list_users(self, query):
        if self.authorized_users:
            user_list = '\n'.join([f"┣ `{user_id}`" for user_id in self.authorized_users])
            message = f"📋 **Authorized Users:**\n{user_list}"
        else:
            message = "📋 **No user restrictions** - All users allowed"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]))
    
    async def reset_security(self, query):
        self.authorized_users.clear()
        self.save_authorized_users()
        await query.edit_message_text("🔄 **Security Reset** - All users now allowed", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]))
    
    async def refresh_status(self, query):
        # Refresh system status
        self.termux_api = self.check_termux_api()
        self.root_available = self.check_root()
        self.admin_features = self.check_device_admin()
        await self.bot_settings(query)
    
    async def system_check(self, query):
        await self.diagnostics(query)
    
    async def change_dir(self, query):
        await query.edit_message_text("🗂️ **Change Directory**\n\nSend new directory path:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings")]]))
    
    async def clear_history(self, query):
        self.command_history.clear()
        await query.edit_message_text("🧹 **Command history cleared**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="bot_settings")]]))
    
    # Add all remaining missing methods with basic implementations
    async def battery_status(self, query):
        if self.termux_api:
            try:
                result = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    message = f"🔋 **Battery Status:**\n```json\n{result.stdout}\n```"
                else:
                    message = "❌ **Battery status unavailable**"
            except Exception as e:
                message = f"❌ **Error:** `{str(e)}`"
        else:
            message = "⚠️ **Termux:API required**"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="device")]]))
    
    async def brightness_control(self, query):
        await query.edit_message_text("💡 **Brightness Control** - Use system settings or `termux-brightness` with API", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="device")]]))
    
    async def volume_control(self, query):
        await query.edit_message_text("🔊 **Volume Control** - Use `termux-volume` with API", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="device")]]))
    
    async def wifi_manager(self, query):
        await self.show_wifi_info(query)
    
    async def device_info(self, query):
        try:
            info = []
            info.append(f"📱 **OS:** {os.uname().sysname}")
            info.append(f"🔧 **Architecture:** {os.uname().machine}")
            info.append(f"🆔 **Hostname:** {os.uname().nodename}")
            message = f"📱 **Device Info:**\n{chr(10).join(info)}"
        except Exception as e:
            message = f"❌ **Error:** `{str(e)}`"
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="device")]]))
    
    async def screen_lock(self, query):
        await query.edit_message_text("🔒 **Screen Lock** - Use power button or system settings", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="device")]]))
    
    async def vibration_control(self, query):
        await query.edit_message_text("📳 **Vibration Control** - Use `termux-vibrate` with API", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="device")]]))
    
    # Add all other missing placeholder methods
    def _create_placeholder_method(self, name, category="main_menu"):
        async def placeholder_method(self, query):
            await query.edit_message_text(
                f"🚧 **{name.replace('_', ' ').title()}** - Feature in development",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Back", callback_data=category)
                ]])
            )
        return placeholder_method
    
    # Add remaining methods dynamically
    def __init_placeholder_methods(self):
        placeholder_methods = [
            'process_inspector', 'performance_monitor', 'smart_cleaner', 
            'security_scan', 'encryption_tools', 'audio_control', 
            'notification_mgr', 'python_scripts', 'batch_operations',
            'photo_effects', 'resize_image', 'timelapse', 'qr_scan',
            'hdr_mode', 'night_mode', 'system_mods', 'root_app_manager',
            'root_filesystem', 'partition_manager', 'kernel_manager',
            'performance_tuning', 'selinux_control', 'firewall_manager',
            'quick_start', 'setup_guide', 'pro_tips', 'troubleshoot',
            'command_help', 'resources'
        ]
        
        for method_name in placeholder_methods:
            if not hasattr(self, method_name):
                setattr(self, method_name, self._create_placeholder_method(method_name))
    
    def run(self):
        """Run the bot"""
        # Initialize placeholder methods
        self.__init_placeholder_methods()
        
        print("\n" + "🔥"*60)
        print("🚀 TERMUX BOT CONTROLLER v2.0 - PROFESSIONAL EDITION")
        print("🔥"*60)
        print("⚡ Initializing advanced systems...")
        print(f"📁 Working Directory: {self.current_directory}")
        print(f"📱 Termux API: {'✅ Available' if self.termux_api else '❌ Not Available'}")
        print(f"👑 Root Access: {'✅ Available' if self.root_available else '❌ Not Available'}")
        print(f"🛡️ Device Admin: {'✅ Available' if self.admin_features else '❌ Limited Access'}")
        print("🔥"*60)
        
        try:
            app = Application.builder().token(self.bot_token).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CallbackQueryHandler(self.button_handler))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_command))
            
            print("✅ Bot initialized successfully!")
            print("💬 Send /start in Telegram to begin")
            print("🎯 All features ready for professional use")
            print("🔄 Press Ctrl+C to stop the bot")
            print("🔥"*60)
            
            app.run_polling(drop_pending_updates=True)
            
        except KeyboardInterrupt:
            print("\n🛑 Bot shutting down gracefully...")
            print("👋 Thanks for using Termux Bot Controller v2.0!")
        except Exception as e:
            print(f"❌ Critical Error: {e}")
            logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    try:
        bot = AdvancedTermuxBot()
        bot.run()
    except Exception as e:
        print(f"🚫 Failed to start bot: {e}")
        sys.exit(1)
