# MovieZoneBot/database.py

import json
import os
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = "data"

# Database file paths
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")
MOVIES_FILE = os.path.join(DATA_DIR, "movies.json")
CHANNELS_FILE = os.path.join(DATA_DIR, "channels.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "requests.json")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")

def initialize_database():
    """Initialize the database by creating necessary directories and files."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Initialize files if they don't exist
    files_to_init = {
        USERS_FILE: {},
        ADMINS_FILE: {},
        MOVIES_FILE: {"next_id": 1, "movies": {}},
        CHANNELS_FILE: {},
        REQUESTS_FILE: {"next_id": 1, "requests": {}},
        TOKENS_FILE: {}
    }
    
    for file_path, default_data in files_to_init.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Initialized {file_path}")

def load_json(file_path: str) -> Dict:
    """Load data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File {file_path} not found, returning empty dict")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return {}

def save_json(file_path: str, data: Dict):
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")

# --- User Management Functions ---

def user_exists(user_id: int) -> bool:
    """Check if a user exists in the database."""
    users = load_json(USERS_FILE)
    return str(user_id) in users

def add_user_if_not_exists(user_id: int, first_name: str, username: Optional[str] = None) -> bool:
    """Add a user to the database if they don't exist."""
    users = load_json(USERS_FILE)
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "joined_at": datetime.now().isoformat(),
            "is_active": True
        }
        save_json(USERS_FILE, users)
        logger.info(f"Added new user: {user_id} ({first_name})")
        return True
    else:
        # Update user info if changed
        user = users[user_id_str]
        updated = False
        if user.get("first_name") != first_name:
            user["first_name"] = first_name
            updated = True
        if user.get("username") != username:
            user["username"] = username
            updated = True
        if updated:
            save_json(USERS_FILE, users)
        return False

def get_user_role(user_id: int) -> str:
    """Get the role of a user (owner/admin/user)."""
    from config import OWNER_ID
    
    if user_id == OWNER_ID:
        return 'owner'
    
    admins = load_json(ADMINS_FILE)
    if str(user_id) in admins:
        return 'admin'
    
    return 'user'

# --- Admin Management Functions ---

def add_admin(admin_id: int, short_name: str, first_name: str, username: Optional[str] = None) -> bool:
    """Add a new admin to the database."""
    admins = load_json(ADMINS_FILE)
    admin_id_str = str(admin_id)
    
    if admin_id_str in admins:
        logger.warning(f"Admin {admin_id} already exists")
        return False
    
    admins[admin_id_str] = {
        "user_id": admin_id,
        "short_name": short_name,
        "first_name": first_name,
        "username": username,
        "added_at": datetime.now().isoformat()
    }
    save_json(ADMINS_FILE, admins)
    logger.info(f"Added new admin: {admin_id} ({short_name})")
    return True

def get_admin_info(admin_id: int) -> Optional[Dict]:
    """Get admin information by user ID."""
    admins = load_json(ADMINS_FILE)
    return admins.get(str(admin_id))

def remove_admin(identifier: str) -> bool:
    """Remove an admin by user ID or short name."""
    admins = load_json(ADMINS_FILE)
    
    # Try to find by user ID first
    if identifier in admins:
        del admins[identifier]
        save_json(ADMINS_FILE, admins)
        logger.info(f"Removed admin with ID: {identifier}")
        return True
    
    # Try to find by short name
    for admin_id, admin_data in admins.items():
        if admin_data.get("short_name") == identifier:
            del admins[admin_id]
            save_json(ADMINS_FILE, admins)
            logger.info(f"Removed admin with short name: {identifier}")
            return True
    
    logger.warning(f"Admin not found: {identifier}")
    return False

def get_all_admins() -> List[Dict]:
    """Get all admins."""
    admins = load_json(ADMINS_FILE)
    return list(admins.values())

# --- Movie Management Functions ---

def add_movie(movie_data: Dict) -> int:
    """Add a new movie to the database."""
    movies = load_json(MOVIES_FILE)
    movie_id = movies["next_id"]
    
    movie_data["movie_id"] = movie_id
    movie_data["added_at"] = datetime.now().isoformat()
    movie_data["download_count"] = 0
    
    movies["movies"][str(movie_id)] = movie_data
    movies["next_id"] += 1
    
    save_json(MOVIES_FILE, movies)
    logger.info(f"Added new movie: {movie_id} - {movie_data.get('title')}")
    return movie_id

def get_movie_details(movie_id: int) -> Optional[Dict]:
    """Get movie details by ID."""
    movies = load_json(MOVIES_FILE)
    return movies["movies"].get(str(movie_id))

def search_movies(query: str, limit: int = 10) -> List[Dict]:
    """Search movies by title."""
    movies = load_json(MOVIES_FILE)
    results = []
    
    query_lower = query.lower()
    for movie_data in movies["movies"].values():
        title = movie_data.get("title", "").lower()
        if query_lower in title:
            results.append(movie_data)
            if len(results) >= limit:
                break
    
    return results

def get_movies_by_first_letter(letter: str, limit: int = 30) -> List[Dict]:
    """Get movies that start with a specific letter."""
    movies = load_json(MOVIES_FILE)
    results = []
    
    letter_upper = letter.upper()
    for movie_data in movies["movies"].values():
        title = movie_data.get("title", "")
        if title and title[0].upper() == letter_upper:
            results.append(movie_data)
            if len(results) >= limit:
                break
    
    return results

def get_movies_by_category(category: str, limit: int = 10, offset: int = 0) -> List[Dict]:
    """Get movies by category with pagination support."""
    movies = load_json(MOVIES_FILE)
    
    if category == "All 🌐":
        # Return all movies for alphabet filtering
        all_matching = list(movies["movies"].values())
    else:
        # First collect all matching movies - handle exact category match
        all_matching = []
        for movie_data in movies["movies"].values():
            categories = movie_data.get("categories", [])
            # Check for exact category match
            for movie_category in categories:
                if category == movie_category:
                    all_matching.append(movie_data)
                    break
    
    # Sort by title for consistent ordering
    all_matching.sort(key=lambda x: x.get('title', '').lower())
    
    # Apply offset and limit
    start_index = offset
    end_index = offset + limit
    results = all_matching[start_index:end_index]
    
    logger.info(f"Category search for '{category}': found {len(all_matching)} movies, returning {len(results)}")
    return results

def delete_movie(movie_id: int) -> bool:
    """Delete a movie from the database."""
    movies = load_json(MOVIES_FILE)
    movie_id_str = str(movie_id)
    
    if movie_id_str in movies["movies"]:
        del movies["movies"][movie_id_str]
        save_json(MOVIES_FILE, movies)
        logger.info(f"Deleted movie: {movie_id}")
        return True
    
    return False

def increment_download_count(movie_id: int):
    """Increment the download count for a movie."""
    movies = load_json(MOVIES_FILE)
    movie_id_str = str(movie_id)
    
    if movie_id_str in movies["movies"]:
        movies["movies"][movie_id_str]["download_count"] = movies["movies"][movie_id_str].get("download_count", 0) + 1
        save_json(MOVIES_FILE, movies)

# --- Channel Management Functions ---

def add_channel(channel_id: str, channel_name: str, short_name: str) -> bool:
    """Add a new channel to the database."""
    channels = load_json(CHANNELS_FILE)
    
    if channel_id in channels:
        logger.warning(f"Channel {channel_id} already exists")
        return False
    
    channels[channel_id] = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "short_name": short_name,
        "added_at": datetime.now().isoformat()
    }
    save_json(CHANNELS_FILE, channels)
    logger.info(f"Added new channel: {channel_id} ({short_name})")
    return True

def remove_channel(identifier: str) -> bool:
    """Remove a channel by ID or short name."""
    channels = load_json(CHANNELS_FILE)
    
    # Try to find by channel ID first
    if identifier in channels:
        del channels[identifier]
        save_json(CHANNELS_FILE, channels)
        logger.info(f"Removed channel with ID: {identifier}")
        return True
    
    # Try to find by short name
    for channel_id, channel_data in channels.items():
        if channel_data.get("short_name") == identifier:
            del channels[channel_id]
            save_json(CHANNELS_FILE, channels)
            logger.info(f"Removed channel with short name: {identifier}")
            return True
    
    logger.warning(f"Channel not found: {identifier}")
    return False

def get_channel_info(channel_id: str) -> Optional[Dict]:
    """Get channel information by channel ID."""
    channels = load_json(CHANNELS_FILE)
    return channels.get(channel_id)

def get_all_channels() -> List[Dict]:
    """Get all channels."""
    channels = load_json(CHANNELS_FILE)
    return list(channels.values())

# --- Request Management Functions ---

def add_movie_request(user_id: int, movie_name: str) -> int:
    """Add a new movie request."""
    requests = load_json(REQUESTS_FILE)
    request_id = requests["next_id"]
    
    requests["requests"][str(request_id)] = {
        "request_id": request_id,
        "user_id": user_id,
        "movie_name": movie_name,
        "status": "pending",
        "requested_at": datetime.now().isoformat()
    }
    requests["next_id"] += 1
    
    save_json(REQUESTS_FILE, requests)
    logger.info(f"Added new movie request: {request_id} - {movie_name} by user {user_id}")
    return request_id

def get_pending_requests(limit: int = 10) -> List[Dict]:
    """Get pending movie requests."""
    requests = load_json(REQUESTS_FILE)
    users = load_json(USERS_FILE)
    
    pending_requests = []
    for request_data in requests["requests"].values():
        if request_data.get("status") == "pending":
            # Add user info
            user_id = request_data["user_id"]
            user_info = users.get(str(user_id), {})
            request_data["users"] = user_info
            pending_requests.append(request_data)
            if len(pending_requests) >= limit:
                break
    
    return pending_requests

def update_request_status(request_id: int, status: str) -> Optional[Dict]:
    """Update the status of a movie request."""
    requests = load_json(REQUESTS_FILE)
    request_id_str = str(request_id)
    
    if request_id_str in requests["requests"]:
        requests["requests"][request_id_str]["status"] = status
        requests["requests"][request_id_str]["updated_at"] = datetime.now().isoformat()
        save_json(REQUESTS_FILE, requests)
        logger.info(f"Updated request {request_id} status to {status}")
        return requests["requests"][request_id_str]
    
    return None

# --- Token Management Functions for Ad System ---

def create_ad_token(user_id: int, movie_id: int, quality: str) -> Optional[str]:
    """Create a token for ad-based download."""
    tokens = load_json(TOKENS_FILE)
    
    # Create a unique token
    timestamp = str(int(time.time()))
    token_data = f"{user_id}_{movie_id}_{quality}_{timestamp}"
    token = hashlib.sha256(token_data.encode()).hexdigest()[:32]
    
    # Get file info
    movie_details = get_movie_details(movie_id)
    if not movie_details:
        logger.error(f"Movie not found: {movie_id}")
        return None
    
    files = movie_details.get("files", {})
    if quality not in files:
        logger.error(f"Quality {quality} not found for movie {movie_id}")
        return None
    
    file_info = files[quality]
    # Handle different file storage formats
    if isinstance(file_info, list) and len(file_info) > 0:
        file_id = file_info[0]  # Take first file ID from list
    elif isinstance(file_info, tuple):
        file_id = file_info[0]  # Take first from tuple
    else:
        file_id = file_info  # Direct file ID
    
    # Store token with expiry (24 hours)
    expiry_time = datetime.now() + timedelta(hours=24)
    tokens[token] = {
        "user_id": user_id,
        "movie_id": movie_id,
        "quality": quality,
        "file_id": file_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": expiry_time.isoformat(),
        "used": False
    }
    
    save_json(TOKENS_FILE, tokens)
    logger.info(f"Created ad token for user {user_id}, movie {movie_id}, quality {quality}")
    return token

def validate_ad_token(token: str, user_id: int) -> Optional[str]:
    """Validate a token and return the file ID if valid."""
    tokens = load_json(TOKENS_FILE)
    
    if token not in tokens:
        logger.warning(f"Token not found: {token}")
        return None
    
    token_data = tokens[token]
    
    # Check if token is for the correct user
    if token_data["user_id"] != user_id:
        logger.warning(f"Token user mismatch: {token}")
        return None
    
    # Check if token is expired
    expiry_time = datetime.fromisoformat(token_data["expires_at"])
    if datetime.now() > expiry_time:
        logger.warning(f"Token expired: {token}")
        del tokens[token]
        save_json(TOKENS_FILE, tokens)
        return None
    
    # Check if token is already used
    if token_data.get("used", False):
        logger.warning(f"Token already used: {token}")
        return None
    
    # Mark token as used
    tokens[token]["used"] = True
    tokens[token]["used_at"] = datetime.now().isoformat()
    save_json(TOKENS_FILE, tokens)
    
    # Increment download count
    increment_download_count(token_data["movie_id"])
    
    logger.info(f"Token validated successfully: {token}")
    return token_data["file_id"]

def cleanup_expired_tokens():
    """Clean up expired tokens."""
    tokens = load_json(TOKENS_FILE)
    now = datetime.now()
    
    expired_tokens = []
    for token, token_data in tokens.items():
        expiry_time = datetime.fromisoformat(token_data["expires_at"])
        if now > expiry_time:
            expired_tokens.append(token)
    
    for token in expired_tokens:
        del tokens[token]
    
    if expired_tokens:
        save_json(TOKENS_FILE, tokens)
        logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")

# --- Stats Functions ---

# Removed duplicate function - using the correct one above

def get_movies_by_uploader(admin_id: int, limit: int = 30) -> List[dict]:
    """Get movies uploaded by specific admin/owner."""
    movies = load_json(MOVIES_FILE)
    
    admin_movies = [
        movie for movie in movies.values() 
        if movie.get('added_by') == admin_id
    ]
    
    # Sort by date added (newest first)
    admin_movies.sort(key=lambda x: x.get('added_at', ''), reverse=True)
    return admin_movies[:limit]

def get_all_admins() -> List[dict]:
    """Get all admins for stats selection."""
    admins = load_json(ADMINS_FILE)
    return list(admins.values())
