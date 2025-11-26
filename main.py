#!/usr/bin/env python3
"""
Telegram Session Bot with USA Proxy - Fixed Version
"""

import os
import asyncio
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    SessionPasswordNeeded,
    PhoneCodeInvalid,
    PhoneNumberInvalid,
    PhoneCodeExpired
)

# Keep alive system
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "🤖 USA Proxy Bot is Running on GitHub!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()

print("🚀 Starting USA Proxy Session Bot...")

# Credentials
API_ID = int(os.environ.get("API_ID", "35779438"))
API_HASH = os.environ.get("API_HASH", "d7cf27cb37f2935c067ee5d102ee8936")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7735504871:AAEAg0Jsohy20PMZ8wtd8rXLuz8rJ4WEdoE")

# USA Proxy List
USA_PROXIES = [
    {
        "scheme": "socks5",
        "hostname": "208.102.51.6",
        "port": 1080,
        "username": None,
        "password": None
    },
    {
        "scheme": "socks5", 
        "hostname": "192.252.215.5",
        "port": 16137,
        "username": None,
        "password": None
    }
]

print(f"✅ Loaded {len(USA_PROXIES)} USA Proxies")

class SessionManager:
    def __init__(self):
        self.user_states = {}
        self.user_sessions = {}
        self.current_proxy_index = 0
        self.init_db()
    
    def init_db(self):
        try:
            conn = sqlite3.connect('sessions.db')
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS user_sessions
                         (user_id INTEGER, phone TEXT, session_file TEXT, 
                          created_date TEXT, proxy_used TEXT)''')
            conn.commit()
            conn.close()
            print("✅ Database Initialized")
        except Exception as e:
            print(f"❌ Database Error: {e}")
    
    def get_next_proxy(self):
        proxy = USA_PROXIES[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(USA_PROXIES)
        return proxy

session_manager = SessionManager()

bot = Client(
    "usa_proxy_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

@bot.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user = message.from_user
    welcome_text = f"""
**🤖 USA Proxy Session Bot**

**স্বাগতম {user.first_name}!** 🎉

🌐 **Server:** GitHub Actions (USA)
✅ **Status:** 24/7 Running

**📋 Commands:**
/create - নতুন সেশন তৈরি করুন
/status - বট স্ট্যাটাস
"""
    
    await message.reply_text(welcome_text)

@bot.on_message(filters.command("create"))
async def create_session_command(client, message: Message):
    user_id = message.from_user.id
    session_manager.user_states[user_id] = "waiting_phone"
    
    await message.reply_text(
        "**🛠️ Session Creation Started!**\n\n"
        "📱 আপনার ফোন নাম্বার দিন (country code সহ):\n"
        "**Example:** +8801XXXXXXX"
    )

@bot.on_message(filters.text & ~filters.command)
async def handle_phone_number(client, message: Message):
    user_id = message.from_user.id
    user_state = session_manager.user_states.get(user_id)
    
    if user_state == "waiting_phone":
        phone_number = message.text.strip()
        
        if not phone_number.startswith('+'):
            await message.reply_text("❌ **Invalid format!** Country code (+) দিয়ে শুরু করুন")
            return
        
        session_manager.user_sessions[user_id] = {"phone": phone_number}
        session_manager.user_states[user_id] = "creating_session"
        
        await message.reply_text(
            f"**📱 Phone Number:** {phone_number}\n\n"
            "⏳ Connecting via USA proxy..."
        )
        
        await create_user_session(client, message, user_id, phone_number)

async def create_user_session(client, message, user_id, phone_number):
    try:
        user_data = session_manager.user_sessions.get(user_id, {})
        proxy = session_manager.get_next_proxy()
        
        session_name = f"usa_user_{user_id}"
        
        user_client = Client(
            session_name=session_name,
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy
        )
        
        async with user_client:
            sent_code = await user_client.send_code(phone_number)
            
            user_data["phone_code_hash"] = sent_code.phone_code_hash
            user_data["session_name"] = session_name
            user_data["proxy_used"] = f"{proxy['hostname']}:{proxy['port']}"
            session_manager.user_sessions[user_id] = user_data
            
            session_manager.user_states[user_id] = "waiting_code"
            
            await message.reply_text(
                f"**✅ Verification Code Sent!**\n\n"
                f"📱 **Phone:** {phone_number}\n"
                f"🔢 **Code দিন:**"
            )
            
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")
        session_manager.user_states.pop(user_id, None)

@bot.on_message(filters.command("status"))
async def status_command(client, message: Message):
    await message.reply_text("**🤖 Bot Status:** ✅ Running on GitHub")

if __name__ == "__main__":
    # Start keep alive server
    keep_alive()
    print("✅ Keep Alive Server Started")
    
    print("🚀 USA Proxy Bot Starting...")
    
    try:
        bot.run()
        print("✅ Bot is running!")
    except Exception as e:
        print(f"❌ Error: {e}")
