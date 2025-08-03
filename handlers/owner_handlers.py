# MovieZoneBot/handlers/owner_handlers.py

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

import database as db
from utils import restricted
from config import OWNER_ID

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# Conversation states for adding/removing admins and channels
(
    ASK_ADMIN_USERID, GET_ADMIN_USERID, GET_ADMIN_SHORT_NAME, CONFIRM_ADD_ADMIN,
    ASK_ADMIN_TO_REMOVE, CONFIRM_REMOVE_ADMIN,
    GET_CHANNEL_LINK, GET_CHANNEL_SHORT_NAME, CONFIRM_ADD_CHANNEL,
    ASK_CHANNEL_TO_REMOVE, CONFIRM_REMOVE_CHANNEL
) = range(11)


# --- Add Admin Conversation ---

@restricted(allowed_roles=['owner'])
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new admin."""
    await update.message.reply_text(
        "Please forward a message from the user you want to make an admin.\n"
        "Or, send their Telegram User ID.\n\n"
        "To cancel, type /cancel."
    )
    return GET_ADMIN_USERID

async def get_admin_userid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user ID of the potential admin."""
    user_id = None
    first_name = None
    username = None

    if update.message.forward_from:
        user_id = update.message.forward_from.id
        first_name = update.message.forward_from.first_name
        username = update.message.forward_from.username
    elif update.message.text and update.message.text.isdigit():
        user_id = int(update.message.text)
        # We need to fetch user details if only ID is provided
        try:
            chat = await context.bot.get_chat(user_id)
            first_name = chat.first_name
            username = chat.username
        except Exception as e:
            await update.message.reply_text("Could not find a user with this ID. Please try again or forward a message.")
            logger.error(f"Error fetching chat for user ID {user_id}: {e}")
            return GET_ADMIN_USERID
    else:
        await update.message.reply_text("Invalid input. Please forward a message or send a valid User ID.")
        return GET_ADMIN_USERID
    
    context.user_data['new_admin'] = {'id': user_id, 'first_name': first_name, 'username': username}
    await update.message.reply_text(f"User found: {first_name} (@{username}).\n\nNow, please provide a short name for this admin (e.g., 'Sudip'). This will be used for internal reference.")
    return GET_ADMIN_SHORT_NAME

async def get_admin_short_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the short name for the admin."""
    short_name = update.message.text
    context.user_data['new_admin']['short_name'] = short_name
    
    admin = context.user_data['new_admin']
    text = (
        f"Confirm Admin Addition\n\n"
        f"User: {admin['first_name']} (@{admin['username']})\n"
        f"User ID: {admin['id']}\n"
        f"Short Name: {admin['short_name']}\n\n"
        "Do you want to make this user an admin?"
    )
    keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="confirm_add_admin")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_admin")]]
    await update.message.reply_markdown_v2(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_ADD_ADMIN

async def confirm_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and adds the user as an admin."""
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_add_admin':
        await query.edit_message_text("Admin addition cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

    admin = context.user_data['new_admin']
    success = db.add_admin(
        admin_id=admin['id'],
        short_name=admin['short_name'],
        first_name=admin['first_name'],
        username=admin['username']
    )
    
    if success:
        await query.edit_message_text(f"✅ Success! {admin['first_name']} is now an admin.")
    else:
        await query.edit_message_text("❌ Error! Could not add admin. Check the logs for details.")
        
    context.user_data.clear()
    return ConversationHandler.END


# --- Remove Admin Conversation ---

@restricted(allowed_roles=['owner'])
async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to remove an admin."""
    admins = db.get_all_admins()
    if not admins:
        await update.message.reply_text("There are no admins to remove.")
        return ConversationHandler.END

    message_text = "Current Admins:\n"
    for admin in admins:
        message_text += f"- {admin['first_name']} (Short Name: `{admin['short_name']}`, ID: `{admin['user_id']}`)\n"

    message_text += "\nPlease enter the User ID or the Short Name of the admin you want to remove."
    await update.message.reply_markdown_v2(message_text)
    return ASK_ADMIN_TO_REMOVE

async def get_admin_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the identifier of the admin to be removed."""
    identifier = update.message.text
    success = db.remove_admin(identifier)
    
    if success:
        await update.message.reply_text(f"✅ Admin '{identifier}' has been removed successfully.")
    else:
        await update.message.reply_text(f"❌ Could not find an admin with identifier '{identifier}'. Please try again.")

    return ConversationHandler.END


# --- Add Channel Conversation ---

@restricted(allowed_roles=['owner'])
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new channel."""
    from utils import set_conversation_commands
    
    # Set conversation commands
    await set_conversation_commands(context, update.effective_chat.id)
    
    await update.message.reply_text(
        "Please send the channel or group link (e.g., https://t.me/moviezone969).\n\n"
        "To cancel, type /cancel."
    )
    return GET_CHANNEL_LINK

async def get_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the channel link."""
    channel_link = update.message.text
    
    # Extract channel username from link
    if "t.me/" in channel_link:
        channel_username = channel_link.split("t.me/")[-1].replace("@", "")
        channel_id = f"@{channel_username}"
    else:
        await update.message.reply_text("Invalid channel link. Please send a valid Telegram channel link.")
        return GET_CHANNEL_LINK
    
    context.user_data['new_channel'] = {
        'channel_id': channel_id,
        'channel_name': channel_username,
        'link': channel_link
    }
    
    await update.message.reply_text(f"Channel found: {channel_id}\n\nNow, please provide a short name for this channel (e.g., 'Main Channel'). This will be used for internal reference.")
    return GET_CHANNEL_SHORT_NAME

async def get_channel_short_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the short name for the channel."""
    short_name = update.message.text
    context.user_data['new_channel']['short_name'] = short_name
    
    channel = context.user_data['new_channel']
    text = (
        f"Confirm Channel Addition\n\n"
        f"Channel: {channel['channel_id']}\n"
        f"Link: {channel['link']}\n"
        f"Short Name: {channel['short_name']}\n\n"
        "Do you want to add this channel?"
    )
    keyboard = [[InlineKeyboardButton("✅ Confirm", callback_data="confirm_add_channel")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_channel")]]
    await update.message.reply_markdown_v2(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_ADD_CHANNEL

async def confirm_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and adds the channel."""
    query = update.callback_query
    await query.answer()

    if query.data == 'cancel_add_channel':
        await query.edit_message_text("Channel addition cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

    channel = context.user_data['new_channel']
    success = db.add_channel(
        channel_id=channel['channel_id'],
        channel_name=channel['channel_name'],
        short_name=channel['short_name']
    )
    
    if success:
        await query.edit_message_text(f"✅ Success! {channel['short_name']} has been added.")
    else:
        await query.edit_message_text("❌ Error! Could not add channel. It might already exist.")
        
    context.user_data.clear()
    return ConversationHandler.END


# --- Remove Channel Conversation ---

@restricted(allowed_roles=['owner'])
async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to remove a channel."""
    channels = db.get_all_channels()
    if not channels:
        await update.message.reply_text("There are no channels to remove.")
        return ConversationHandler.END

    message_text = "Current Channels:\n"
    for channel in channels:
        message_text += f"- {channel['short_name']} (ID: `{channel['channel_id']}`)\n"

    message_text += "\nPlease enter the Channel ID or the Short Name of the channel you want to remove."
    await update.message.reply_markdown_v2(message_text)
    return ASK_CHANNEL_TO_REMOVE

async def get_channel_to_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the identifier of the channel to be removed."""
    identifier = update.message.text
    success = db.remove_channel(identifier)
    
    if success:
        await update.message.reply_text(f"✅ Channel '{identifier}' has been removed successfully.")
    else:
        await update.message.reply_text(f"❌ Could not find a channel with identifier '{identifier}'. Please try again.")

    return ConversationHandler.END


# --- General Management Commands ---

@restricted(allowed_roles=['owner'])
async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides buttons to add or remove admins."""
    keyboard = [
        [InlineKeyboardButton("➕ Add New Admin", callback_data="admin_add")],
        [InlineKeyboardButton("➖ Remove an Admin", callback_data="admin_remove")]
    ]
    await update.message.reply_text("Select an option to manage admins:", reply_markup=InlineKeyboardMarkup(keyboard))

@restricted(allowed_roles=['owner'])
async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides buttons to add or remove channels."""
    keyboard = [
        [InlineKeyboardButton("➕ Add New Channel", callback_data="channel_add")],
        [InlineKeyboardButton("➖ Remove a Channel", callback_data="channel_remove")]
    ]
    await update.message.reply_text("Select an option to manage channels:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin management button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_add":
        await query.edit_message_text("Starting add admin process...")
        await add_admin_start(query, context)
    elif query.data == "admin_remove":
        await query.edit_message_text("Starting remove admin process...")
        await remove_admin_start(query, context)

async def handle_channel_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle channel management button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "channel_add":
        await query.edit_message_text("Starting add channel process...")
        await add_channel_start(query, context)
    elif query.data == "channel_remove":
        await query.edit_message_text("Starting remove channel process...")
        await remove_channel_start(query, context)

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generic cancellation function."""
    from utils import restore_default_commands
    
    # Restore default commands
    await restore_default_commands(context, update.effective_chat.id)
    
    await update.message.reply_text("Action cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# Conversation Handlers
add_admin_conv = ConversationHandler(
    entry_points=[CommandHandler("addadmin", add_admin_start)],
    states={
        GET_ADMIN_USERID: [MessageHandler(filters.TEXT | filters.FORWARDED, get_admin_userid)],
        GET_ADMIN_SHORT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_admin_short_name)],
        CONFIRM_ADD_ADMIN: [CallbackQueryHandler(confirm_add_admin, pattern='^(confirm|cancel)_add_admin$')],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)

remove_admin_conv = ConversationHandler(
    entry_points=[CommandHandler("removeadmin", remove_admin_start)],
    states={
        ASK_ADMIN_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_admin_to_remove)],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)

add_channel_conv = ConversationHandler(
    entry_points=[CommandHandler("addchannel", add_channel_start)],
    states={
        GET_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_link)],
        GET_CHANNEL_SHORT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_short_name)],
        CONFIRM_ADD_CHANNEL: [CallbackQueryHandler(confirm_add_channel, pattern='^(confirm|cancel)_add_channel$')],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)

remove_channel_conv = ConversationHandler(
    entry_points=[CommandHandler("removechannel", remove_channel_start)],
    states={
        ASK_CHANNEL_TO_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_to_remove)],
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)


# Main handler list to be imported
owner_handlers = [
    add_admin_conv,
    remove_admin_conv,
    add_channel_conv,
    remove_channel_conv,
    CommandHandler("manageadmins", manage_admins),
    CommandHandler("managechannels", manage_channels),
    MessageHandler(filters.Regex("^👥 Manage Admins$"), manage_admins),
    MessageHandler(filters.Regex("^📢 Manage Channels$"), manage_channels),
    CallbackQueryHandler(handle_admin_management, pattern="^admin_"),
    CallbackQueryHandler(handle_channel_management, pattern="^channel_")
]
