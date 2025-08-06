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
                text=notification_text
            )
            logger.info(f"Sent upload notification to user {request_info['user_id']} for movie '{request_info['movie_name']}'.")
        except BadRequest:
            logger.warning(f"Could not send notification to user {request_info['user_id']}. They may have blocked the bot.")
        except Exception as e:
            logger.error(f"Failed to send notification to user {request_info['user_id']}: {e}")

    # Delete the current message completely
    try:
        await query.delete_message()
        logger.info(f"Deleted request message after {action} action for request {request_id}")
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")
        # Fallback: edit message to show it's handled
        action_emoji = "✅" if action == 'done' else "🗑️"
        await query.edit_message_text(f"{action_emoji} Request '{request_info['movie_name']}' has been {new_status}.")


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

            # Build response with Title: prefix and no Description field
            response_text = f"🎬 Title: {movie_details.get('title', 'N/A')}\n\n"
            
            # Only include non-N/A fields
            release_year = movie_details.get('release_year', 'N/A')
            if release_year != 'N/A':
                response_text += f"📅 Release Year: {release_year}\n"
            
            runtime = movie_details.get('runtime', 'N/A')
            if runtime != 'N/A':
                response_text += f"⏰ Runtime: {runtime}\n"
            
            imdb_rating = movie_details.get('imdb_rating', 'N/A')
            if imdb_rating != 'N/A':
                response_text += f"⭐ IMDb: {imdb_rating}/10\n"
            
            languages = movie_details.get('languages', [])
            if languages:
                response_text += f"🎭 Languages: {', '.join(languages)}\n"
            
            categories = movie_details.get('categories', [])
            if categories:
                response_text += f"🎪 Categories: {', '.join(categories)}"
            
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

        elif callback_data in ['confirm_delete', 'cancel_delete'] or callback_data.startswith('delete_'):
            # These callbacks are handled by the remove_movie conversation handler
            # We should not process them here, let the conversation handler take care of them
            return
            
        elif callback_data == 'browse_categories':
            # Handle "Back to Categories" button - Show browse categories
            from config import BROWSE_CATEGORIES
            
            # Create category buttons in 2-column layout
            buttons = []
            for i in range(0, len(BROWSE_CATEGORIES), 2):
                row = []
                for j in range(2):
                    if i + j < len(BROWSE_CATEGORIES):
                        category = BROWSE_CATEGORIES[i + j]
                        row.append(InlineKeyboardButton(category, callback_data=f"cat_{category.replace(' ', '_')}"))
                if row:
                    buttons.append(row)
            
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.edit_message_text("📂 Browse Categories\n\nSelect a category to explore movies:", reply_markup=reply_markup)

        elif prefix == 'cat':
            # Handle category selection - Show movies in 3x10 grid format
            try:
                # Parse category and page from callback data
                callback_parts = callback_data.split('_')
                if callback_parts[-1].isdigit():
                    # Has page number: cat_Hollywood_🇺🇸_2
                    page = int(callback_parts[-1])
                    category_parts = callback_parts[1:-1]
                else:
                    # No page number: cat_Hollywood_🇺🇸
                    page = 1
                    category_parts = callback_parts[1:]
                
                # Reconstruct category name properly
                category = '_'.join(category_parts).replace('_', ' ')
                
                logger.info(f"Category browsing - Original callback: {callback_data}, Parsed category: '{category}', Page: {page}")
                
                # Special handling for "All" category - alphabet filtering
                if category == "All 🌐":
                    await query.edit_message_text(
                        "🌐 All Movies - Alphabet Filter\n\n"
                        "Please send any letter (A-Z) to see movies starting with that letter.\n\n"
                        "For example, send 'A' to see all movies starting with A."
                    )
                    return
                
                # Get movies with pagination (30 per page)
                offset = (page - 1) * 30
                movies = db.get_movies_by_category(category, limit=31, offset=offset)  # Get 31 to check if there's a next page
                
                if not movies:
                    # Debug: Show what categories are available
                    all_movies = db.load_json(db.MOVIES_FILE)
                    available_categories = set()
                    for movie_data in all_movies.get("movies", {}).values():
                        available_categories.update(movie_data.get("categories", []))
                    
                    logger.error(f"No movies found for category: '{category}'. Available categories: {list(available_categories)}")
                    await query.edit_message_text(f"❌ No movies found in category: {category}\n\nAvailable categories: {', '.join(list(available_categories))}")
                    return
            except Exception as e:
                logger.error(f"Error parsing category callback data '{callback_data}': {e}")
                await query.edit_message_text("❌ Error processing category request. Please try again.")
                return
            
            # Create 3-column grid layout
            buttons = []
            movies_to_show = movies[:30]  # Show max 30 movies
            
            # Group movies into rows of 3
            for i in range(0, len(movies_to_show), 3):
                row = []
                for j in range(3):
                    if i + j < len(movies_to_show):
                        movie = movies_to_show[i + j]
                        title = movie.get('title', 'Unknown')
                        # Truncate long titles for button display
                        if len(title) > 15:
                            title = title[:12] + "..."
                        row.append(InlineKeyboardButton(f"🎬 {title}", callback_data=f"view_{movie['movie_id']}"))
                if row:
                    buttons.append(row)
            
            # Add navigation buttons if needed
            nav_buttons = []
            if page > 1:
                nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"cat_{category.replace(' ', '_')}_{page-1}"))
            
            if len(movies) > 30:  # There are more movies
                nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"cat_{category.replace(' ', '_')}_{page+1}"))
            
            if nav_buttons:
                buttons.append(nav_buttons)
            
            # Add back to categories button
            buttons.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="browse_categories")])
            
            reply_markup = InlineKeyboardMarkup(buttons)
            
            # Show only buttons, no text message
            if page == 1:
                await query.edit_message_text(f"🎬 {category} Movies:", reply_markup=reply_markup)
            else:
                await query.edit_message_text(f"🎬 {category} Movies (Page {page}):", reply_markup=reply_markup)

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
