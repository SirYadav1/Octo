import random
import re
import asyncio
import os
import sys
import time
from dotenv import load_dotenv
from telethon import TelegramClient, events
from colorama import Fore, Style, init
from art import text2art
from telethon.errors import FloodWaitError

# Initialize colorama and art
init(autoreset=True)

# Configure stdout to handle UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env file
load_dotenv()

# Define your API ID and API hash
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

if not api_id or not api_hash:
    raise ValueError("API_ID and API_HASH environment variables must be set")

# Define bot username
bot_username = 'OctopusEN_Bot'

# Initialize group_username and speed_mode
group_username = None
custom_delay = 5

# Create the Telegram client
client = TelegramClient('octoplay', api_id, api_hash)

# Load custom wordlist from the path specified in .env
wordlist_path = os.getenv('WORDLIST_PATH')
if not wordlist_path:
    raise ValueError("WORDLIST_PATH environment variable must be set in .env file")

try:
    with open(wordlist_path, 'r', encoding='utf-8') as file:
        word_list = set(line.strip().lower() for line in file if line.strip())
except Exception as e:
    print(f"{Fore.RED}❌ Error loading wordlist: {e}")
    sys.exit(1)

# ====================== UTILS.PY ======================
def get_valid_words(letters, pattern, word_list):
    """
    Get valid words that match the given pattern and can be formed using the given letters.

    :param letters: String of available letters
    :param pattern: Pattern to match (with underscores for unknown letters)
    :param word_list: List of valid words
    :return: List of valid words that match the pattern
    """
    try:
        pattern = pattern.lower()
        word_length = len(pattern)
        letters = letters.lower()
        possible_words = []

        # Create regex pattern from the given pattern
        regex_pattern = "^" + pattern.replace("_", ".") + "$"

        # Filter words from the custom wordlist that match the length and regex pattern
        for word in word_list:
            if len(word) == word_length and re.match(regex_pattern, word):
                if all(word.count(l) <= letters.count(l) for l in set(word)):
                    possible_words.append(word)

        return possible_words if possible_words else ""
    except Exception as e:
        print(f"{Fore.RED}❌ An error occurred in get_valid_words: {e}")
        return ""

def format_string(input_str):
    """
    Format the input string to extract and join letters.

    :param input_str: Input string containing letters
    :return: Formatted string of letters in uppercase
    """
    try:
        # Split the input string into parts
        parts = input_str.split()

        # Remove the first two elements (the number and the word "letter")
        letters = parts[2:]

        # Convert to uppercase and join
        result = "".join(letters).upper()

        return result
    except Exception as e:
        print(f"{Fore.RED}❌ An error occurred in format_string: {e}")
        return ""

# ====================== STARTUP.PY ======================
def animated_loading():
    animation = ["|", "/", "-", "\\"]
    for i in range(30):
        sys.stdout.write(f"\r{Fore.YELLOW}🚀 Starting bot... {animation[i % len(animation)]} {Fore.CYAN}{'.' * (i % 4)}")
        sys.stdout.flush()
        time.sleep(0.1)
    print(f"\r{Fore.GREEN}✅ Bot started successfully!       ")

def progress_bar():
    print(Fore.CYAN + "🔹 Initializing...")
    for i in range(1, 21):
        time.sleep(0.1)
        bar = "█" * i + "-" * (20 - i)
        sys.stdout.write(f"\r[{Fore.GREEN}{bar}{Fore.RESET}] {i*5}%")
        sys.stdout.flush()
    print("\n" + Fore.GREEN + "✅ Initialization Complete!")

def startup_banner():
    banner = text2art("OCTOMOD")
    colors = [Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]
    for line in banner.split("\n"):
        print(random.choice(colors) + line)
        time.sleep(0.1)

# ====================== MAIN.PY ======================
async def send_welcome_message():
    me = await client.get_me()
    await client.send_message('me', f"""
🎉Welcome to Octomod v1.2.1! 🎉

Hi {me.first_name} 😊,  

Thank you for choosing Octomod! The octomod bot is now active and ready to enhance your game experience. Below are the available commands to get started:  

- **`/po`** – Start the octomod bot in a group.  
- **`/eo`** – Stop the octomod bot from playing in the group.  
- **`/time <seconds>`** – Set a custom delay (in seconds) between messages.  
""")

async def notify_user(message):
    me = await client.get_me()
    await client.send_message('me', message)

async def main():
    await client.start()
    await send_welcome_message()

    @client.on(events.NewMessage(pattern='/time (\d+)', outgoing=True))
    async def set_custom_delay(event):
        global custom_delay
        delay_input = event.pattern_match.group(1).strip()
        try:
            custom_delay = int(delay_input)
            async with client.action('me', 'typing'):
                await asyncio.sleep(2)
                await client.send_message('me', f"Custom delay set to {custom_delay} seconds.")
        except ValueError:
            async with client.action('me', 'typing'):
                await asyncio.sleep(2)
                await client.send_message('me', "Invalid delay value. Please enter a valid number.")
        await event.delete()

    @client.on(events.NewMessage(pattern='/po', outgoing=True))
    async def set_group(event):
        global group_username
        try:
            group_username = event.chat_id
            print(f'{Fore.GREEN}✅ Octomod is playing in {event.chat.title}')
            await notify_user(f'Octomod is now playing in {event.chat.title}')
        except Exception as e:
            print(f"{Fore.RED}❌ An error occurred: {e}")
            await notify_user(f'An error occurred: {e}')

    @client.on(events.NewMessage(pattern='/eo', outgoing=True))
    async def end_group(event):
        global group_username
        try:
            if group_username == event.chat_id:
                group_username = None
                print(f'{Fore.YELLOW}⚠️ /end command used in {event.chat.title}')
                await notify_user(f'Octomod has stopped playing in {event.chat.title}')
        except Exception as e:
            print(f"{Fore.RED}❌ An error occurred: {e}")
            await notify_user(f'An error occurred: {e}')

    @client.on(events.NewMessage)
    async def handler(event):
        global group_username
        try:
            if group_username and event.chat_id == group_username:
                sender = await event.get_sender()
                if sender and sender.username == bot_username:
                    # Extract only the string part of the message, excluding emojis
                    message_text = re.sub(r'[^\w\s,.!?]', '', event.message.message)
                    second_last_line = message_text.split('\n')[-2].strip()
                    content = format_string(second_last_line)
                    last_line = message_text.split('\n')[-1].strip()
                    result = get_valid_words(content, last_line.replace(" ", ""), word_list)

                    if not result:
                        print(f"{Fore.YELLOW}⚠️ No word found. Clicking 'Pass' button...")
                        buttons = await event.get_buttons()
                        for button_row in buttons:
                            for button in button_row:
                                if button.text == "Pass ♻️":
                                    print(f"{Fore.CYAN}🔄 Clicking 'Pass' button...")
                                    await asyncio.sleep(6)
                                    await button.click()
                                    print(f"{Fore.GREEN}✅ 'Pass' button clicked.")
                                    break
                    else:
                        print(f"{Fore.GREEN}✅ Words found: {result}")
                        for res in result:
                            try:
                                async with client.action(group_username, "typing"):
                                    await asyncio.sleep(custom_delay)
                                    await client.send_message(group_username, res)
                                    print(f"{Fore.BLUE}✉️ Sent: {res}")
                            except FloodWaitError as e:
                                print(f"{Fore.RED}❌ Flood wait error: Sleeping for {e.seconds} seconds")
                                await asyncio.sleep(e.seconds)
                                new_message = await client.get_messages(group_username, limit=1)
                                if new_message[0].id != event.message.id:
                                    print(f"{Fore.YELLOW}⚠️ New message detected, ignoring previous responses.")
                                    break
                                await client.send_message(group_username, res)
                        new_message = await client.get_messages(group_username, limit=1)
                        if new_message[0].id != event.message.id:
                            print(f"{Fore.YELLOW}⚠️ New question detected, ignoring previous responses.")
                            return
        except FloodWaitError as e:
            print(f"{Fore.RED}❌ Flood wait error: Sleeping for {e.seconds} seconds")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            print(f"{Fore.RED}❌ An error occurred in handler: {e}")

    print(f'{Fore.CYAN}🔹 Listening for messages from {bot_username}...')
    await client.run_until_disconnected()

# Run the fancy startup sequence
startup_banner()
progress_bar()
animated_loading()

# Run the client
with client:
    client.loop.run_until_complete(main())