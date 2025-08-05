# MovieZone Telegram Bot

## Overview

MovieZone is a Telegram bot designed for movie discovery, sharing, and request management. It enables users to search for movies, browse by categories, request new content, and download movies via an ad-based link system. The bot incorporates a robust role-based access control system with distinct permissions for owners, administrators, and regular users. The project aims to provide a streamlined, user-friendly experience for movie enthusiasts while offering monetization opportunities through integrated advertising.

## User Preferences

Preferred communication style: Simple, everyday language.
All bot commands are available only through reply keyboard buttons.
The hamburger menu is completely removed; during conversations, it is empty.
The "❌ Cancel" button appears in the reply keyboard alongside other commands during conversations.
The `/cancel` command is available via command box input.
The bot should not make changes to the `BOT_TOKEN` in `config.py`.
Updated category system with specific emoji icons and two special categories:
- "All 🌐" for alphabet-based movie filtering (user types letter, bot shows movies starting with that letter)
- "Hentai 💦" available only in admin movie addition interface, not in user browsing

## System Architecture

The application adopts a modular architecture, promoting separation of concerns and maintainability.

### UI/UX Decisions
- **Interaction Model**: Exclusively uses reply keyboard buttons for all user interactions, eliminating the hamburger menu for a cleaner interface.
- **Cancel Mechanism**: A prominent "❌ Cancel" button is integrated into reply keyboards during conversations for consistent cancellation. The `/cancel` command is also supported via text input.
- **Dynamic Command Menu**: The command menu (`/start`, `/help`) dynamically hides during ongoing conversations, showing only `/cancel`, and restores upon conversation completion.
- **Category Browsing**: Movies within categories are displayed in a 3x10 grid format with pagination and easy navigation back to main categories.
- **Message Formatting**: Professional, structured layouts with emojis and clear information hierarchy are used consistently across all movie displays, search results, and welcome messages. All bold formatting is removed.
- **Admin/Channel Management**: Features like managing admins and channels are integrated into existing commands and accessed via dedicated buttons (e.g., "Manage Admins" includes "Add New Admin", "Remove an Admin"). Short names are used for easy identification in removal lists.

### Technical Implementations
- **Core Framework**: Built on the `python-telegram-bot` library.
- **Configuration**: Centralized in `config.py` for environment variables, constants, and message templates.
- **Data Storage**: Uses a JSON-based file system (`database.py`) for users, admins, movies, channels, requests, and tokens, ensuring easy backup and migration without external database dependencies.
- **Handler Modules**: Organized handlers for specific functionalities (Start, Movie Search, Conversation, Callback, Owner actions) to ensure modularity.
- **Utility Functions**: `utils.py` provides common functionalities like role-based access control (`@restricted` decorator), keyboard generation, movie post formatting, and ad link generation.
- **Role-Based Access Control**: Strict permissions (Owner, Admin, User) are enforced via decorators and dynamic keyboard generation.
- **Command Management**: Per-chat command scope management is used to control command visibility dynamically.
- **Conversation Handling**: Multi-step conversations are managed with robust cancellation logic.
- **Ad Integration**: Ad links are generated with secure tokens; users are redirected through an ad page before accessing content.

### Feature Specifications
- **User Registration**: Automatic registration on `/start` command with role-appropriate welcome messages.
- **Movie Search & Browse**: Users can search by query or browse categories with detailed movie information and download options.
- **Movie Request System**: Users can submit movie requests, which admins can manage. Users are notified upon fulfillment.
- **Admin & Owner Features**: Comprehensive management of users, movies, channels, and requests.
- **Movie Management**: Owner role includes full movie lifecycle management with "➕ Add Movie", "🗑️ Remove Movie", and "📊 Show Stats" functionality accessible via reply keyboard buttons.
- **Skip Functionality**: Added skip buttons to movie addition process for release year, runtime, IMDb rating, categories, and languages to save time for admins/owners. Skip options use sensible defaults (N/A for metadata, General for category, English for language).
- **Dynamic Command Menu**: Contextual command menu adjustments based on conversation state.
- **Automated Posting**: After preview, movies can be posted to multiple selected channels with validation checks.
- **Message Cleanup**: Scheduled auto-deletion of messages and token expiration for a clean system.

## External Dependencies

- `python-telegram-bot`: Primary library for Telegram Bot API interaction.
- `json`: Used for file-based data persistence.
- `os`: For environment variable access and file system operations.
- `logging`: For application logging and debugging.
- `hashlib`: Used for token generation and security features.
- `datetime`: For time-based operations and scheduling.
- **GitHub Pages**: Potentially used for hosting the ad page (monetization system).