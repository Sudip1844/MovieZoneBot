# MovieZoneBot/handlers/start_handler.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

import database as db
from utils import get_main_keyboard
from config import BOT_USERNAME

# লগিং সেটআপ
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    - Adds new users to the database.
    - Sends a welcome message with a keyboard based on the user's role.
    - Handles deep links from the ad page.
    """
    user = update.effective_user
    logger.info(f"/start command received from user: {user.id} ({user.first_name})")

    # Add user to the database if they don't exist
    db.add_user_if_not_exists(user.id, user.first_name, user.username)
    
    # context.args contains the part after the /start command (for deep linking)
    # Example: /start <secureToken>
    if context.args:
        payload = context.args[0]
        logger.info(f"User {user.id} started with payload: {payload}")
        
        # Validate the ad token from the ad page
        file_id_to_send = db.validate_ad_token(token=payload, user_id=user.id)
        
        if file_id_to_send:
            logger.info(f"Valid token. Sending file {file_id_to_send} to user {user.id}")
            await context.bot.send_message(
                chat_id=user.id,
                text="✅ Your download is ready! Sending the file now..."
            )
            try:
                # We use the direct file_id to send the file
                await context.bot.send_document(chat_id=user.id, document=file_id_to_send)
            except Exception as e:
                logger.error(f"Failed to send file with ID {file_id_to_send} to user {user.id}. Error: {e}")
                await context.bot.send_message(
                    chat_id=user.id,
                    text="❌ There was an error sending the file. Please try generating a new link."
                )
            return  # Stop further execution after sending the file
        else:
            # If the token is invalid or expired
            await context.bot.send_message(
                chat_id=user.id,
                text="⚠️ Sorry, this download link is invalid or has expired. Please generate a new one from the bot."
            )

    # For a normal /start command without a payload
    user_role = db.get_user_role(user.id)
    welcome_message = ""
    if user_role == 'owner':
        welcome_message = f"👑 Welcome, Owner {user.mention_html()}!\n\nAll special commands are available on your keyboard. Ready to manage the bot."
    elif user_role == 'admin':
        welcome_message = f"🛡️ Welcome, Admin {user.mention_html()}!\n\nYou can add movies, upload files, and view user requests."
    else:
        # Standard welcome message for a regular user
        welcome_message = f"👋 Welcome, {user.mention_html()}!\n\nWelcome to {BOT_USERNAME}. Here you can find your favorite Bengali, Hindi, and dubbed movies.\n\nJust search for a movie or browse our categories to get started!"

    keyboard = get_main_keyboard(user_role)
    await update.message.reply_html(welcome_message, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message for the /help command."""
    user = update.effective_user
    user_role = db.get_user_role(user.id)
    
    if user_role == 'owner':
        help_text = """❓ Owner Help & Commands

Available Commands:
• /addmovie - Add new movie or series
• /showrequests - View user movie requests  
• /manageadmins - Add or remove admins
• /managechannels - Add or remove channels
• /removemovie - Delete movies from database
• /showstats - View movie statistics

You have full access to all bot features and can manage admins and channels."""
        
    elif user_role == 'admin':
        help_text = """❓ Admin Help & Commands

Available Commands:
• /addmovie - Add new movie or series
• /showrequests - View and manage user requests
• /removemovie - Delete movies from database  
• /showstats - View movie statistics

You can manage movies and handle user requests."""
        
    else:
        help_text = """❓ How to Use MovieZone Bot

Main Features:
🔍 Search - Find movies by name
🎭 Request - Request new movies to admin

Download Process:
1. 🔍 Search or browse for a movie in our channel @moviezone969
2. 📱 Select quality (480p/720p/1080p) links or Series download link 
3. 👀 Watch ads
4. 📥 Get your movie!

Tips:
• Use specific movie names for better search results in channel 
• Check our channel for latest uploads
• Report any issues to admins

Support: 
Join: @moviezone969

🎬 Happy watching!"""
        
    await update.message.reply_text(help_text)

# This is the welcome message for new channel members.
# It will be triggered by a different handler in main.py
NEW_MEMBER_WELCOME_MESSAGE = """
Welcome {user_mention} to our channel & bot!

❓ How to Use MovieZone Bot

Main Features:
- 🔍 Search: Find movies by name.
- 📂 Category: Browse by genre.
- 🙏 Request: Request new movies.

Download Process:
1.  🔍 Search or browse for a movie.
2.  📲 Select quality (480p/720p/1080p).
3.  👀 Watch a short ad to support us.
4.  📥 Download your movie instantly!

Tips:
- Use specific movie names for better search results.
- Check our channel for the latest uploads.
- Report any issues to admins via the bot.

Support:
- Join: @moviezone969
- Contact: Use the /request command in the bot.

🎬 Happy watching!
"""


# Handlers list to be imported in main.py
start_handlers = [
    CommandHandler("start", start),
    CommandHandler("help", help_command),
    MessageHandler(filters.Regex('^❓ Help$'), help_command) # Also works from the keyboard button
]
