# MovieZoneBot/config.py

import os

# --- Telegram Bot Configuration ---
# Your Telegram bot token from BotFather
BOT_TOKEN = "7489158288:AAG3r41T8kG4O01BpBeICApd28p9g4DJJ4A"

# আপনার বটের ইউজারনেম (t.me/YourBotUsername) - আপনার দেওয়া ছবি অনুযায়ী
BOT_USERNAME = "MoviezoneDownloadbot"

# --- Owner Configuration ---
# বটের মালিকের টেলিগ্রাম ইউজার আইডি
OWNER_ID = 5379553841

# --- Ad Page Configuration ---
# আপনার GitHub Pages-এ থাকা অ্যাড পেজের URL
AD_PAGE_URL = "https://sudip1844.github.io/moviezone-redirect-page-"

# --- Bot Settings ---
# মুভি যোগ করার সময় যে ক্যাটাগরিগুলো দেখানো হবে (আপনার ছবি অনুযায়ী)
# Categories for movie addition (includes Hentai for admin/owner only)
ADMIN_CATEGORIES = [
    "Bollywood 🇮🇳", "Hollywood 🇺🇸", "South Indian 🎬", "Web Series 🎥",
    "Bengali ✨", "Anime & cartoon 🌀", "Comedy 🤣", "Action 💥",
    "Romance 💑", "Horror 😱", "Thriller 🔍", "Sci-Fi 🛸",
    "K-Drama 🎎", "18+ 🔞", "Hentai 💦"
]

# Categories for browsing (includes All for alphabet filtering)
BROWSE_CATEGORIES = [
    "All 🌐", "Bollywood 🇮🇳", "Hollywood 🇺🇸", "South Indian 🎬", "Web Series 🎥",
    "Bengali ✨", "Anime & cartoon 🌀", "Comedy 🤣", "Action 💥",
    "Romance 💑", "Horror 😱", "Thriller 🔍", "Sci-Fi 🛸",
    "K-Drama 🎎", "18+ 🔞", "Hentai 💦"
]

# Backward compatibility - default categories for movie addition
CATEGORIES = ADMIN_CATEGORIES

# মুভি যোগ করার সময় যে ভাষাগুলো দেখানো হবে
LANGUAGES = [
    "Bengali", "Hindi", "English", "Tamil", "Telugu", "Korean", "Gujarati"
]

# Conversation Handler এর জন্য টাইমআউট (সেকেন্ডে)
# যদি ব্যবহারকারী 600 সেকেন্ড (10 মিনিট) ধরে কোনো উত্তর না দেয়, কথোপকথন বাতিল হয়ে যাবে
CONVERSATION_TIMEOUT = 600

# পোস্টের টেমপ্লেট
# সিঙ্গেল মুভির জন্য
SINGLE_MOVIE_POST_TEMPLATE = """
🍿 <b>{title}</b>

📌 <b>Language:</b> {languages}
☘️ <b>Genre:</b> {categories}
🗓️ <b>Release Year:</b> {release_year}
⏰ <b>Runtime:</b> {runtime}
⭐️ <b>IMDb Rating:</b> {imdb_rating}/10

🔗 <b>Download Link Below</b>
{download_links}

🔥 <b>Ultra Fast • Direct Access</b>
🛰️ <b>Join Now:</b> @{channel_username}
🔔 <b>New Movies Uploaded Daily!</b>
"""

# ওয়েব সিরিজের জন্য
SERIES_POST_TEMPLATE = """
📺 <b>{title}</b>

📌 <b>Language:</b> {languages}
☘️ <b>Genre:</b> {categories}
🗓️ <b>Release Year:</b> {release_year}
⏰ <b>Runtime:</b> {runtime}
⭐️ <b>IMDb Rating:</b> {imdb_rating}/10

<b>Available Episode - (Total ep)</b>
🔗 <b>Download Link Below</b>
{download_links}

🔥 <b>Ultra Fast • Direct Access</b>
🛰️ <b>Join Now:</b> @{channel_username}
🔔 <b>New Movies Uploaded Daily!</b>
"""