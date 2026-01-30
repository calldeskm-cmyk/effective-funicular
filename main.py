import hmac
import hashlib
import requests
import string
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json
import codecs
import time
from datetime import datetime
from colorama import Fore, Style, init
import urllib3
import os
import sys
import base64
import signal
import threading
import psutil
import re
import subprocess
import importlib
import telebot

# GitHub Actions setup
init(autoreset=True)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Telegram bot setup
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Global variables
EXIT_FLAG = False
SUCCESS_COUNTER = 0
TARGET_ACCOUNTS = 0
RARE_COUNTER = 0
COUPLES_COUNTER = 0
RARITY_SCORE_THRESHOLD = 3
LOCK = threading.Lock()

# Folder structure
BASE_FOLDER = "./oN-Athex"
TOKENS_FOLDER = os.path.join(BASE_FOLDER, "TOKENS-JWT")
ACCOUNTS_FOLDER = os.path.join(BASE_FOLDER, "ACCOUNTS")
RARE_ACCOUNTS_FOLDER = os.path.join(BASE_FOLDER, "RARE ACCOUNTS")
COUPLES_ACCOUNTS_FOLDER = os.path.join(BASE_FOLDER, "COUPLES ACCOUNTS")
GHOST_FOLDER = os.path.join(BASE_FOLDER, "GHOST")
GHOST_ACCOUNTS_FOLDER = os.path.join(GHOST_FOLDER, "ACCOUNTS")
GHOST_RARE_FOLDER = os.path.join(GHOST_FOLDER, "RAREACCOUNT")
GHOST_COUPLES_FOLDER = os.path.join(GHOST_FOLDER, "COUPLESACCOUNT")

for folder in [BASE_FOLDER, TOKENS_FOLDER, ACCOUNTS_FOLDER, RARE_ACCOUNTS_FOLDER, COUPLES_ACCOUNTS_FOLDER, GHOST_FOLDER, GHOST_ACCOUNTS_FOLDER, GHOST_RARE_FOLDER, GHOST_COUPLES_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Configuration
REGION_LANG = {"ME": "ar","IND": "hi","ID": "id","VN": "vi","TH": "th","BD": "bn","PK": "ur","TW": "zh","CIS": "ru","SAC": "es","BR": "pt"}
REGION_URLS = {"IND": "https://client.ind.freefiremobile.com/","ID": "https://clientbp.ggblueshark.com/","BR": "https://client.us.freefiremobile.com/","ME": "https://clientbp.common.ggbluefox.com/","VN": "https://clientbp.ggblueshark.com/","TH": "https://clientbp.common.ggbluefox.com/","CIS": "https://clientbp.ggblueshark.com/","BD": "https://clientbp.ggblueshark.com/","PK": "https://clientbp.ggblueshark.com/","SG": "https://clientbp.ggblueshark.com/","SAC": "https://client.us.freefiremobile.com/","TW": "https://clientbp.ggblueshark.com/"}
hex_key = "32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533"
key = bytes.fromhex(hex_key)
hex_data = "8J+agCBQUkVNSVVNIEFDQ09VTlQgR0VORVJBVE9SIPCfkqsgQnkgU1BJREVFUklPIHwgTm90IEZvciBTYWxlIPCfkas="
client_data = base64.b64decode(hex_data).decode('utf-8')
GARENA = "QnkgQG9OQXRoZXg="

# GitHub Actions detection
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

# Telegram command handlers
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Generate Accounts', 'View Saved Accounts', 'About', 'Exit')
    bot.reply_to(message, "Welcome to Athex Account Generator!\nChoose an option:", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
/start - Start the bot
/generate - Generate new accounts
/view - View saved accounts
/help - Show this help message
/status - Show current status
"""
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['status'])
def status_command(message):
    bot.reply_to(message, f"Current status: Generated {SUCCESS_COUNTER}/{TARGET_ACCOUNTS} accounts")

@bot.message_handler(commands=['generate'])
def generate_command(message):
    # Start generation in background thread
    threading.Thread(target=run_generation, args=(message,), daemon=True).start()
    bot.reply_to(message, "Starting account generation...")

@bot.message_handler(commands=['view'])
def view_command(message):
    # Start viewing in background thread
    threading.Thread(target=run_view, args=(message,), daemon=True).start()
    bot.reply_to(message, "Viewing saved accounts...")

@bot.message_handler(commands=['about'])
def about_command(message):
    about_text = """Athex Account Generator - Tool for generating Free Fire accounts.
Features:
- Multi-region account generation
- GHOST Mode support
- Automatic JWT token generation
- Multi-threaded processing
- Safe account storage
"""
    bot.reply_to(message, about_text)

@bot.message_handler(func=lambda message: True)
def handle_menu_choice(message):
    if message.text == 'Generate Accounts':
        generate_command(message)
    elif message.text == 'View Saved Accounts':
        view_command(message)
    elif message.text == 'About':
        about_command(message)
    elif message.text == 'Exit':
        bot.reply_to(message, "Goodbye!")
    else:
        bot.reply_to(message, "Invalid option. Please choose from the menu.")

# Guest ID generation functions (exact copy from original code)
def generate_exponent_number():
    exponent_digits = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    number = random.randint(1, 99999)
    number_str = f"{number:05d}"
    exponent_str = ''.join(exponent_digits[digit] for digit in number_str)
    return exponent_str

def generate_random_name(base_name):
    exponent_part = generate_exponent_number()
    return f"{base_name[:7]}{exponent_part}"

def generate_custom_password(prefix):
    garena_decoded = base64.b64decode(GARENA).decode('utf-8')
    characters = string.ascii_uppercase + string.digits
    random_part1 = ''.join(random.choice(characters) for _ in range(5))
    random_part2 = ''.join(random.choice(characters) for _ in range(5))
    return f"{prefix}_{random_part1}_{garena_decoded}_{random_part2}"

# Core functions (exact copy from original code)
def safe_exit(signum=None, frame=None):
    global EXIT_FLAG
    EXIT_FLAG = True
    bot.send_message(message.chat.id, "Safe exit triggered. Script closing...")

signal.signal(signal.SIGINT, safe_exit)
signal.signal(signal.SIGTERM, safe_exit)

def run_generation(message):
    try:
        # Call your existing generate_accounts_flow function here
        # Example:
        # generate_accounts_flow(message=message)
        bot.reply_to(message, "Account generation completed!")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def run_view(message):
    try:
        # Call your existing view_saved_accounts function here
        # Example:
        # view_saved_accounts(message=message)
        bot.reply_to(message, "Viewing completed!")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

def print_success(message):
    bot.send_message(message.chat.id, f"✅ {message}")

def print_error(message):
    bot.send_message(message.chat.id, f"❌ {message}")

def print_warning(message):
    bot.send_message(message.chat.id, f"⚠️ {message}")

def print_rarity_found(account_data, rarity_type, reason, rarity_score):
    msg = f"""💎 RARE ACCOUNT FOUND!
🎯 Type: {rarity_type}
⭐ Rarity Score: {rarity_score}
👤 Name: {account_data['name']}
🆔 UID: {account_data['uid']}
🎮 Account ID: {account_data.get('account_id', 'N/A')}
📝 Reason: {reason}
🧵 Thread: {account_data.get('thread_id', 'N/A')}
🌍 Region: {account_data.get('region', 'N/A')}"""
    bot.send_message(message.chat.id, msg)

# Install dependencies
def install_requirements():
    required_packages = [
        'requests',
        'pycryptodome',
        'colorama',
        'urllib3',
        'psutil'
    ]
    
    print(f"🔍 Checking required packages...")
    
    for package in required_packages:
        try:
            if package == 'pycryptodome':
                import Crypto
            else:
                importlib.import_module(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"⚠️ Installing {package}...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False
    return True

def main():
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN':
        print("Please set your TELEGRAM_TOKEN environment variable")
        return
    
    if install_requirements():
        try:
            bot.polling()
        except KeyboardInterrupt:
            safe_exit()
        except Exception as e:
            print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
