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

    # Disable hamburger menu for this user
    from utils import restore_default_commands
    await restore_default_commands(context, update.effective_chat.id)

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
        welcome_message = f"""👑 Welcome Back, Owner {user.mention_html()}!

🎬 MovieZone Bot Management Panel

Available Powers:
• 🎭 Movie Management - Add/Remove movies
• 👥 Admin Control - Manage bot administrators  
• 📢 Channel Management - Handle movie channels
• 📊 Analytics - View detailed statistics
• 🙏 User Requests - Review & process requests

You have complete control over the bot ecosystem.
Ready to manage your movie empire!"""
        
    elif user_role == 'admin':
        welcome_message = f"""🛡️ Welcome Back, Admin {user.mention_html()}!

🎬 MovieZone Bot Admin Panel

Your Capabilities:
• 🎭 Add Movies - Upload new content to database
• 📊 View Requests - Handle user movie requests  
• 🗑️ Remove Movies - Delete outdated content
• 📈 Statistics - Monitor bot performance

You can manage the movie library and assist users.
Ready to serve the community!"""
        
    else:
        # Standard welcome message for a regular user
        welcome_message = f"""🎬 Welcome to MovieZone, {user.mention_html()}!

Your Ultimate Movie Destination

What We Offer:
🔍 Search Movies - Find any movie instantly
📂 Browse Categories - Explore by genre & language  
🙏 Request Movies - Ask for movies you can't find
📥 Direct Downloads - Fast & secure downloads

Movie Collection:
• 🎭 Bollywood & Bengali Movies
• 🧑‍🎤 Latest Hollywood Blockbusters
• 🎪 South Indian Dubbed Movies  
• 📺 Popular Web Series
• 🎨 Animation & Kids Content

Download Process:
1. 🔍 Search or browse for your movie
2. 📱 Select your preferred quality
3. 👀 View a quick ad (helps us grow!)
4. 📥 Download instantly!

🚀 Ready to explore? Use the buttons below!

Join our channel: @moviezone969"""

    keyboard = get_main_keyboard(user_role)
    await update.message.reply_html(welcome_message, reply_markup=keyboard)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message for the /help command."""
    user = update.effective_user
    user_role = db.get_user_role(user.id)
    
    if user_role == 'owner':
        help_text = """❓ Owner Help & Commands

Available Features:
• ➕ Add Movie - Add new movie or series
• 📊 Show Requests - View user movie requests  
• 👥 Manage Admins - Add or remove admins
• 📢 Manage Channels - Add or remove channels
• 🗑️ Remove Movie - Delete movies from database
• 📈 Show Stats - View movie statistics

You have full access to all bot features and can manage admins and channels."""
        
    elif user_role == 'admin':
        help_text = """❓ Admin Help & Commands

Available Features:
• ➕ Add Movie - Add new movie or series
• 📊 Show Requests - View and manage user requests
• 🗑️ Remove Movie - Delete movies from database  
• 📈 Show Stats - View movie statistics

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


async def cancel_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel button press from reply keyboard."""
    from utils import get_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = get_main_keyboard(user_role)
    
    # Clear any ongoing conversation
    context.user_data.clear()
    
    await update.message.reply_text("❌ Action cancelled.", reply_markup=keyboard)

# Handlers list to be imported in main.py
start_handlers = [
    CommandHandler("start", start),
    CommandHandler("help", help_command),
    MessageHandler(filters.Regex('^❓ Help$'), help_command), # Also works from the keyboard button
    MessageHandler(filters.Regex('^❌ Cancel$'), cancel_button_handler) # Handle cancel button
]
