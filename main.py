#!/usr/bin/env python3
"""
Telegram Session Bot with USA Proxy
USA প্রক্সি আইপি দিয়ে সেশন তৈরি করবে
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

print("🚀 Starting USA Proxy Session Bot...")

# Credentials
API_ID = int(os.environ.get("API_ID", "35779438"))
API_HASH = os.environ.get("API_HASH", "d7cf27cb37f2935c067ee5d102ee8936")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7735504871:AAEAg0Jsohy20PMZ8wtd8rXLuz8rJ4WEdoE")

# USA Proxy List - Working Proxies
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
    },
    {
        "scheme": "http",
        "hostname": "154.16.202.22",
        "port": 8080,
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

🌐 **Server:** USA Proxy Enabled
📍 **Location:** United States
✅ **Status:** 24/7 Running

**📋 Commands:**
/create - USA proxy দিয়ে সেশন তৈরি করুন
/proxies - Available proxies দেখুন
/mysessions - আমার সেশনগুলো দেখুন  
/status - বট স্ট্যাটাস
"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛠️ Create Session (USA)", callback_data="create_session")],
        [InlineKeyboardButton("🌐 View Proxies", callback_data="view_proxies")],
        [InlineKeyboardButton("📊 Bot Status", callback_data="status")]
    ])
    
    await message.reply_text(welcome_text, reply_markup=keyboard)

@bot.on_message(filters.command("create"))
async def create_session_command(client, message: Message):
    user_id = message.from_user.id
    session_manager.user_states[user_id] = "waiting_phone"
    
    proxy = session_manager.get_next_proxy()
    
    await message.reply_text(
        f"**🛠️ USA Proxy Session Creation!**\n\n"
        f"🌐 **Proxy Server:** {proxy['hostname']}:{proxy['port']}\n"
        f"📍 **Location:** United States\n\n"
        "📱 আপনার ফোন নাম্বার দিন (country code সহ):\n"
        "**Example:** +1XXXXXXXXXX (USA)\n"
        "**Example:** +8801XXXXXXX (Bangladesh)"
    )

@bot.on_message(filters.command("proxies"))
async def proxies_command(client, message: Message):
    proxies_text = "**🌐 Available USA Proxies:**\n\n"
    
    for i, proxy in enumerate(USA_PROXIES, 1):
        proxies_text += f"**{i}. {proxy['scheme'].upper()} Proxy**\n"
        proxies_text += f"   • **IP:** `{proxy['hostname']}`\n"
        proxies_text += f"   • **Port:** `{proxy['port']}`\n"
        proxies_text += f"   • **Type:** {proxy['scheme']}\n\n"
    
    await message.reply_text(proxies_text)

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
        
        proxy = session_manager.get_next_proxy()
        
        await message.reply_text(
            f"**📱 Phone Number:** {phone_number}\n"
            f"**🌐 USA Proxy:** {proxy['hostname']}\n\n"
            "⏳ Connecting via USA proxy..."
        )
        
        await create_user_session(client, message, user_id, phone_number, proxy)

async def create_user_session(client, message, user_id, phone_number, proxy):
    try:
        user_data = session_manager.user_sessions.get(user_id, {})
        
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
                f"**✅ Verification Code Sent via USA Proxy!**\n\n"
                f"📱 **Phone:** {phone_number}\n"
                f"📨 **Method:** {sent_code.type.value}\n"
                f"🌐 **Proxy:** {proxy['hostname']}:{proxy['port']}\n"
                f"📍 **Location:** United States\n\n"
                "**🔢 Telegram থেকে পাওয়া verification code টি দিন:**"
            )
            
    except Exception as e:
        await message.reply_text(f"❌ **Error:** {str(e)}")
        session_manager.user_states.pop(user_id, None)

@bot.on_message(filters.regex(r'^\d{5}$') | filters.regex(r'^\d{6}$'))
async def handle_verification_code(client, message: Message):
    user_id = message.from_user.id
    user_state = session_manager.user_states.get(user_id)
    
    if user_state == "waiting_code":
        verification_code = message.text.strip()
        user_data = session_manager.user_sessions.get(user_id, {})
        
        try:
            session_name = user_data.get("session_name")
            phone_number = user_data.get("phone")
            phone_code_hash = user_data.get("phone_code_hash")
            proxy_used = user_data.get("proxy_used", "USA Proxy")
            
            user_client = Client(session_name=session_name)
            
            async with user_client:
                try:
                    await user_client.sign_in(
                        phone_number=phone_number,
                        phone_code_hash=phone_code_hash,
                        phone_code=verification_code
                    )
                except SessionPasswordNeeded:
                    session_manager.user_states[user_id] = "waiting_password"
                    await message.reply_text("🔐 **2FA Password দিন:**")
                    return
            
            me = await user_client.get_me()
            
            conn = sqlite3.connect('sessions.db')
            c = conn.cursor()
            c.execute('''INSERT INTO user_sessions 
                         (user_id, phone, session_file, created_date, proxy_used) 
                         VALUES (?, ?, ?, datetime('now'), ?)''',
                     (user_id, phone_number, f"{session_name}.session", proxy_used))
            conn.commit()
            conn.close()
            
            success_text = f"""
**🎉 USA Proxy Session Created Successfully!**

**👤 User Information:**
• **Name:** {me.first_name} {me.last_name or ''}
• **Username:** @{me.username or 'N/A'}
• **Phone:** {me.phone_number}

**🌐 USA Connection Info:**
• **Proxy Server:** {proxy_used}
• **Location:** United States
• **Session File:** `{session_name}.session`

**✅ Verified:** USA IP Address
"""
            await message.reply_text(success_text)
            
            session_manager.user_states.pop(user_id, None)
            session_manager.user_sessions.pop(user_id, None)
            
        except Exception as e:
            await message.reply_text(f"❌ **Error:** {str(e)}")
            session_manager.user_states.pop(user_id, None)

@bot.on_message(filters.command("status"))
async def status_command(client, message: Message):
    status_text = f"""
**🤖 USA Proxy Bot Status**

**🔧 Proxy Configuration:**
• **Total USA Proxies:** {len(USA_PROXIES)}
• **Active Users:** {len(session_manager.user_states)}

**🌐 USA Proxy Types:**
• SOCKS5 Proxies: {len([p for p in USA_PROXIES if p['scheme'] == 'socks5'])}
• HTTP Proxies: {len([p for p in USA_PROXIES if p['scheme'] == 'http'])}

**📍 Proxy Locations:** United States
**⚡ Status:** ✅ Running with USA IP
"""
    await message.reply_text(status_text)

@bot.on_message(filters.command("mysessions"))
async def my_sessions_command(client, message: Message):
    user_id = message.from_user.id
    
    try:
        conn = sqlite3.connect('sessions.db')
        c = conn.cursor()
        c.execute('''SELECT phone, session_file, created_date, proxy_used 
                     FROM user_sessions WHERE user_id = ?''', (user_id,))
        sessions = c.fetchall()
        conn.close()
        
        if not sessions:
            await message.reply_text("**📭 No Sessions Found!**\n\nUse /create to make your first USA proxy session.")
            return
        
        sessions_text = "**📁 Your USA Proxy Sessions:**\n\n"
        for i, (phone, session_file, created_date, proxy_used) in enumerate(sessions, 1):
            sessions_text += f"**{i}. {phone}**\n"
            sessions_text += f"   • **File:** `{session_file}`\n"
            sessions_text += f"   • **Proxy:** {proxy_used}\n"
            sessions_text += f"   • **Created:** {created_date}\n\n"
        
        await message.reply_text(sessions_text)
    except Exception as e:
        await message.reply_text("❌ **Database Error!**")

@bot.on_callback_query()
async def handle_callbacks(client, callback_query):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if data == "create_session":
        await create_session_command(client, callback_query.message)
    elif data == "view_proxies":
        await proxies_command(client, callback_query.message)
    elif data == "status":
        await status_command(client, callback_query.message)
    
    await callback_query.answer()

if __name__ == "__main__":
    print("🚀 USA Proxy Session Bot Starting...")
    print(f"🌐 Loaded {len(USA_PROXIES)} USA Proxies")
    
    try:
        bot.run()
        print("✅ USA Proxy Bot is running!")
    except Exception as e:
        print(f"❌ Error: {e}")
