# MovieZoneBot/handlers/conversation_handlers.py

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode
from typing import Optional

import database as db
from utils import restricted, format_movie_post
from config import CATEGORIES, LANGUAGES, CONVERSATION_TIMEOUT, OWNER_ID

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# Conversation states (কথোপকথনের ধাপ)
(
    GET_THUMBNAIL, GET_TITLE, GET_RELEASE_YEAR, GET_RUNTIME,
    GET_IMDB_RATING, CHOOSE_CATEGORIES, CHOOSE_LANGUAGES, CHOOSE_FILE_TYPE,
    UPLOAD_SINGLE_FILES, UPLOAD_SERIES_FILES, CONFIRM_POST, SELECT_CHANNELS
) = range(12)

# --- Helper Functions for this Conversation ---

def build_selection_keyboard(options: list, selected_options: set) -> InlineKeyboardMarkup:
    """ ক্যাটাগরি বা ভাষা নির্বাচনের জন্য কীবোর্ড তৈরি করে। """
    buttons = []
    row = []
    for option in options:
        # যদি কোনো আইটেম ইতোমধ্যে সিলেক্ট করা থাকে, তবে তার পাশে একটি ✅ চিহ্ন যোগ করা হয়
        text = f"✅ {option}" if option in selected_options else option
        row.append(InlineKeyboardButton(text, callback_data=f"select_{option}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    # "Done" বাটন যোগ করা হয়
    buttons.append([InlineKeyboardButton("➡️ Done", callback_data="select_done")])
    return InlineKeyboardMarkup(buttons)

# --- Conversation Handler Functions ---

@restricted(allowed_roles=['owner', 'admin'])
async def add_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ /addmovie কমান্ড দিয়ে কথোপকথন শুরু করে। """
    # আগের কোনো ডেটা থাকলে তা পরিষ্কার করে
    context.user_data.pop('movie_data', None)
    context.user_data['movie_data'] = {
        'added_by': update.effective_user.id,
        'categories': set(),
        'languages': set(),
        'files': {} # { '480p': 'file_id_1', '720p': 'file_id_2' }
    }
    
    await update.message.reply_text(
        "🎬 **Add New Movie/Series**\n\n"
        "Step 1: Please send the thumbnail for the movie (as a photo).\n\n"
        "To cancel at any time, type /cancel.",
        parse_mode=ParseMode.MARKDOWN
    )
    return GET_THUMBNAIL

async def get_thumbnail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ থাম্বনেল সংগ্রহ করে এবং পরবর্তী ধাপে যায়। """
    photo = update.message.photo[-1] # Best quality photo
    context.user_data['movie_data']['thumbnail_file_id'] = photo.file_id
    logger.info(f"User {update.effective_user.id} uploaded a thumbnail.")
    
    await update.message.reply_text("✅ Thumbnail saved.\n\nStep 2: Now, enter the movie title.")
    return GET_TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ টাইটেল সংগ্রহ করে। """
    context.user_data['movie_data']['title'] = update.message.text
    await update.message.reply_text("✅ Title saved.\n\nStep 3: Enter the release year (e.g., 2023).")
    return GET_RELEASE_YEAR

async def get_release_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['movie_data']['release_year'] = update.message.text
    await update.message.reply_text("✅ Release year saved.\n\nStep 4: Enter the runtime (e.g., 2hr 14min).")
    return GET_RUNTIME

async def get_runtime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['movie_data']['runtime'] = update.message.text
    await update.message.reply_text("✅ Runtime saved.\n\nStep 5: Enter the IMDb rating (e.g., 8.3).")
    return GET_IMDB_RATING

async def get_imdb_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['movie_data']['imdb_rating'] = update.message.text
    
    keyboard = build_selection_keyboard(CATEGORIES, set())
    await update.message.reply_text(
        "✅ IMDb rating saved.\n\nStep 6: Please select the movie categories (you can select multiple).",
        reply_markup=keyboard
    )
    return CHOOSE_CATEGORIES

async def choose_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ ক্যাটাগরি নির্বাচন হ্যান্ডেল করে। """
    query = update.callback_query
    await query.answer()
    
    selected_option = query.data.split('_', 1)[1]
    
    if selected_option == 'done':
        if not context.user_data['movie_data']['categories']:
            await query.message.reply_text("⚠️ Please select at least one category before continuing.")
            return CHOOSE_CATEGORIES
            
        keyboard = build_selection_keyboard(LANGUAGES, set())
        await query.edit_message_text(
            "✅ Categories saved.\n\nStep 7: Now select the languages.",
            reply_markup=keyboard
        )
        return CHOOSE_LANGUAGES
    
    # Add or remove the category from the set
    if selected_option in context.user_data['movie_data']['categories']:
        context.user_data['movie_data']['categories'].remove(selected_option)
    else:
        context.user_data['movie_data']['categories'].add(selected_option)
    
    # Update the keyboard with the new selection
    keyboard = build_selection_keyboard(CATEGORIES, context.user_data['movie_data']['categories'])
    await query.edit_message_reply_markup(reply_markup=keyboard)
    return CHOOSE_CATEGORIES

async def choose_languages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ ভাষা নির্বাচন হ্যান্ডেল করে। """
    query = update.callback_query
    await query.answer()
    
    selected_option = query.data.split('_', 1)[1]

    if selected_option == 'done':
        if not context.user_data['movie_data']['languages']:
            await query.message.reply_text("⚠️ Please select at least one language before continuing.")
            return CHOOSE_LANGUAGES

        keyboard = [[InlineKeyboardButton("Single Movie File", callback_data="filetype_single")],
                    [InlineKeyboardButton("Multiple Series Files", callback_data="filetype_series")]]
        await query.edit_message_text(
            "✅ Languages saved.\n\nStep 9: Is this a single movie or a web series?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CHOOSE_FILE_TYPE
    
    if selected_option in context.user_data['movie_data']['languages']:
        context.user_data['movie_data']['languages'].remove(selected_option)
    else:
        context.user_data['movie_data']['languages'].add(selected_option)
        
    keyboard = build_selection_keyboard(LANGUAGES, context.user_data['movie_data']['languages'])
    await query.edit_message_reply_markup(reply_markup=keyboard)
    return CHOOSE_LANGUAGES

async def choose_file_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ ফাইল টাইপ (সিঙ্গেল/সিরিজ) নির্বাচন হ্যান্ডেল করে। """
    query = update.callback_query
    await query.answer()
    
    file_type = query.data.split('_')[1]
    
    if file_type == 'single':
        context.user_data['movie_data']['is_series'] = False
        reply_keyboard = [['480p', '720p', '1080p'], ["✅ All Done"]]
        await query.edit_message_text("Step 10: Please upload the movie files. Select a quality to upload.")
        await query.message.reply_text(
            "Select a quality to upload files for:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return UPLOAD_SINGLE_FILES
    elif file_type == 'series':
        context.user_data['movie_data']['is_series'] = True
        context.user_data['movie_data']['next_episode'] = 1
        await query.edit_message_text(f"Step 10: Please upload Episode 1.")
        return UPLOAD_SERIES_FILES

async def upload_single_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ সিঙ্গেল মুভির ফাইল আপলোড হ্যান্ডেল করে। """
    if update.message.text in ['480p', '720p', '1080p']:
        quality = update.message.text
        context.user_data['selected_quality'] = quality
        await update.message.reply_text(f"OK. Now, send the file for **{quality}**.", parse_mode=ParseMode.MARKDOWN)
        return UPLOAD_SINGLE_FILES
    elif update.message.text == "✅ All Done":
        return await all_files_done(update, context)
    else:
        # Handle file upload
        quality = context.user_data.get('selected_quality')
        if not quality:
            await update.message.reply_text("Please select a quality first using the buttons.")
            return UPLOAD_SINGLE_FILES

        # We can handle video, document, etc.
        file = update.message.effective_attachment
        if not file:
            await update.message.reply_text("Please send a valid file (video or document).")
            return UPLOAD_SINGLE_FILES
            
        context.user_data['movie_data']['files'][quality] = (file.file_id, file.file_unique_id)
        del context.user_data['selected_quality']
        
        reply_keyboard = [['480p', '720p', '1080p'], ["✅ All Done"]]
        await update.message.reply_text(
            f"✅ **{quality}** file saved. Select another quality or click 'All Done' when finished.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True),
            parse_mode=ParseMode.MARKDOWN
        )
        return UPLOAD_SINGLE_FILES
    
async def upload_series_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ সিরিজের ফাইল আপলোড হ্যান্ডেল করে। """
    if update.message.text and update.message.text.startswith("Upload Episode"):
        episode_num = context.user_data['movie_data']['next_episode']
        await update.message.reply_text(f"OK. Now, send the file for Episode {episode_num}.")
        return UPLOAD_SERIES_FILES
    elif update.message.text == "✅ All Done":
        return await all_files_done(update, context)
    else:
        # Handle file upload
        file = update.message.effective_attachment
        if not file:
            await update.message.reply_text("Please send a valid file (video or document).")
            return UPLOAD_SERIES_FILES
            
        episode_num = context.user_data['movie_data']['next_episode']
        quality_key = f"E{episode_num:02d}" # E01, E02...
        
        context.user_data['movie_data']['files'][quality_key] = (file.file_id, file.file_unique_id)
        
        await update.message.reply_text(f"✅ Episode {episode_num} saved.")
        
        context.user_data['movie_data']['next_episode'] += 1
        episode_num += 1
        
        reply_keyboard = [[f"Upload Episode {episode_num}"], ["✅ All Done"]]
        await update.message.reply_text(
            "Upload the next episode or click 'All Done'.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        )
        return UPLOAD_SERIES_FILES

async def all_files_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ সমস্ত ফাইল আপলোড শেষ হলে প্রিভিউ দেখায়। """
    movie_data = context.user_data['movie_data']
    
    if not movie_data.get('files'):
        await update.message.reply_text("⚠️ You haven't uploaded any files! Please upload at least one file or /cancel.")
        return UPLOAD_SINGLE_FILES if not movie_data.get('is_series') else UPLOAD_SERIES_FILES

    await update.message.reply_text("Great! All data collected. Generating preview...", reply_markup=ReplyKeyboardRemove())
    
    # Convert sets to lists for JSON serialization
    movie_data['categories'] = list(movie_data['categories'])
    movie_data['languages'] = list(movie_data['languages'])
    
    # প্রিভিউয়ের জন্য একটি temporary movie_id যোগ করি
    movie_data['movie_id'] = 'preview'
    
    # একটি ডামি চ্যানেল নাম দিয়ে প্রিভিউ তৈরি করা হচ্ছে
    preview_text = format_movie_post(movie_data, "moviezone969")
    
    # Show preview message first
    await update.message.reply_text("📋 Preview of your post:")
    
    # Show preview with thumbnail
    thumbnail_id = movie_data.get('thumbnail_file_id')
    if thumbnail_id:
        try:
            await update.message.reply_photo(
                photo=thumbnail_id,
                caption=preview_text,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send thumbnail in preview: {e}")
            await update.message.reply_html(preview_text)
    else:
        await update.message.reply_html(preview_text)
    
    # Show channels selection
    channels = db.get_all_channels()
    if channels:
        keyboard = []
        for channel in channels:
            keyboard.append([InlineKeyboardButton(f"📢 {channel['short_name']}", callback_data=f"channel_{channel['channel_id']}")])
        keyboard.append([InlineKeyboardButton("✅ Post to Selected Channels", callback_data="post_now")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")])
        
        await update.message.reply_text(
            "Select channels to post to:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_CHANNELS
    else:
        # No channels configured, just save the movie
        # Remove preview movie_id before saving
        if 'movie_id' in movie_data and movie_data['movie_id'] == 'preview':
            del movie_data['movie_id']
        movie_id = db.add_movie(movie_data)
        await update.message.reply_text(f"✅ Movie added successfully! Movie ID: {movie_id}")
        context.user_data.clear()
        return ConversationHandler.END

async def select_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """ চ্যানেল নির্বাচন হ্যান্ডেল করে। """
    query = update.callback_query
    await query.answer()
    
    if query.data == "post_now":
        # Save movie to database
        movie_data = context.user_data['movie_data']
        # Remove preview movie_id before saving
        if 'movie_id' in movie_data and movie_data['movie_id'] == 'preview':
            del movie_data['movie_id']
        movie_id = db.add_movie(movie_data)
        
        selected_channels = context.user_data.get('selected_channels', [])
        if selected_channels:
            # Post to selected channels
            for channel_id in selected_channels:
                try:
                    preview_text = format_movie_post(movie_data, "moviezone969")
                    if movie_data.get('thumbnail_file_id'):
                        await context.bot.send_photo(
                            chat_id=channel_id,
                            photo=movie_data['thumbnail_file_id'],
                            caption=preview_text,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=channel_id,
                            text=preview_text,
                            parse_mode=ParseMode.HTML
                        )
                    logger.info(f"Posted movie {movie_id} to channel {channel_id}")
                except Exception as e:
                    logger.error(f"Failed to post to channel {channel_id}: {e}")
        
        await query.edit_message_text(f"✅ Movie added successfully! Movie ID: {movie_id}")
        context.user_data.clear()
        return ConversationHandler.END
    
    elif query.data == "cancel_post":
        await query.edit_message_text("❌ Movie posting cancelled.")
        context.user_data.clear()
        return ConversationHandler.END
    
    elif query.data.startswith("channel_"):
        # Toggle channel selection
        channel_id = query.data.split("_", 1)[1]
        selected_channels = context.user_data.get('selected_channels', [])
        
        if channel_id in selected_channels:
            selected_channels.remove(channel_id)
        else:
            selected_channels.append(channel_id)
        
        context.user_data['selected_channels'] = selected_channels
        
        # Update keyboard
        channels = db.get_all_channels()
        keyboard = []
        for channel in channels:
            text = f"✅ {channel['short_name']}" if channel['channel_id'] in selected_channels else f"📢 {channel['short_name']}"
            keyboard.append([InlineKeyboardButton(text, callback_data=f"channel_{channel['channel_id']}")])
        keyboard.append([InlineKeyboardButton("✅ Post to Selected Channels", callback_data="post_now")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_post")])
        
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return SELECT_CHANNELS

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """কথোপকথন বাতিল করে।"""
    await update.message.reply_text("Movie addition cancelled.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END

# Conversation Handler
add_movie_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("addmovie", add_movie_start),
        MessageHandler(filters.Regex("^➕ Add Movie$"), add_movie_start)
    ],
    states={
        GET_THUMBNAIL: [MessageHandler(filters.PHOTO, get_thumbnail)],
        GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
        GET_RELEASE_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_release_year)],
        GET_RUNTIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_runtime)],
        GET_IMDB_RATING: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_imdb_rating)],
        CHOOSE_CATEGORIES: [CallbackQueryHandler(choose_categories, pattern="^select_")],
        CHOOSE_LANGUAGES: [CallbackQueryHandler(choose_languages, pattern="^select_")],
        CHOOSE_FILE_TYPE: [CallbackQueryHandler(choose_file_type, pattern="^filetype_")],
        UPLOAD_SINGLE_FILES: [MessageHandler(filters.TEXT | filters.ATTACHMENT, upload_single_files)],
        UPLOAD_SERIES_FILES: [MessageHandler(filters.TEXT | filters.ATTACHMENT, upload_series_files)],
        SELECT_CHANNELS: [CallbackQueryHandler(select_channels, pattern="^(channel_|post_now|cancel_post)")]
    },
    fallbacks=[CommandHandler('cancel', cancel_conversation)],
    conversation_timeout=CONVERSATION_TIMEOUT
)
