import os
import json
import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient, DESCENDING

# ================= CONFIG =================
# Environment variables for sensitive data
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
MONGO_URI = os.environ.get("MONGO_URI", "YOUR_MONGO_URI")
AADHAAR_API_KEY = os.environ.get("AADHAAR_API_KEY", "YOUR_AADHAAR_API_KEY")

AUTHORIZED_USERS_STR = os.environ.get("AUTHORIZED_USERS", "")
AUTHORIZED_USERS = [int(uid.strip()) for uid in AUTHORIZED_USERS_STR.split(',') if uid.strip()]

WELCOME_IMG = "https://files.catbox.moe/lm8e6u.png"
WELCOME_MESSAGE_DM = """👤 INVESTIGATOR: {user_id_name}
RANK: 🍃 GENIN
╔═══ ◎ ᴍᴀɴɢᴇᴋʏᴏ ᴅᴀᴛᴀ ꜱᴄᴀɴ ᴇɴɢɪɴᴇ ◎
║ ᴅᴇᴇᴘ ᴡᴇʙ • ᴅᴀʀᴋ ᴛʀᴀɪʟꜱ • ʀᴇᴀʟ-ᴛɪᴍᴇ ɪɴᴛᴇʟ
╚═══════════════════════
👁️ ꜱʜᴀʀɪɴɢᴀɴ ꜰᴇᴀᴛᴜʀᴇ ᴜɴʟᴏᴄᴋᴇᴅ
⚡️ ᴘʜᴏɴᴇ ʟᴏᴏᴋᴜᴘ
⚡️ ꜱᴍꜱ ʟᴏᴏᴋᴜᴘ
⚡️ ᴀᴀᴅʜᴀᴀʀ ʟᴏᴏᴋᴜᴘ
⚡️ ꜰᴀᴍɪʟʏ ʟᴏᴏᴋᴜᴘ
⚡️ ᴠᴇʜɪᴄʟᴇ ʟᴏᴏᴋᴜᴘ
🔥 ᴏᴘᴇʀᴀᴛɪɴɢ ɪɴ ᴜᴄʜɪʜᴀ ᴍᴏᴅᴇ…
ᴏɴᴇ ᴛᴀᴘ → ᴅᴀᴛᴀ ᴜɴʀᴀᴠᴇʟꜱ
ᴏɴᴇ ʟᴏᴏᴋ → ɪɴꜰᴏ ᴇxᴘᴏꜱᴇᴅ
ᴏɴᴇ ᴄᴏᴍᴍᴀɴᴅ → ᴄʟᴀɴ ᴘᴏᴡᴇʀ ᴜɴʟᴇᴀꜱʜᴇᴅ
"""
API_BASE_URL = "http://api.subhxcosmo.in/api"
API_KEY_VNIOX = "VNIOX"
API_KEY_VINOX2 = "VINOX2"

# NEW AADHAAR API CONFIG
AADHAAR_API_URL = "https://database-sigma-nine.vercel.app/aadhaar/{term}"

# =========================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
mongo = MongoClient(MONGO_URI)
db = mongo["tg_bot"]
users_col = db["users"]
usage_col = db["usage"]

# ================= HELPERS =================
def save_user(u):
    users_col.update_one({"id": u.id}, {"$set": {"id": u.id, "name": u.first_name or "", "username": u.username or "N/A"}}, upsert=True)

def inc_usage(uid):
    usage_col.update_one({"id": uid}, {"$inc": {"count": 1}}, upsert=True)

def footer_buttons():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("👨‍💻 MADE BY", url="https://t.me/LingTech_Dev")
    )
    return kb

def help_footer_button():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("MAKE OWN BOT", url="https://t.me/LingTech_Dev"))
    return kb

def make_api_request(api_type, term, api_key):
    try:
        if api_type == "new_aadhaar":
            url = AADHAAR_API_URL.format(term=term)
            r = requests.get(url, params={"api_key": AADHAAR_API_KEY})
        else:
            r = requests.get(API_BASE_URL, params={"key": api_key, "type": api_type, "term": term})
        
        r.raise_for_status()
        data = r.json()
        
        for key in ["owner", "cached", "proxyUsed", "attempt"]:
            data.pop(key, None)
            
        return data.get("result", data)
    except Exception as e:
        return {"error": str(e)}

# ================= HANDLERS =================
@bot.message_handler(commands=["start"])
def start(m):
    if m.chat.type != "private" or m.from_user.id not in AUTHORIZED_USERS: return
    save_user(m.from_user)
    bot.send_photo(m.chat.id, WELCOME_IMG, caption=WELCOME_MESSAGE_DM.format(user_id_name=m.from_user.first_name), reply_markup=footer_buttons())

def handle_api_command(m, api_type, api_key, usage):
    if m.chat.type != "private" or m.from_user.id not in AUTHORIZED_USERS: return
    save_user(m.from_user)
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, f"Usage: {usage}", reply_markup=footer_buttons())
        return
    
    # Removed global TG_TOTAL and TG_USERS as they are not suitable for serverless functions
    inc_usage(m.from_user.id)
    
    status_msg = bot.reply_to(m, "🔍 <b>Searching...</b>")
    
    result = make_api_request(api_type, parts[1], api_key)
    
    if "error" in result:
        bot.edit_message_text(f"❌ Error: {result["error"]}", m.chat.id, status_msg.message_id, reply_markup=footer_buttons())
    else:
        pretty = json.dumps(result, indent=2, ensure_ascii=False)
        if len(pretty) > 3900:
            pretty = pretty[:3900] + "\n\n... (Result truncated due to length)"
        try:
            bot.edit_message_text(f"<pre>{pretty}</pre>", m.chat.id, status_msg.message_id, reply_markup=footer_buttons())
        except Exception as e:
            if "message is too long" in str(e).lower():
                bot.edit_message_text("⚠️ Result is too large to display in Telegram.", m.chat.id, status_msg.message_id, reply_markup=footer_buttons())
            else:
                bot.edit_message_text(f"❌ Error displaying result: {str(e)}", m.chat.id, status_msg.message_id, reply_markup=footer_buttons())

@bot.message_handler(commands=["num"])
def num_cmd(m):
    handle_api_command(m, "mobile", API_KEY_VNIOX, "/num <phone_number>")

@bot.message_handler(commands=["tgid"])
def tgid_cmd(m):
    handle_api_command(m, "sms", API_KEY_VNIOX, "/tgid <Telegram_Numbric_Id>")

@bot.message_handler(commands=["aadhar"])
def aadhar_cmd(m):
    handle_api_command(m, "new_aadhaar", None, "/aadhar <12_Digit_Aadhar_Number>")

@bot.message_handler(commands=["family"])
def family_cmd(m):
    handle_api_command(m, "id_family", API_KEY_VNIOX, "/family <12_Digit_Aadhar_Number>")

@bot.message_handler(commands=["vehiclenum"])
def vehiclenum_cmd(m):
    handle_api_command(m, "vehicle_num", API_KEY_VNIOX, "/vehiclenum <vehicle_number>")

@bot.message_handler(commands=["help"])
def help_cmd(m):
    if m.chat.type != "private" or m.from_user.id not in AUTHORIZED_USERS: return
    help_message = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/num <10_Digit_Phone_Number> - Get mobile information\n"
        "/tgid <Telegram_Numbric_Id> - Get Mobile Number\n"
        "/aadhar <12_Digit_Aadhar_Number> - Get Aadhar number information (New API)\n"
        "/family <12_Digit_Aadhar_Number> - Get family information\n"
        "/vehiclenum <vehicle_number> - Get vehicle information\n"
        "/help - Show this help message\n\n"
        "You Make Own Bot Dm - @LingTech_Dev"
    )
    bot.reply_to(m, help_message, reply_markup=help_footer_button())

# Vercel serverless function entry point
def handler(request):
    if request.method == "POST":
        update = telebot.types.Update.de_json(request.get_json(force=True))
        bot.process_new_updates([update])
        return "", 200
    else:
        return "Hello from Telegram Bot!", 200
