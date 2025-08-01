# Data Directory

This directory contains the JSON storage files for the MovieZone bot.

## Files Structure

- `users.json` - User registration and role data
- `admins.json` - Admin user information
- `movies.json` - Movie database with details and file links
- `channels.json` - Registered channels for posting
- `requests.json` - User movie requests
- `tokens.json` - Temporary download tokens

## Note

The actual JSON files are not included in the repository for privacy and security reasons. They will be created automatically when the bot starts for the first time.

## Initial Setup

The bot will create these files with default empty structures:

```json
{
  "users": {},
  "admins": {},
  "movies": {},
  "channels": {},
  "requests": {},
  "tokens": {}
}
```