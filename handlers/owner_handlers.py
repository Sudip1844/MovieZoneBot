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
    from utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Explicitly set conversation commands for callback query
        from utils import set_conversation_commands
        await set_conversation_commands(update, context)
        
        await query.edit_message_text(
            "Please forward a message from the user you want to make an admin.\n"
            "Or, send their Telegram User ID.\n\n"
            "To cancel at any time, press ❌ Cancel button."
        )
    else:
        await update.message.reply_text(
            "Please forward a message from the user you want to make an admin.\n"
            "Or, send their Telegram User ID.\n\n"
            "To cancel, press ❌ Cancel button.",
            reply_markup=keyboard
        )
    return GET_ADMIN_USERID

async def get_admin_userid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user ID of the potential admin."""
    # Check if user sent /cancel command
    if update.message.text and (update.message.text.lower() == '/cancel' or update.message.text.lower() == 'cancel'):
        from utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Admin addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
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
    
    # Check if user sent /cancel command
    if short_name.lower() == '/cancel' or short_name.lower() == 'cancel':
        from utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Admin addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
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
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONFIRM_ADD_ADMIN

async def confirm_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and adds the user as an admin."""
    query = update.callback_query
    await query.answer()

    from utils import restore_default_commands
    
    if query.data == 'cancel_add_admin':
        await restore_default_commands(context, query.message.chat_id)
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
    
    await restore_default_commands(context, query.message.chat_id)
    context.user_data.clear()
    return ConversationHandler.END


# --- Remove Admin Conversation ---

@restricted(allowed_roles=['owner'])
async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to remove an admin with button selection."""
    from utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Explicitly set conversation commands for callback query
        from utils import set_conversation_commands
        await set_conversation_commands(update, context)
        
        admins = db.get_all_admins()
        if not admins:
            await query.edit_message_text("There are no admins to remove.")
            return ConversationHandler.END

        # Create buttons for each admin - only show short name as requested
        buttons = []
        for admin in admins:
            admin_display = admin['short_name']  # Only use short name as requested
            buttons.append([InlineKeyboardButton(admin_display, callback_data=f"remove_admin_{admin['user_id']}")])
        
        # Add cancel button
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_admin")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Select admin to remove:", reply_markup=reply_markup)
    else:
        admins = db.get_all_admins()
        if not admins:
            await update.message.reply_text("There are no admins to remove.")
            return ConversationHandler.END

        # Create buttons for each admin - only show short name as requested
        buttons = []
        for admin in admins:
            admin_display = admin['short_name']  # Only use short name as requested
            buttons.append([InlineKeyboardButton(admin_display, callback_data=f"remove_admin_{admin['user_id']}")])
        
        # Add cancel button
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_admin")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Select admin to remove:", reply_markup=reply_markup)
    
    return CONFIRM_REMOVE_ADMIN

async def confirm_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and removes the selected admin."""
    query = update.callback_query
    await query.answer()
    
    from utils import restore_default_commands
    
    if query.data == "cancel_remove_admin":
        await restore_default_commands(context, query.message.chat_id)
        await query.edit_message_text("❌ Admin removal cancelled.")
        return ConversationHandler.END
    
    if query.data.startswith("remove_admin_"):
        admin_id = query.data.split("_")[2]
        success = db.remove_admin(admin_id)
        
        if success:
            await query.edit_message_text(f"✅ Admin has been removed successfully.")
        else:
            await query.edit_message_text(f"❌ Could not remove admin. Please try again.")
    
    await restore_default_commands(context, query.message.chat_id)
    return ConversationHandler.END


# --- Add Channel Conversation ---

@restricted(allowed_roles=['owner'])
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new channel."""
    from utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Explicitly set conversation commands for callback query
        from utils import set_conversation_commands
        await set_conversation_commands(update, context)
        
        await query.edit_message_text(
            "Please send the channel or group link (e.g., https://t.me/moviezone969).\n\n"
            "To cancel at any time, press ❌ Cancel button."
        )
    else:
        await update.message.reply_text(
            "Please send the channel or group link (e.g., https://t.me/moviezone969).\n\n"
            "To cancel, press ❌ Cancel button.",
            reply_markup=keyboard
        )
    return GET_CHANNEL_LINK

async def get_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the channel link."""
    channel_link = update.message.text
    
    # Check if user sent /cancel command
    if channel_link.lower() == '/cancel' or channel_link.lower() == 'cancel':
        from utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Channel addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    # Extract channel username from link
    if "t.me/" in channel_link:
        channel_username = channel_link.split("t.me/")[-1].replace("@", "")
        
        # Check if it's a private channel link (contains + or joinchat)
        if "+" in channel_username or "joinchat/" in channel_link:
            await update.message.reply_text(
                "❌ Private channel links are not supported.\n\n"
                "Please add the bot to your channel first, then use the channel's @username instead.\n"
                "Example: https://t.me/moviezone969"
            )
            return GET_CHANNEL_LINK
        
        channel_id = f"@{channel_username}"
        
        # Try to get channel info to verify bot has access
        try:
            chat = await context.bot.get_chat(channel_id)
            channel_name = chat.title or channel_username
        except Exception as e:
            await update.message.reply_text(
                f"❌ Cannot access channel {channel_id}.\n\n"
                "Please make sure:\n"
                "1. The channel exists\n"
                "2. The bot is added to the channel\n"
                "3. The bot has 'Post Messages' permission"
            )
            return GET_CHANNEL_LINK
    else:
        await update.message.reply_text("Invalid channel link. Please send a valid Telegram channel link.")
        return GET_CHANNEL_LINK
    
    context.user_data['new_channel'] = {
        'channel_id': channel_id,
        'channel_name': channel_name,
        'link': channel_link
    }
    
    await update.message.reply_text(f"Channel found: {channel_name} ({channel_id})\n\nNow, please provide a short name for this channel (e.g., 'Main Channel'). This will be used for internal reference.")
    return GET_CHANNEL_SHORT_NAME

async def get_channel_short_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the short name for the channel."""
    short_name = update.message.text
    
    # Check if user sent /cancel command
    if short_name.lower() == '/cancel' or short_name.lower() == 'cancel':
        from utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Channel addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
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
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
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
    
    from utils import restore_default_commands
    
    if success:
        await query.edit_message_text(f"✅ Success! {channel['short_name']} has been added.")
    else:
        await query.edit_message_text("❌ Error! Could not add channel. It might already exist.")
    
    await restore_default_commands(context, query.message.chat_id)
    context.user_data.clear()
    return ConversationHandler.END


# --- Remove Channel Conversation ---

@restricted(allowed_roles=['owner'])
async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to remove a channel with button selection."""
    from utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # Explicitly set conversation commands for callback query
        from utils import set_conversation_commands
        await set_conversation_commands(update, context)
        
        channels = db.get_all_channels()
        if not channels:
            await query.edit_message_text("There are no channels to remove.")
            return ConversationHandler.END

        # Create buttons for each channel - only show short name as requested
        buttons = []
        for channel in channels:
            channel_display = channel['short_name']  # Only use short name as requested
            # Clean channel_id for callback data
            clean_id = channel['channel_id'].replace('@', '').replace('-', '_')
            buttons.append([InlineKeyboardButton(channel_display, callback_data=f"remove_channel_{clean_id}")])
        
        # Add cancel button
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_channel")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.edit_message_text("Select channel to remove:", reply_markup=reply_markup)
    else:
        channels = db.get_all_channels()
        if not channels:
            await update.message.reply_text("There are no channels to remove.")
            return ConversationHandler.END

        # Create buttons for each channel - only show short name as requested
        buttons = []
        for channel in channels:
            channel_display = channel['short_name']  # Only use short name as requested
            # Clean channel_id for callback data
            clean_id = channel['channel_id'].replace('@', '').replace('-', '_')
            buttons.append([InlineKeyboardButton(channel_display, callback_data=f"remove_channel_{clean_id}")])
        
        # Add cancel button
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_remove_channel")])
        
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text("Select channel to remove:", reply_markup=reply_markup)
    
    return CONFIRM_REMOVE_CHANNEL

async def confirm_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms and removes the selected channel."""
    query = update.callback_query
    await query.answer()
    
    from utils import restore_default_commands
    
    if query.data == "cancel_remove_channel":
        await restore_default_commands(context, query.message.chat_id)
        await query.edit_message_text("❌ Channel removal cancelled.")
        return ConversationHandler.END
    
    if query.data.startswith("remove_channel_"):
        # Extract and reconstruct channel_id
        clean_id = query.data.split("remove_channel_")[1]
        original_id = clean_id.replace('_', '-')
        if not original_id.startswith('@'):
            original_id = '@' + original_id
            
        success = db.remove_channel(original_id)
        
        if success:
            await query.edit_message_text(f"✅ Channel has been removed successfully.")
        else:
            await query.edit_message_text(f"❌ Could not remove channel. Please try again.")
    
    await restore_default_commands(context, query.message.chat_id)
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
        # Create a fake update object for add_admin_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await add_admin_start(fake_update, context)
    elif query.data == "admin_remove":
        await query.edit_message_text("Starting remove admin process...")
        # Create a fake update object for remove_admin_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await remove_admin_start(fake_update, context)

async def handle_channel_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle channel management button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "channel_add":
        await query.edit_message_text("Starting add channel process...")
        # Create a fake update object for add_channel_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await add_channel_start(fake_update, context)
    elif query.data == "channel_remove":
        await query.edit_message_text("Starting remove channel process...")
        # Create a fake update object for remove_channel_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await remove_channel_start(fake_update, context)

async def cancel_admin_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel admin management conversation."""
    from utils import restore_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    
    await update.message.reply_text("❌ Admin management cancelled.", reply_markup=keyboard)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_channel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel channel management conversation."""
    from utils import restore_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    
    await update.message.reply_text("❌ Channel management cancelled.", reply_markup=keyboard)
    context.user_data.clear()
    return ConversationHandler.END

# Conversation Handlers
add_admin_conv = ConversationHandler(
    entry_points=[
        CommandHandler("addadmin", add_admin_start),
        CallbackQueryHandler(add_admin_start, pattern='^admin_add$')
    ],
    states={
        GET_ADMIN_USERID: [MessageHandler(filters.TEXT | filters.FORWARDED, get_admin_userid)],
        GET_ADMIN_SHORT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_admin_short_name)],
        CONFIRM_ADD_ADMIN: [CallbackQueryHandler(confirm_add_admin, pattern='^(confirm|cancel)_add_admin$')],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_admin_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_admin_conversation)
    ]
)

remove_admin_conv = ConversationHandler(
    entry_points=[
        CommandHandler("removeadmin", remove_admin_start),
        CallbackQueryHandler(remove_admin_start, pattern='^admin_remove$')
    ],
    states={
        CONFIRM_REMOVE_ADMIN: [CallbackQueryHandler(confirm_remove_admin, pattern='^(remove_admin_|cancel_remove_admin).*$')],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_admin_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_admin_conversation)
    ]
)

add_channel_conv = ConversationHandler(
    entry_points=[
        CommandHandler("addchannel", add_channel_start),
        CallbackQueryHandler(add_channel_start, pattern='^channel_add$')
    ],
    states={
        GET_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_link)],
        GET_CHANNEL_SHORT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_short_name)],
        CONFIRM_ADD_CHANNEL: [CallbackQueryHandler(confirm_add_channel, pattern='^(confirm|cancel)_add_channel$')],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_channel_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_channel_conversation)
    ]
)

remove_channel_conv = ConversationHandler(
    entry_points=[
        CommandHandler("removechannel", remove_channel_start),
        CallbackQueryHandler(remove_channel_start, pattern='^channel_remove$')
    ],
    states={
        CONFIRM_REMOVE_CHANNEL: [CallbackQueryHandler(confirm_remove_channel, pattern='^(remove_channel_|cancel_remove_channel).*$')],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_channel_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_channel_conversation)
    ]
)


# Main handler list to be imported
owner_handlers = [
    add_admin_conv,
    remove_admin_conv,
    add_channel_conv,
    remove_channel_conv,
    MessageHandler(filters.Regex("^👥 Manage Admins$"), manage_admins),
    MessageHandler(filters.Regex("^📢 Manage Channels$"), manage_channels),
    CallbackQueryHandler(handle_channel_management, pattern="^channel_remove$")
]
