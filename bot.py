import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Konfigurasi Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Konfigurasi Bot
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_CHAT_IDS = [int(id.strip()) for id in os.getenv('ALLOWED_CHAT_IDS').split(',')]

# Inisialisasi model Gemini
model = genai.GenerativeModel('gemini-pro')

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    welcome_msg = """
    🤖 *Bot AI Gemini* 🤖

    Saya adalah bot yang ditenagai oleh Google Gemini AI. Anda bisa bertanya apa saja!

    Contoh perintah:
    - /start - Memulai bot
    - /help - Menampilkan bantuan
    - Tanyakan langsung untuk berinteraksi dengan AI

    Bot dibuat untuk membantu banyak orang!
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_CHAT_IDS:
        return
    
    help_msg = """
    🆘 *Bantuan* 🆘

    Bot ini menggunakan Google Gemini AI untuk menjawab pertanyaan Anda.

    Cukup ketik pesan biasa untuk berinteraksi dengan AI.

    Perintah yang tersedia:
    - /start - Memulai bot
    - /help - Menampilkan pesan ini

    Bot ini aman dan gratis untuk digunakan!
    """
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in ALLOWED_CHAT_IDS:
        await update.message.reply_text("Maaf, Anda tidak memiliki akses ke bot ini.")
        return
    
    user_message = update.message.text
    
    try:
        # Tampilkan status "mengetik"
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Dapatkan respons dari Gemini
        response = model.generate_content(user_message)
        
        # Kirim balasan
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Maaf, terjadi kesalahan saat memproses permintaan Anda.")

def main():
    print("Memulai bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    print("Polling...")
    app.run_polling(poll_interval=3)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

if __name__ == '__main__':
    main()
