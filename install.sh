#!/bin/bash

echo "🤖 Termux Control Bot Installer"
echo "================================"

# Update packages
echo "📦 Updating packages..."
pkg update -y
pkg upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
pkg install -y python python-pip termux-api git

# Install Termux:API app if not installed
echo "📱 Checking Termux:API..."
if ! command -v termux-battery-status &> /dev/null; then
    echo "⚠️  Please install Termux:API app from Google Play Store"
    echo "   https://play.google.com/store/apps/details?id=com.termux.api"
fi

# Create bot directory
echo "📁 Creating bot directory..."
mkdir -p ~/termux-bot
cd ~/termux-bot

# Download bot files (if from remote)
# For now, user needs to copy the files manually

echo "✅ Installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy bot.py to ~/termux-bot/"
echo "2. Copy .env to ~/termux-bot/ and configure it"
echo "3. Run: cd ~/termux-bot && python bot.py"
echo ""
echo "🔧 Configuration:"
echo "- Get bot token from @BotFather on Telegram"
echo "- Get your user ID from @userinfobot on Telegram"
echo "- Edit .env file with your credentials"
echo ""
echo "🚀 To run bot: python ~/termux-bot/bot.py"
