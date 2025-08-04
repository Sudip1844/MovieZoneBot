# MovieZoneBot/utils.py

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update
)
from config import CATEGORIES, BOT_USERNAME, AD_PAGE_URL, SINGLE_MOVIE_POST_TEMPLATE, SERIES_POST_TEMPLATE
import database as db
import logging
from typing import List

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# --- Role Verification Decorator ---
def restricted(allowed_roles: List[str]):
    """
    একটি ডেকোরেটর যা একটি কমান্ডকে নির্দিষ্ট ভূমিকার (role) ব্যবহারকারীদের জন্য সীমাবদ্ধ করে।
    উদাহরণ: @restricted(allowed_roles=['owner', 'admin'])
    """
    def decorator(func):
        async def wrapped(update: Update, context, *args, **kwargs):
            # Handle both regular messages and callback queries
            if hasattr(update, 'callback_query') and update.callback_query:
                user_id = update.callback_query.from_user.id
                message = update.callback_query.message
            else:
                user_id = update.effective_user.id
                message = update.message
                
            user_role = db.get_user_role(user_id)
            
            if user_role not in allowed_roles:
                await message.reply_text("❌ দুঃখিত, এই কমান্ডটি ব্যবহার করার অনুমতি আপনার নেই।")
                logger.warning(f"Unauthorized access attempt by user {user_id} ({user_role}) for a '{', '.join(allowed_roles)}' command.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapped
    return decorator

# --- Keyboard and Button Generation ---

def get_main_keyboard(user_role: str) -> ReplyKeyboardMarkup:
    """Create role-based main menu keyboard for users."""
    
    if user_role == 'owner':
        # Owner gets all commands
        keyboard = [
            [KeyboardButton("➕ Add Movie"), KeyboardButton("📊 Show Requests")],
            [KeyboardButton("👥 Manage Admins"), KeyboardButton("📢 Manage Channels")],
            [KeyboardButton("❓ Help")]
        ]
    elif user_role == 'admin':
        # Admin gets movie management commands only
        keyboard = [
            [KeyboardButton("➕ Add Movie"), KeyboardButton("📊 Show Requests")],
            [KeyboardButton("❓ Help")]
        ]
    else:
        # Regular users get basic commands only
        keyboard = [
            [KeyboardButton("🔍 Search Movies"), KeyboardButton("📂 Browse Categories")],
            [KeyboardButton("🙏 Request Movie")],
            [KeyboardButton("❓ Help")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_conversation_keyboard(user_role: str) -> ReplyKeyboardMarkup:
    """Create keyboard with cancel button during conversations."""
    keyboard = [
        [KeyboardButton("❌ Cancel")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_category_keyboard() -> InlineKeyboardMarkup:
    """মুভির ক্যাটাগরিগুলোর জন্য একটি ইনলাইন কীবোর্ড তৈরি করে।"""
    buttons = []
    row = []
    for category in CATEGORIES:
        # প্রতিটি ক্যাটাগরির জন্য একটি বাটন তৈরি করা হয়
        # callback_data তে 'cat_' প্রিফিক্স ব্যবহার করা হয় যাতে অন্য বাটন থেকে আলাদা করা যায়
        clean_category = category.replace("✅ ", "").replace(" ", "_")
        row.append(InlineKeyboardButton(category, callback_data=f"cat_{clean_category}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    return InlineKeyboardMarkup(buttons)

def get_quality_buttons(movie_id: int, files: dict) -> InlineKeyboardMarkup:
    """একটি মুভির জন্য উপলব্ধ কোয়ালিটির বাটন তৈরি করে।"""
    buttons = []
    for quality in files.keys():
        # বাটনগুলো 'quality' প্রিফিক্স দিয়ে শুরু হবে
        callback_data = f"quality_{movie_id}_{quality}"
        buttons.append([InlineKeyboardButton(f"🎬 {quality}", callback_data=callback_data)])
    
    return InlineKeyboardMarkup(buttons)

def generate_ad_link_button(user_id: int, movie_id: int, quality: str) -> InlineKeyboardMarkup | None:
    """একটি 'Watch Ad & Download' বাটন তৈরি করে।"""
    token = db.create_ad_token(user_id=user_id, movie_id=movie_id, quality=quality)
    if not token:
        logger.error(f"Failed to create ad token for user {user_id}, movie {movie_id}, quality {quality}")
        return None
        
    # URL তৈরি করা হয়: https://your-page.com/?token=XYZ&uid=123
    ad_url = f"{AD_PAGE_URL}?token={token}&uid={user_id}"
    
    button = [[InlineKeyboardButton("📺 Watch Ad & Download Now", url=ad_url)]]
    return InlineKeyboardMarkup(button)

def format_movie_post(movie_details: dict, channel_username: str) -> str:
    """
    ডেটাবেস থেকে প্রাপ্ত মুভির তথ্য দিয়ে একটি সুন্দর পোস্ট ফরম্যাট করে।
    আপনার দেওয়া ছবির ফরম্যাট অনুযায়ী এটি তৈরি করা হয়েছে।
    """
    files = movie_details.get('files', {})
    is_series = any('E' in quality for quality in files.keys())
    
    # ডাউনলোড লিঙ্ক তৈরি
    download_links = ""
    if is_series:
        # সিরিজের জন্য একটি মাত্র লিঙ্ক
        first_episode = next((quality for quality in files.keys() if quality.startswith('E')), None)
        if first_episode:
            deep_link = f"https://t.me/{BOT_USERNAME}?start=file_{movie_details['movie_id']}_{first_episode}"
            download_links = f"Ep1 to Ep(last) || 👉 <a href='{deep_link}'>Click To Download</a> 📥"
    else:
        # সিঙ্গেল মুভির জন্য প্রতিটি কোয়ালিটির লিঙ্ক
        qualities = sorted([quality for quality in files.keys() if not quality.startswith('E')])
        for quality in qualities:
            deep_link = f"https://t.me/{BOT_USERNAME}?start=file_{movie_details['movie_id']}_{quality}"
            download_links += f"{quality} || 👉 <a href='{deep_link}'>Click To Download</a> 📥\n"

    # ডেটা পূরণ করা
    template_data = {
        'title': movie_details.get('title', 'N/A'),
        'languages': " | ".join(movie_details.get('languages', [])),
        'categories': " | ".join(movie_details.get('categories', [])),
        'release_year': movie_details.get('release_year', 'N/A'),
        'runtime': movie_details.get('runtime', 'N/A'),
        'imdb_rating': movie_details.get('imdb_rating', 'N/A'),
        'download_links': download_links.strip(),
        'channel_username': channel_username
    }

    if is_series:
        return SERIES_POST_TEMPLATE.format(**template_data)
    else:
        return SINGLE_MOVIE_POST_TEMPLATE.format(**template_data)

def get_movie_search_results_markup(movies: List[dict]) -> InlineKeyboardMarkup:
    """Create inline keyboard for movie search results."""
    buttons = []
    for movie in movies:
        button_text = f"🎬 {movie.get('title', 'Unknown')}"
        callback_data = f"view_{movie['movie_id']}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(buttons)

# --- Dynamic Bot Commands Management ---
async def set_conversation_commands(update: Update, context):
    """Set /cancel command in command box during conversations (like Add Movie does)."""
    from telegram import BotCommand, BotCommandScopeChat
    
    try:
        # Get chat_id from either update.effective_chat or callback query
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            chat_id = update.effective_chat.id
            
        # Set only /cancel command for command box (same as Add Movie conversation)
        conversation_commands = [BotCommand("cancel", "Cancel current action")]
        await context.bot.set_my_commands(
            commands=conversation_commands,
            scope=BotCommandScopeChat(chat_id=chat_id)
        )
        logger.info(f"Set /cancel command in command box for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to set conversation commands: {e}")

async def restore_default_commands(update: Update, context):
    """Restore default commands when conversation ends."""
    from telegram import BotCommand, BotCommandScopeChat
    
    try:
        # Get chat_id from either update.effective_chat or callback query
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            chat_id = update.effective_chat.id
            
        # Restore default commands to hamburger menu (start & help only)
        default_commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Get help and instructions")
        ]
        await context.bot.set_my_commands(
            commands=default_commands,
            scope=BotCommandScopeChat(chat_id=chat_id)
        )
        logger.info(f"Restored default commands to hamburger menu for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to restore default commands: {e}")

async def set_conversation_keyboard(update: Update, context, user_role: str):
    """Set conversation keyboard with cancel button and update commands."""
    keyboard = get_conversation_keyboard(user_role)
    # Store the original keyboard to restore later
    context.user_data['original_keyboard'] = get_main_keyboard(user_role)
    
    # Set conversation commands (only /cancel visible)
    await set_conversation_commands(update, context)
    
    return keyboard

async def restore_main_keyboard(update: Update, context, user_role: str):
    """Restore main keyboard and commands when conversation ends."""
    keyboard = context.user_data.get('original_keyboard', get_main_keyboard(user_role))
    
    # Restore default commands
    await restore_default_commands(update, context)
    
    return keyboard
