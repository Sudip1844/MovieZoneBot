# MovieZone Telegram Bot

## Overview

MovieZone is a Telegram bot application designed for movie discovery, sharing, and request management. The bot allows users to search for movies, browse by categories, request new movies, and download content through an ad-based link system. It features role-based access control with owner, admin, and regular user permissions.

## User Preferences

Preferred communication style: Simple, everyday language.

## Migration Status

**Migration to Replit Completed**: August 3, 2025
**Replit Environment Migration Completed**: August 4, 2025
- Successfully migrated from Replit Agent to standard Replit environment
- Fixed package conflicts between telegram and python-telegram-bot packages
- BOT_TOKEN now hardcoded in config.py for direct access (user preference for public GitHub repo)
- Updated dependency management for Replit compatibility
- Bot application runs successfully with streamlined configuration
- **Fixed Admin/Channel Management**: Resolved conversation handler conflicts with search functionality
  - Modified conversation handlers to properly handle callback query entry points
  - Updated text search handler to not interfere with ongoing conversations
  - Admin and channel addition now works correctly from inline buttons
  - Fixed MarkdownV2 parsing errors in confirmation messages by switching to plain text format
- **Enhanced Dynamic Command Menu System**: Implemented uniform /cancel command approach across all conversations
  - Implemented per-chat command scope management using BotCommandScopeChat
  - **Uniform Approach**: Hamburger menu completely cleared during ALL conversations for consistency
  - /cancel command available ONLY through text input (command box) during conversations
  - Eliminates inconsistent dual-approach between hamburger menu and command box
  - Other commands automatically hide during conversations and restore when conversations end
  - Added global cancel handler to handle /cancel from any conversation state
  - Enhanced command management functions in utils.py for consistent behavior across all handlers
  - Applies to: add movie, request movie, add/remove admin, add/remove channel, show stats, remove movie
  - Fixed text input handling: `/cancel` command now properly cancels conversations instead of being processed as input data
  - Added strict cancel filtering to all text input handlers preventing accidental request submissions
  - Updated conversation messages to instruct users to "Type /cancel to cancel this action"
  - Enhanced cancel filtering in get_movie_request function with multiple cancel variations
  - Fixed issue where "❌ Cancel" text was being processed as movie request instead of canceling conversation

### Recent Updates - August 3, 2025
- **Fixed Movie Posting to Channels**: Enhanced channel link validation system
  - Private channel links (containing + or joinchat) are now properly rejected
  - Added bot access verification before adding channels to database
  - Clear error messages guide users to use proper @username format
  - Bot now tests channel permissions during channel addition process
- **Fixed Admin/Channel Removal System**: Enhanced remove functionality with proper callback handling
  - Added callback query entry points for remove admin and remove channel conversations
  - Fixed "Unhandled callback prefix" errors for admin_remove and channel_remove buttons
  - Modified display to show only short names in removal lists (as requested by user)
  - Remove buttons now properly trigger conversation handlers from inline buttons
- **Enhanced Help Command & Dynamic Menu System**: Improved user interface and command management
  - Removed confusing `/command` format from help messages - now shows feature names with emojis
  - Enhanced dynamic command menu to show only `/cancel` during conversations (hiding all other commands)
  - Commands automatically restore to default (`/start`, `/help`) when conversations end
  - Fixed command scope using proper BotCommandScopeChat for per-chat command management
  - Applies to all conversations: add/remove admin, add/remove channel, add movie, request movie, etc.

### Previous Updates - August 3, 2025
- **Enhanced Welcome System**: Created comprehensive welcome messages matching help command quality
  - Owner welcome: Complete management panel overview with all available powers
  - Admin welcome: Detailed admin capabilities and responsibilities  
  - User welcome: Full movie destination guide with features and download process
- **Fixed CallbackQuery Error**: Updated @restricted decorator to properly handle both messages and callback queries
- **Dynamic Command Menu System**: Fixed and enhanced command menu management
  - When conversations start: /cancel command appears in command menu, other commands hide
  - When conversations end: Command menu reverts to default (/start, /help)
  - Applies to all conversations: movie requests, add movie, admin management, channel management
- **Browse Categories Grid Layout**: Implemented clean 3×10 grid format for category browsing
  - Movies display in 3-column rows (maximum 30 movies per page)
  - No separate text messages - only inline button grid
  - Pagination with Previous/Next buttons for categories with 30+ movies
  - Back to Categories button for easy navigation
  - Long movie titles automatically truncated for clean display
- **Enhanced Admin & Channel Management**: Complete button-based management system integrated into existing commands
  - "👥 Manage Admins" button now includes: ➕ Add New Admin, ➖ Remove an Admin
  - "📢 Manage Channels" button now includes: ➕ Add New Channel, ➖ Remove a Channel  
  - Add Admin: Forward message or send User ID, assign short name for easy reference
  - Remove Admin: Button selection from all existing admins with short names displayed
  - Add Channel: Enter Telegram channel link, assign short name for internal reference
  - Remove Channel: Button selection from all existing channels with short names displayed
  - Short name system allows easy identification and removal by nickname
  - No separate commands needed - everything accessible through existing owner interface
- **Movie Posting Automation**: Added channel selection step after movie preview
  - After movie preview, select multiple channels for automatic posting
  - Toggle channel selection with checkmarks for visual confirmation
  - Movie automatically posts to all selected channels upon confirmation
  - No channels configured = movie saves without posting
- **Professional Message Formatting**: Structured layout with emojis, sections, and clear information hierarchy

### Previous Updates - August 2, 2025
- **Dynamic Command Menu System**: Implemented intelligent command menu management where:
  - Default: Only `/start` and `/help` commands visible in menu
  - During Conversations: `/cancel` automatically appears when user enters any conversation (movie request, add movie, etc.)
  - Auto-Restore: Command menu reverts to default when conversation ends or is cancelled
- **Individual Request Management**: Converted bulk request display to individual message system where:
  - Each movie request appears as separate message with dedicated action buttons
  - Messages automatically delete after admin action (Done/Delete) to prevent confusion
  - Clean admin workflow with no leftover messages or button conflicts
- **Consistent Movie Display Formatting**: Standardized all movie displays across the application:
  - Search results, category browsing, and direct movie views now use identical formatting
  - Unified emoji system: 🎭 Language, 🎪 Genre, 📅 Release Year, ⏰ Runtime, ⭐ IMDb Rating
  - Consistent download button formatting: "Quality || 👉 Click To Download 📥"
  - Added promotional footer to all movie displays
- **Role-Based Command Visibility**: Implemented strict role-based keyboard generation
- **Clean Message Formatting**: Removed all bold formatting for proper Telegram display

## System Architecture

The application follows a modular architecture with clear separation of concerns:

- **Main Application**: `main.py` serves as the entry point, setting up the Telegram bot application with handlers and job scheduling
- **Configuration Management**: Centralized configuration in `config.py` with environment variables and constants
- **Data Layer**: JSON-based file storage system managed through `database.py`
- **Handler Layer**: Modular handlers for different bot functionalities in the `handlers/` directory
- **Utility Functions**: Common functions and decorators in `utils.py`

## Key Components

### 1. Bot Core (`main.py`)
- Telegram bot application setup using python-telegram-bot library
- Handler registration for commands, messages, and callbacks
- Auto-deletion job scheduling for message cleanup
- Chat member update handling for channel management

### 2. Configuration (`config.py`)
- Bot token and username configuration
- Owner ID and admin settings
- Category and language definitions for movies
- Ad page URL configuration
- Message templates for movie posts
- Conversation timeout settings

### 3. Database Layer (`database.py`)
- JSON file-based storage system
- Separate files for users, admins, movies, channels, requests, and tokens
- CRUD operations for all entities
- Data initialization and file management

### 4. Handler Modules
- **Start Handler**: Welcome messages, user registration, deep link processing
- **Movie Handlers**: Search functionality, category browsing, movie details
- **Conversation Handlers**: Multi-step conversations for adding movies
- **Callback Handler**: Inline keyboard button interactions
- **Owner Handlers**: Admin management, channel management (owner-only features)

### 5. Utility Functions (`utils.py`)
- Role-based access control decorator (`@restricted`)
- Keyboard generation functions
- Movie post formatting
- Ad link generation for monetization

## Data Flow

### User Registration Flow
1. User sends `/start` command
2. Bot adds user to database if not exists
3. Bot sends welcome message with role-appropriate keyboard

### Movie Search Flow
1. User requests movie search
2. Bot prompts for search query
3. Database searches movies by title/description
4. Bot returns results with download options

### Movie Request Flow
1. User submits movie request
2. Request stored in database with pending status
3. Admins/owner can view and manage requests
4. Users get notified when requests are fulfilled

### File Download Flow
1. User clicks download button
2. Bot generates secure token and ad page link
3. User visits ad page and gets redirected back with token
4. Bot validates token and sends file

## External Dependencies

### Core Libraries
- `python-telegram-bot`: Telegram Bot API wrapper
- `json`: Built-in JSON handling for data persistence
- `os`: Environment variable and file system operations
- `logging`: Application logging and debugging
- `hashlib`: Token generation and security
- `datetime`: Time-based operations and scheduling

### Optional Integrations
- **Supabase**: Database configuration present but not currently implemented
- **GitHub Pages**: Ad page hosting for monetization system

## Deployment Strategy

### File-Based Storage
- Uses JSON files in `data/` directory for persistence
- Suitable for small to medium scale deployments
- Easy backup and migration capabilities
- No external database dependencies required

### Environment Configuration
- Bot token configurable via environment variables
- Fallback to hardcoded values for development
- Owner ID and other settings in configuration file

### Modular Design
- Handler-based architecture allows easy feature addition/removal
- Clear separation between business logic and Telegram API interactions
- Conversation handlers for complex user interactions

### Auto-Cleanup
- Scheduled message deletion after 48 hours
- Token expiration and cleanup mechanisms
- Request status management and cleanup

### Role-Based Security
- Owner: Full access to all features including admin management
- Admin: Movie management and request handling
- User: Basic search, browse, and request functionality
- Decorator-based access control throughout the application

The application is designed to be easily deployable on platforms like Replit, with minimal external dependencies and a self-contained data storage system.