# MovieZoneBot/handlers/callback_handler.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest

import database as db
from utils import generate_ad_link_button, get_quality_buttons

# লগিং সেটআপ
logger = logging.getLogger(__name__)

async def handle_request_action(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, action: str):
    """Handles 'Done' or 'Delete' action on a movie request."""
    query = update.callback_query
    
    new_status = 'accepted' if action == 'done' else 'deleted'
    request_info = db.update_request_status(request_id, new_status)

    if not request_info:
        await query.answer("Could not update this request. It might have been handled already.", show_alert=True)
        return

    await query.answer(f"Request marked as {new_status}.")
    
    # Notify the user if the request was accepted
    if new_status == 'accepted':
        notification_text = (
            f"🎉 Good news! Your requested movie, {request_info['movie_name']}, has been uploaded.\n\n"
            "You can now find it using the 'Search Movies' button in the bot."
        )
        try:
            await context.bot.send_message(
                chat_id=request_info['user_id'],
                text=notification_text,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Sent upload notification to user {request_info['user_id']} for movie '{request_info['movie_name']}'.")
        except BadRequest:
            logger.warning(f"Could not send notification to user {request_info['user_id']}. They may have blocked the bot.")
        except Exception as e:
            logger.error(f"Failed to send notification to user {request_info['user_id']}: {e}")

    # Refresh the request list
    pending_requests = db.get_pending_requests(limit=10)
    if not pending_requests:
        await query.edit_message_text("🎉 All pending requests have been handled!")
        return

    message_text = "📋 Pending Movie Requests (Updated)\n\n"
    buttons = []
    for i, req in enumerate(pending_requests, 1):
        user_info = f"@{req['users']['username']}" if req['users'].get('username') else f"ID: {req['user_id']}"
        message_text += f"{i}. {req['movie_name']}\n   👤 Requested by: {user_info}\n   🗓️ On: {req['requested_at'][:10]}\n\n"
        buttons.append([
            InlineKeyboardButton(f"✅ Done {i}", callback_data=f"req_done_{req['request_id']}"),
            InlineKeyboardButton(f"🗑️ Delete {i}", callback_data=f"req_del_{req['request_id']}")
        ])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(message_text, reply_markup=reply_markup)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all callback queries from inline buttons."""
    query = update.callback_query
    # Always answer the callback query first to remove the loading icon
    await query.answer()

    user_id = query.from_user.id
    callback_data = query.data
    logger.info(f"Callback query received from user {user_id}: {callback_data}")

    parts = callback_data.split('_')
    prefix = parts[0]

    try:
        if prefix == 'quality':
            movie_id, quality = int(parts[1]), '_'.join(parts[2:]) # Handles qualities like '720p_HEVC'
            movie_details = db.get_movie_details(movie_id)
            if not movie_details:
                await query.edit_message_text("❌ Error: Movie not found. It might have been deleted.")
                return

            movie_title = movie_details.get('title', 'this movie')
            await query.edit_message_text(f"To download {movie_title} in {quality}, you need to watch a short ad.")
            
            ad_link_markup = generate_ad_link_button(user_id=user_id, movie_id=movie_id, quality=quality)
            if ad_link_markup:
                await query.message.reply_text("👇 Click the button below to proceed.", reply_markup=ad_link_markup)
            else:
                await query.message.reply_text("❌ Sorry, something went wrong while generating the download link. Please try again.")

        elif prefix == 'view':
            movie_id = int(parts[1])
            movie_details = db.get_movie_details(movie_id)
            if not movie_details:
                await query.edit_message_text("❌ Error: Movie not found.")
                return

            # Keep original format but with new emoji icons
            response_text = f"🎬 {movie_details.get('title', 'N/A')}\n\n" \
                            f"Description: {movie_details.get('description', 'N/A')}\n" \
                            f"📅 Release Year: {movie_details.get('release_year', 'N/A')}\n" \
                            f"⏰ Runtime: {movie_details.get('runtime', 'N/A')}\n" \
                            f"⭐ IMDb: {movie_details.get('imdb_rating', 'N/A')}/10\n" \
                            f"🎭 Languages: {', '.join(movie_details.get('languages', []))}\n" \
                            f"🎪 Categories: {', '.join(movie_details.get('categories', []))}"
            
            # Create quality buttons
            files = movie_details.get('files', {})
            buttons = []
            for quality in files.keys():
                callback_data = f"quality_{movie_id}_{quality}"
                buttons.append([InlineKeyboardButton(f"🎬 {quality}", callback_data=callback_data)])
            
            quality_buttons_markup = InlineKeyboardMarkup(buttons)
            
            thumbnail_id = movie_details.get('thumbnail_file_id')
            if thumbnail_id:
                try:
                    await query.edit_message_text("Please see the movie details below:")
                    await query.message.reply_photo(photo=thumbnail_id, caption=response_text, reply_markup=quality_buttons_markup)
                except Exception as e:
                    logger.error(f"Failed to send photo for movie {movie_id}: {e}")
                    await query.message.reply_text(response_text, reply_markup=quality_buttons_markup)
            else:
                await query.message.reply_text(response_text, reply_markup=quality_buttons_markup)
        
        elif prefix == 'req':
            action, request_id = parts[1], int(parts[2])
            await handle_request_action(update, context, request_id, action)

        elif prefix == 'cat':
            # Handle category selection
            category = '_'.join(parts[1:]).replace('_', ' ')
            movies = db.get_movies_by_category(category, limit=10)
            
            if not movies:
                await query.edit_message_text(f"❌ No movies found in category: {category}")
                return
            
            message_text = f"🎬 Movies in {category}:\n\n"
            buttons = []
            
            for i, movie in enumerate(movies, 1):
                message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
                buttons.append([InlineKeyboardButton(f"🎬 {movie.get('title', 'Unknown')}", callback_data=f"view_{movie['movie_id']}")])
            
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text(message_text, reply_markup=reply_markup)

        else:
            logger.warning(f"Unhandled callback prefix: {prefix}")
            await query.edit_message_text("Sorry, there was an error processing your request.")

    except (IndexError, ValueError) as e:
        logger.error(f"Error processing callback_data '{callback_data}': {e}")
        await query.edit_message_text("❌ An unexpected error occurred. Please try again.")
    except Exception as e:
        logger.error(f"A critical error occurred in handle_callback_query: {e}")
        await query.edit_message_text("❌ A critical error occurred. The developer has been notified.")

# Handler to be imported in main.py
callback_query_handler = CallbackQueryHandler(handle_callback_query)
