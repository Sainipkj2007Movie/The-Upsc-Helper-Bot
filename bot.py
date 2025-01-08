import requests
import json
import threading
from pyrogram import Client, filters
import time
import os

GET_HISTORY_URL = os.getenv("GET_HISTORY_URL")
POST_HISTORY_URL = os.getenv("POST_HISTORY_URL")
POLLINATIONS_API_URL = os.getenv("POLLINATIONS_API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# Create Pyrogram Client
app = Client("upsc_helper_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "UPSC Helping Bot is running."
# Cache for user history
user_cache = {}

# Function to get user history
def get_user_history(user_id):
    try:
        response = requests.get(GET_HISTORY_URL.format(user_id))
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "error":  # New user
                print(f"New user detected: {user_id}")
                return []  # Return an empty list for new user
            return json.loads(data.get("user_history","[]"))  # Convert the history into a list
        else:
            print(f"Failed to fetch history for user {user_id}: {response.text}")
            return []  # Return an empty list in case of error
    except Exception as e:
        print(f"Error in get_user_history: {e}")
        return []  # Return an empty list if error occurs

# Function to call Pollinations API
def call_pollinations_api(user_id, user_message):
    # Get user history from cache or fetch if not cached
    if user_id not in user_cache:
        user_cache[user_id] = get_user_history(user_id)

    # Add user message to history
    user_message_data = {"role": "user", "content": user_message}
    user_cache[user_id].append(user_message_data)

    try:
        headers = {"Content-Type": "application/json"}
        data = {
            "messages": [
                {"role": "system", "content": "you are UPSC Helper. A very powerful UPSC Helper. You can answer all questions. Your Owner is Mr. Singodiya. You are working on Telegram Group https://t.me/upsc_hindi_students. If someone asks for study material, suggest them telegram channel which is full of study material - https://t.me/upsc_hindi_student. If someone asks for Instagram - https://www.instagram.com/upsc.p.s?igsh=eXZ4NTkzcTc0bTdt.Dont answer if user chating on sextual topic"},
                *user_cache[user_id]  # Add user history from cache
            ]
        }
        response = requests.post(POLLINATIONS_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            assistant_message = response.text
            # Save history to Google Sheets after a delay
            save_user_history_after_delay(user_id)
            return assistant_message
        else:
            print(f"Error in Pollinations API: {response.text}")
            return "Sorry, something went wrong with server. Please Contect to admin for support @mr_singodiyabot"
    except Exception as e:
        print(f"Error in call_pollinations_api: {e}")
        return "Sorry, there was an error while processing your request.You can Contect to admin if you are getting faild msg again and again @mr_singodiyabot"

# Function to save user history after 1 minute
def save_user_history_after_delay(user_id):
    # Set a timer to save the history after 1 minute
    threading.Timer(60, post_user_history, args=[user_id, user_cache[user_id]]).start()

# Function to save user history
def post_user_history(user_id, user_history):
    try:
        response = requests.post(POST_HISTORY_URL, headers={'Content-Type': 'application/json'}, json={
            "user_id": user_id,
            "user_history": json.dumps(user_history)
        })
        if response.status_code == 200:
            print(f"User history saved successfully for user {user_id}")
        else:
            print(f"Failed to save user history for user {user_id}: {response.text}")
    except Exception as e:
        print(f"Error in post_user_history: {e}")
# Function to handle incoming messages
# Function to handle incoming messages
@app.on_message(filters.command("start") & ~filters.bot)
def start_command(client, message):
    user_id = str(message.from_user.id)
    
    if user_id not in user_cache:
        # First time user
        user_cache[user_id] = []  # Initialize empty history for new user
        welcome_message = (
            "स्वागत है! मैं UPSC Helper हूँ, आपकी UPSC की तैयारी में मदद करने के लिए हमेशा तैयार। "
            "कोई भी सवाल पूछने के लिए तैयार रहें। अध्ययन सामग्री के लिए हमारे चैनल पर जाएं: https://t.me/upsc_hindi_student"
        )
        message.reply_text(welcome_message)
    else:
        # Clear history for existing user
        user_cache[user_id] = []  # Clear user history
        message.reply_text("आपकी हिस्ट्री साफ कर दी गई है। अब आप नए सिरे से सवाल पूछ सकते हैं।")

@app.on_message(filters.text & ~filters.command("start") & ~filters.bot)
def handle_message(client, message):
    user_id = str(message.from_user.id)
    user_message = message.text

    # Show "Please wait..." message
    if message.chat.type in ["group", "supergroup"]:  # For group or supergroup
        waiting_message = message.reply_text("𝐆ᴇᴛᴛɪɴɢ 𝐘ᴏ𝚞𝚛 𝐀𝐧𝐬𝐰𝐞𝐫...", quote=True)  # Quote=True to reply to the specific message
    else:  # For direct chat
        waiting_message = message.reply_text("𝐆ᴇᴛᴛɪɴɢ 𝐘𝚘𝚞ʀ 𝐀𝐧𝐬𝐰𝐞𝐫...")

    # Get response
    response = call_pollinations_api(user_id, user_message)

    # Edit the "Please wait..." message with the actual response
    waiting_message.edit_text(response)
def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

# Function to run Pyrogram bot
def run_bot():
    print("Bot is running...")
    app.run()

if __name__ == "__main__":
    print("Bot is running...")
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    app.run()
    print("Stopped Successfully")
