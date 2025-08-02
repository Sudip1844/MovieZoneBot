# MovieZoneBot/handlers/movie_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram.constants import ParseMode

import database as db
from utils import get_category_keyboard, get_movie_search_results_markup, restricted
from config import CATEGORIES

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# Conversation states
REQUEST_MOVIE_NAME, DELETE_MOVIE_NAME, SHOW_STATS_MOVIE_NAME = range(3)

# --- Search Movies ---

async def search_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle movie search functionality."""
    await update.message.reply_text(
        "🔍 Search Movies\n\n"
        "Please type the name of the movie you're looking for:"
    )

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the actual search query from user."""
    query = update.message.text
    
    # Skip if this is a keyboard button or command
    if query in ["🔍 Search Movies", "📂 Browse Categories", "🙏 Request Movie", "➕ Add Movie", "📊 Show Requests", "👥 Manage Admins", "📢 Manage Channels", "❓ Help"]:
        return
    
    if query.startswith('/'):
        return
    
    logger.info(f"User {update.effective_user.id} searched for: {query}")
    
    movies = db.search_movies(query, limit=10)
    
    if not movies:
        await update.message.reply_text(f"❌ No movies found for '{query}'. Try using different keywords or request it using the 'Request Movie' button.")
        return
    
    if len(movies) == 1:
        # Only one movie found, show details directly
        movie = movies[0]
        await show_movie_details(update, context, movie)
    else:
        # Multiple movies found, show selection
        message_text = f"🎬 Found {len(movies)} movies for '{query}':\n\n"
        for i, movie in enumerate(movies, 1):
            message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
        
        reply_markup = get_movie_search_results_markup(movies)
        await update.message.reply_html(message_text, reply_markup=reply_markup)

async def show_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Show detailed information about a movie."""
    response_text = f"🎬 <b>{movie.get('title', 'N/A')}</b>\n\n" \
                    f"<b>Description:</b> {movie.get('description', 'N/A')}\n" \
                    f"<b>Release Year:</b> {movie.get('release_year', 'N/A')}\n" \
                    f"<b>Runtime:</b> {movie.get('runtime', 'N/A')}\n" \
                    f"<b>IMDb:</b> {movie.get('imdb_rating', 'N/A')}/10\n" \
                    f"<b>Languages:</b> {', '.join(movie.get('languages', []))}\n" \
                    f"<b>Categories:</b> {', '.join(movie.get('categories', []))}"
    
    # Create quality buttons
    files = movie.get('files', {})
    buttons = []
    for quality in files.keys():
        callback_data = f"quality_{movie['movie_id']}_{quality}"
        buttons.append([InlineKeyboardButton(f"🎬 {quality}", callback_data=callback_data)])
    
    quality_buttons_markup = InlineKeyboardMarkup(buttons)
    
    thumbnail_id = movie.get('thumbnail_file_id')
    if thumbnail_id:
        try:
            await update.message.reply_photo(
                photo=thumbnail_id, 
                caption=response_text, 
                parse_mode=ParseMode.HTML, 
                reply_markup=quality_buttons_markup
            )
        except Exception as e:
            logger.error(f"Failed to send photo for movie {movie['movie_id']}: {e}")
            await update.message.reply_html(response_text, reply_markup=quality_buttons_markup)
    else:
        await update.message.reply_html(response_text, reply_markup=quality_buttons_markup)

# --- Browse Categories ---

async def browse_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show movie categories for browsing."""
    keyboard = get_category_keyboard()
    await update.message.reply_text(
        "📂 Browse by Categories\n\n"
        "Select a category to see available movies:",
        reply_markup=keyboard
    )

# --- Request Movie ---

async def request_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the movie request conversation."""
    from utils import set_conversation_commands
    
    # Set conversation commands
    await set_conversation_commands(context, update.effective_chat.id)
    
    await update.message.reply_text(
        "🙏 Request a Movie\n\n"
        "Please tell me the name of the movie you want to request:\n\n"
        "To cancel, type /cancel."
    )
    return REQUEST_MOVIE_NAME

async def get_movie_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the movie request from user."""
    movie_name = update.message.text
    user_id = update.effective_user.id
    
    # First check if the movie already exists
    existing_movies = db.search_movies(movie_name, limit=5)
    if existing_movies:
        message_text = f"🎬 Found similar movies:\n\n"
        buttons = []
        for i, movie in enumerate(existing_movies, 1):
            message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
            buttons.append([InlineKeyboardButton(f"🎬 {movie.get('title', 'Unknown')}", callback_data=f"view_{movie['movie_id']}")])
        
        buttons.append([InlineKeyboardButton("📝 Still Request This Movie", callback_data=f"force_request")])
        context.user_data['requested_movie'] = movie_name
        
        await update.message.reply_html(
            message_text + "\nIf none of these match what you're looking for, you can still request it:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return REQUEST_MOVIE_NAME
    else:
        # Movie not found, add to requests
        request_id = db.add_movie_request(user_id, movie_name)
        from utils import restore_default_commands
        
        # Restore default commands
        await restore_default_commands(context, update.effective_chat.id)
        
        await update.message.reply_text(
            f"✅ Request Submitted!\n\n"
            f"Your request for '{movie_name}' has been submitted to our admins.\n"
            f"Request ID: {request_id}\n\n"
            "You'll be notified when the movie is uploaded. Thank you for your patience!"
        )
        return ConversationHandler.END

async def force_request_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Force add a movie request even if similar movies exist."""
    query = update.callback_query
    await query.answer()
    
    movie_name = context.user_data.get('requested_movie')
    if not movie_name:
        await query.edit_message_text("Error: Movie name not found. Please try again.")
        return ConversationHandler.END
    
    user_id = query.from_user.id
    request_id = db.add_movie_request(user_id, movie_name)
    
    await query.edit_message_text(
        f"✅ **Request Submitted!**\n\n"
        f"Your request for '{movie_name}' has been submitted to our admins.\n"
        f"Request ID: {request_id}\n\n"
        "You'll be notified when the movie is uploaded. Thank you for your patience!"
    )
    return ConversationHandler.END

# --- Show Requests (Admin/Owner) ---

@restricted(allowed_roles=['owner', 'admin'])
async def show_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending movie requests to admins/owners."""
    pending_requests = db.get_pending_requests(limit=10)
    
    if not pending_requests:
        await update.message.reply_text("🎉 No pending movie requests at the moment!")
        return
    
    await update.message.reply_text(f"📋 Found {len(pending_requests)} pending movie requests:\n")
    
    # Send each request as individual message
    for i, req in enumerate(pending_requests, 1):
        user_info = f"@{req['users'].get('username')}" if req['users'].get('username') else f"ID: {req['user_id']}"
        
        message_text = f"Request #{i}: {req['movie_name']}\n"
        message_text += f"👤 Requested by: {user_info}\n"
        message_text += f"🗓️ On: {req['requested_at'][:10]}"
        
        # Individual buttons for each request
        buttons = [
            [
                InlineKeyboardButton("✅ Done", callback_data=f"req_done_{req['request_id']}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"req_del_{req['request_id']}")
            ]
        ]
        
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# --- Remove Movie (Owner/Admin) ---

@restricted(allowed_roles=['owner', 'admin'])
async def remove_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the remove movie conversation."""
    from utils import set_conversation_commands
    
    # Set conversation commands
    await set_conversation_commands(context, update.effective_chat.id)
    
    await update.message.reply_text(
        "🗑️ Remove Movie\n\n"
        "Please enter the name of the movie you want to remove:\n\n"
        "To cancel, type /cancel."
    )
    return DELETE_MOVIE_NAME

async def get_movie_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie deletion."""
    movie_name = update.message.text
    
    movies = db.search_movies(movie_name, limit=10)
    if not movies:
        await update.message.reply_text(f"❌ No movies found with name '{movie_name}'. Please try again or /cancel.")
        return DELETE_MOVIE_NAME
    
    if len(movies) == 1:
        # Only one movie found, show confirmation
        movie = movies[0]
        context.user_data['movie_to_delete'] = movie
        
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Delete", callback_data="confirm_delete")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")]
        ]
        
        await update.message.reply_html(
            f"🗑️ Confirm Deletion\n\n"
            f"Are you sure you want to delete:\n"
            f"<b>{movie.get('title', 'Unknown')}</b>\n\n"
            f"This action cannot be undone!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DELETE_MOVIE_NAME
    else:
        # Multiple movies found
        message_text = f"🎬 Found {len(movies)} movies:\n\n"
        buttons = []
        
        for i, movie in enumerate(movies, 1):
            message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
            buttons.append([InlineKeyboardButton(f"🗑️ Delete: {movie.get('title', 'Unknown')}", callback_data=f"delete_{movie['movie_id']}")])
        
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")])
        
        await update.message.reply_html(
            message_text + "\nSelect the movie you want to delete:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return DELETE_MOVIE_NAME

async def confirm_movie_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie deletion confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_delete":
        await query.edit_message_text("❌ Movie deletion cancelled.")
        return ConversationHandler.END
    elif query.data == "confirm_delete":
        movie = context.user_data.get('movie_to_delete')
        if movie:
            success = db.delete_movie(movie['movie_id'])
            if success:
                await query.edit_message_text(f"✅ Movie '{movie.get('title', 'Unknown')}' has been deleted successfully.")
            else:
                await query.edit_message_text("❌ Failed to delete the movie. Please try again.")
        else:
            await query.edit_message_text("❌ Error: Movie information not found.")
        return ConversationHandler.END
    elif query.data.startswith("delete_"):
        movie_id = int(query.data.split("_")[1])
        movie = db.get_movie_details(movie_id)
        if movie:
            success = db.delete_movie(movie_id)
            if success:
                await query.edit_message_text(f"✅ Movie '{movie.get('title', 'Unknown')}' has been deleted successfully.")
            else:
                await query.edit_message_text("❌ Failed to delete the movie. Please try again.")
        else:
            await query.edit_message_text("❌ Error: Movie not found.")
        return ConversationHandler.END

# --- Show Stats (Owner/Admin) ---

@restricted(allowed_roles=['owner', 'admin'])
async def show_stats_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the show stats conversation."""
    from utils import set_conversation_commands
    
    # Set conversation commands
    await set_conversation_commands(context, update.effective_chat.id)
    
    await update.message.reply_text(
        "📊 Movie Statistics\n\n"
        "Please enter the name of the movie to see its statistics:\n\n"
        "To cancel, type /cancel."
    )
    return SHOW_STATS_MOVIE_NAME

async def get_movie_for_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie stats request."""
    movie_name = update.message.text
    
    movies = db.search_movies(movie_name, limit=10)
    if not movies:
        await update.message.reply_text(f"❌ No movies found with name '{movie_name}'. Please try again or /cancel.")
        return SHOW_STATS_MOVIE_NAME
    
    if len(movies) == 1:
        # Only one movie found, show stats
        movie = movies[0]
        await show_movie_stats(update, context, movie)
        return ConversationHandler.END
    else:
        # Multiple movies found
        message_text = f"🎬 Found {len(movies)} movies:\n\n"
        buttons = []
        
        for i, movie in enumerate(movies, 1):
            message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
            buttons.append([InlineKeyboardButton(f"📊 {movie.get('title', 'Unknown')}", callback_data=f"stats_{movie['movie_id']}")])
        
        await update.message.reply_html(
            message_text + "\nSelect the movie to see statistics:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return SHOW_STATS_MOVIE_NAME

async def show_movie_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Show statistics for a specific movie."""
    stats_text = f"📊 Statistics for {movie.get('title', 'Unknown')}\n\n"
    stats_text += f"🎬 Movie ID: {movie['movie_id']}\n"
    stats_text += f"📅 Added on: {movie.get('added_at', 'Unknown')[:10]}\n"
    stats_text += f"👤 Added by: {movie.get('added_by', 'Unknown')}\n"
    stats_text += f"📥 Total Downloads: {movie.get('download_count', 0)}\n"
    stats_text += f"🗂️ Available Qualities: {', '.join(movie.get('files', {}).keys())}\n"
    stats_text += f"🌐 Languages: {', '.join(movie.get('languages', []))}\n"
    stats_text += f"📂 Categories: {', '.join(movie.get('categories', []))}\n"
    
    await update.message.reply_html(stats_text)

async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle stats callback from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("stats_"):
        movie_id = int(query.data.split("_")[1])
        movie = db.get_movie_details(movie_id)
        if movie:
            await show_movie_stats(query, context, movie)
        else:
            await query.edit_message_text("❌ Error: Movie not found.")
    
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel any ongoing conversation."""
    from utils import restore_default_commands
    
    # Restore default commands
    await restore_default_commands(context, update.effective_chat.id)
    
    await update.message.reply_text("❌ Action cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

# Conversation Handlers
request_movie_conv = ConversationHandler(
    entry_points=[
        CommandHandler("request", request_movie_start),
        MessageHandler(filters.Regex("^🙏 Request Movie$"), request_movie_start)
    ],
    states={
        REQUEST_MOVIE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_request),
            CallbackQueryHandler(force_request_movie, pattern="^force_request$")
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)

remove_movie_conv = ConversationHandler(
    entry_points=[CommandHandler("removemovie", remove_movie_start)],
    states={
        DELETE_MOVIE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_to_delete),
            CallbackQueryHandler(confirm_movie_deletion, pattern="^(confirm_delete|cancel_delete|delete_)")
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)

show_stats_conv = ConversationHandler(
    entry_points=[CommandHandler("showstats", show_stats_start)],
    states={
        SHOW_STATS_MOVIE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_for_stats),
            CallbackQueryHandler(handle_stats_callback, pattern="^stats_")
        ]
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)]
)

# Main handler list to be imported
movie_handlers = [
    # Conversation handlers first
    request_movie_conv,
    remove_movie_conv,
    show_stats_conv,
    # Regular handlers
    MessageHandler(filters.Regex("^🔍 Search Movies$"), search_movies),
    MessageHandler(filters.Regex("^📂 Browse Categories$"), browse_categories),
    MessageHandler(filters.Regex("^📊 Show Requests$"), show_requests),
    # Text search handler (should be last to catch search queries)
    MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.REPLY, handle_search_query)
]
