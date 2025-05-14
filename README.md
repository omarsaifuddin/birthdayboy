# Birthday Bot

A Discord bot developed using discord.py that stores and announces user birthdays across Discord servers and via direct messages (DMs).

## Working Example
To use BirthdayBoy in your own server, refer to the invite link below.

https://discord.com/oauth2/authorize?client_id=410957284466753537

## Features

- **Birthday Registration**: Users can register their birthday via `!setbirthday` command
- **Birthday Announcements**: Automatic announcements in servers and via DMs
- **Privacy Controls**: Users can toggle announcements, DMs, and age sharing
- **Administrative Controls**: Server admins can configure announcement channels, command channels, and more

## Self-Hosting Requirements

- Python 3.8+
- PostgreSQL database
- Discord bot token
- Docker (optional)

## Installation

### Standard Installation

1. Clone this repository
2. Install required packages:
```
pip install -r requirements.txt
```
3. Create PostgreSQL databases:
```sql
CREATE DATABASE birthday_bot_dev;
CREATE DATABASE birthday_bot_test;
CREATE DATABASE birthday_bot_prod;
```
4. Copy `env.example` to `.env` and configure your environment variables:
```
cp env.example .env
```
5. Edit `.env` file with your Discord bot token and PostgreSQL credentials
6. Run the bot:
```
python main.py
```

### Docker Installation

1. Clone this repository
2. Copy `env.example` to `.env` and configure your environment variables:
```
cp env.example .env
```
3. Build and start the containers:
```
docker-compose up -d
```

The Docker setup includes:
- PostgreSQL container with three separate databases (dev, test, prod)
- A database initialization service that ensures all databases are created
- Python application container for the bot

The bot will start automatically after the database is ready and initialized with all the required databases.

## Configuration

Before running the bot, make sure to:

1. Create a Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Enable the required intents (Message Content, Server Members)
3. Add the bot to your server with proper permissions

## Commands

### User Commands
- `!setbirthday MMDD` - Set your birthday (MMDD or DDMM format)
- `!setbirthyear YYYY` - Add your birth year (optional)
- `!toggledms` - Toggle birthday DMs
- `!toggleannounce` - Toggle server announcements
- `!toggleshareage` - Toggle age sharing (requires birth year)
- `!help` - Display user commands

### Administrative Commands
- `!setannouncechannel #channel` - Set channel for birthday announcements
- `!setcommandchannel #channel` - Set channel for birthday commands
- `!toggleeveryone` - Toggle @everyone mentions in announcements
- `!settimezone timezone` - Set server timezone
- `!adminhelp` - Display admin commands

## Development

- The bot uses PostgreSQL to store user data and server settings
- Separate databases are used for development, testing, and production environments
- Testing can be done with Python's testing framework

## Security and Privacy

- Users are warned when sharing personal information
- Birth year and age sharing are opt-in only
- User data is stored securely in a PostgreSQL database

## License

This project is licensed under the MIT License. 
