# MovieZoneBot/main.py

import logging
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler, ContextTypes
from typing import Tuple, Optional

# --- Configuration and Database Imports ---
from config import BOT_TOKEN, OWNER_ID
import database as db

# --- Handlers Imports ---
from handlers.start_handler import start_handlers, NEW_MEMBER_WELCOME_MESSAGE
from handlers.callback_handler import callback_query_handler
from handlers.conversation_handlers import add_movie_conv_handler
from handlers.movie_handlers import movie_handlers
from handlers.owner_handlers import owner_handlers

# --- Logging Setup ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
# Set higher logging level for httpx to avoid noisy INFO messages
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Auto-Delete Job Functions ---
async def delete_message_job(context):
    """Deletes a message after a specified time."""
    try:
        await context.bot.delete_message(chat_id=context.job.chat_id, message_id=context.job.data['message_id'])
        logger.info(f"Auto-deleted message {context.job.data['message_id']} from chat {context.job.chat_id}")
    except Exception as e:
        logger.warning(f"Could not delete message {context.job.data['message_id']}: {e}")

def schedule_message_deletion(context, chat_id: int, message_id: int, delay_seconds: int = 86400): # 24 hours
    """Schedules a message to be deleted after a delay."""
    if context.job_queue:
        context.job_queue.run_once(
            delete_message_job,
            when=delay_seconds,
            data={'message_id': message_id},
            chat_id=chat_id,
            name=f"delete_{chat_id}_{message_id}"
        )
    else:
        logger.warning(f"JobQueue not available - message {message_id} will not be auto-deleted")

async def delete_conversation_messages(context, chat_id: int, message_ids: list):
    """Delete multiple conversation messages immediately."""
    deleted_count = 0
    for message_id in message_ids:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            deleted_count += 1
        except Exception as e:
            logger.warning(f"Could not delete conversation message {message_id}: {e}")
    logger.info(f"Deleted {deleted_count}/{len(message_ids)} conversation messages from chat {chat_id}")

def schedule_user_message_cleanup(context, chat_id: int, message_id: int, user_role: str):
    """Schedule user message cleanup based on role."""
    import database as db
    
    # For owners and admins: delete everything after 24 hours
    # For users: delete everything except movie posts after 24 hours
    if user_role in ['owner', 'admin']:
        schedule_message_deletion(context, chat_id, message_id, 86400)  # 24 hours
    else:
        # For users, we need to check if it's a movie post or not
        # Movie posts are preserved, other messages deleted after 24 hours
        schedule_message_deletion(context, chat_id, message_id, 86400)

# --- New Channel Member Handler ---
def extract_status_change(chat_member_update: ChatMemberUpdated) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status change can't be determined."""
    status_change = chat_member_update.difference().get("status")
    if status_change is None:
        return None

    old_is_member, new_is_member = chat_member_update.difference().get("status")
    was_member = old_is_member in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_is_member == ChatMember.RESTRICTED and new_is_member is not None)
    is_member = new_is_member in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_is_member == ChatMember.RESTRICTED and new_is_member is not None)

    return was_member, is_member

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Greets new users in chats and announces when someone leaves."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    user = update.chat_member.new_chat_member.user

    # We only want to greet new members, not status changes of existing members
    if not was_member and is_member:
        logger.info(f"{user.mention_html()} joined channel {update.effective_chat.title}")
        # Send the welcome message to the user directly
        try:
            welcome_text = NEW_MEMBER_WELCOME_MESSAGE.format(user_mention=user.mention_html())
            await context.bot.send_message(user.id, welcome_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Failed to send welcome message to new channel member {user.id}: {e}")

# --- Global Cancel Handler ---
async def global_cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command globally to end any conversation."""
    from utils import restore_main_keyboard
    import database as db

    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)

    await update.message.reply_text("❌ Action cancelled.", reply_markup=keyboard)
    context.user_data.clear()

# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    # You can add a notification to yourself here if you want
    # For example:
    # await context.bot.send_message(chat_id=OWNER_ID, text=f"An error occurred: {context.error}")


def main() -> None:
    """Start the bot."""
    if not BOT_TOKEN:
        logger.critical("FATAL: BOT_TOKEN is not configured. Bot cannot start.")
        return

    # Initialize database
    db.initialize_database()

    # --- Application Setup ---
    application = Application.builder().token(BOT_TOKEN).build()

    # --- Registering Handlers ---
    # Add all handlers from the different handler files.
    # The order can be important.

    # 1. Owner-specific handlers (highest priority for these commands)
    for handler in owner_handlers:
        application.add_handler(handler)

    # 2. Add Movie conversation handler
    application.add_handler(add_movie_conv_handler)

    # 3. Movie-related handlers (search, category, request, remove movie)
    # These must be added before the general callback handler to process delete callbacks
    for handler in movie_handlers:
        application.add_handler(handler)

    # 4. Regular command and message handlers from start_handler
    for handler in start_handlers:
        application.add_handler(handler)

    # 5. Callback Query Handler for all inline buttons (must be after conversation handlers)
    application.add_handler(callback_query_handler)

    # 6. Welcome message for new channel members
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    # 7. Global cancel command handler
    application.add_handler(CommandHandler('cancel', global_cancel_handler))

    # 8. Error handler
    application.add_error_handler(error_handler)

    # --- Disable Hamburger Menu Globally ---
    async def post_init(application):
        # Disable hamburger menu globally - use reply keyboard only
        from telegram import BotCommandScopeDefault, BotCommandScopeAllPrivateChats
        await application.bot.set_my_commands([], scope=BotCommandScopeDefault())
        await application.bot.set_my_commands([], scope=BotCommandScopeAllPrivateChats())
        logger.info("Hamburger menu disabled globally for all users - using reply keyboard only")

    application.post_init = post_init

    # --- Start the Bot ---
    logger.info("Bot is starting up...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot has been stopped.")


if __name__ == "__main__":
    main()