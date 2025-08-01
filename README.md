# MovieZone Telegram Bot

A comprehensive Telegram movie bot with role-based access control featuring movie upload, management, search, and ad-based download system.

## Features

### User Features
- **🔍 Movie Search**: Find movies by name
- **📂 Category Browse**: Browse movies by genre
- **🙏 Movie Request**: Request new movies from admins
- **💾 Download System**: Ad-based download with quality options

### Admin Features
- **➕ Add Movies**: Upload new movies with thumbnails and details
- **📊 Request Management**: View and handle user movie requests
- **🗑️ Remove Movies**: Delete movies from database
- **📈 Statistics**: View movie and user statistics

### Owner Features
- **👥 Admin Management**: Add or remove admin users
- **📢 Channel Management**: Manage posting channels
- **🛡️ Full Access**: Complete control over bot features

## Tech Stack

- **Framework**: Python Telegram Bot (PTB) v20.7
- **Storage**: JSON-based file storage
- **Architecture**: Modular handler-based system
- **Access Control**: Role-based permissions (Owner/Admin/User)

## Project Structure

```
MovieZone-Bot/
├── main.py                 # Entry point and bot setup
├── config.py              # Configuration and constants
├── database.py            # JSON storage management
├── utils.py               # Utility functions and decorators
├── handlers/              # Handler modules
│   ├── start_handler.py   # Start command and help
│   ├── movie_handlers.py  # Movie operations
│   ├── conversation_handlers.py  # Multi-step conversations
│   ├── callback_handler.py       # Button interactions
│   └── owner_handlers.py  # Owner-only features
└── data/                  # JSON storage files
    ├── users.json
    ├── admins.json
    ├── movies.json
    ├── channels.json
    ├── requests.json
    └── tokens.json
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- GitHub Pages for ad redirect (optional)

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Sudip1844/moviezone-bot.git
cd moviezone-bot

# Install dependencies
pip install python-telegram-bot==20.7

# Run the bot
python main.py
```

### 3. Configuration

Edit `config.py` to set:
- `BOT_TOKEN`: Your Telegram bot token
- `BOT_USERNAME`: Your bot username
- `OWNER_ID`: Your Telegram user ID
- `AD_PAGE_URL`: URL for ad redirect page

### 4. Bot Commands

#### User Commands
- `/start` - Start the bot and register
- `/help` - Show help message
- `🔍 Search Movies` - Search for movies
- `📂 Browse Categories` - Browse by genre
- `🙏 Request Movie` - Request new movies

#### Admin Commands (Additional)
- `➕ Add Movie` - Add new movies
- `📊 Show Requests` - Manage user requests

#### Owner Commands (Additional)
- `👥 Manage Admins` - Add/remove admins
- `📢 Manage Channels` - Manage posting channels

## Features in Detail

### Role-Based Access Control
- **Owner**: Full access to all features
- **Admin**: Movie management and user requests
- **User**: Search, browse, and request features

### Movie Management
- Upload movies with thumbnails
- Multiple quality options (480p, 720p, 1080p)
- Series support with episode handling
- Category and language organization

### Download System
- Ad-based monetization
- Secure token generation
- Quality selection
- Direct file delivery

### Database Structure
- JSON-based storage for simplicity
- Separate files for different data types
- Easy backup and migration
- No external database dependencies

## Deployment

### Replit Deployment
1. Import project to Replit
2. Set environment variables
3. Configure bot token
4. Run the project

### VPS Deployment
1. Clone repository
2. Install dependencies
3. Configure systemd service
4. Set up reverse proxy (optional)

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

This project is open source and available under the MIT License.

## Support

For support and updates:
- **Telegram**: [@moviezone969](https://t.me/moviezone969)
- **GitHub Issues**: Report bugs and feature requests

## Bot Demo

Try the bot: [@YourBotUsername](https://t.me/YourBotUsername)

---

**Note**: This bot is designed for educational purposes. Ensure compliance with copyright laws and Telegram's terms of service when using for movie distribution.# MovieZoneBot
