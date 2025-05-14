import os
import discord
from discord.ext import commands, tasks
import datetime
import asyncio
import logging
from dotenv import load_dotenv

from database import initialize_database, close_all_connections
from data_access import (
    set_birthday, set_birth_year, toggle_user_setting, get_user_birthday,
    get_birthdays_for_date, set_server_setting, get_server_setting, clean_up_user_data,
    clear_birthday
)
from utils import (
    parse_birthday, validate_year, get_current_date_mmdd, 
    get_guild_timezone, calculate_age, is_admin
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('birthday_bot')

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
MASTER_KEY_ID = int(os.getenv('MASTER_KEY_ID', 0))

# Setup Discord bot with required intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Private warning message for setting birthday/birth year
PRIVACY_WARNING = """
⚠️ **Privacy Warning**:
You are about to share personal information with this bot. This data is stored securely in a database but remember:
- Sharing your birthday can potentially reveal personal information
- Server birthday announcements can be seen by all server members
- You can disable announcements at any time using `!toggleannounce` and `!toggledms`

Your data will only be used for birthday announcements as configured by your preferences.
"""

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    initialize_database()
    
    # Start birthday check task
    check_birthdays.start()
    logger.info('Bot is ready and birthday checking is running')

@bot.event
async def on_guild_join(guild):
    """Called when the bot joins a guild"""
    logger.info(f'Joined guild: {guild.name} ({guild.id})')
    
@bot.event
async def on_guild_remove(guild):
    """Called when the bot is removed from a guild"""
    logger.info(f'Left guild: {guild.name} ({guild.id})')

@bot.event
async def on_member_remove(member):
    """Called when a member leaves a guild"""
    # Optional: Clean up user data when they leave a server
    # Uncomment to enable this feature
    # clean_up_user_data(member.id, member.guild.id)
    pass

@bot.command(name="setbirthday")
async def set_birthday_cmd(ctx, birthday_str: str = None):
    """Set your birthday (MMDD or DDMM format)"""
    if birthday_str is None:
        await ctx.send("Please provide your birthday in MMDD or DDMM format. Example: `!setbirthday 1225` for December 25")
        return
    
    # Get command channel setting
    command_channel_id = get_server_setting(ctx.guild.id, "command_channel")
    
    # Check if command is allowed in this channel
    if command_channel_id and ctx.channel.id != int(command_channel_id) and not ctx.author.guild_permissions.administrator:
        command_channel = ctx.guild.get_channel(int(command_channel_id))
        if command_channel:
            await ctx.send(f"Please use {command_channel.mention} for birthday commands.")
            return
    
    # Parse and validate birthday
    parsed_birthday = parse_birthday(birthday_str)
    if not parsed_birthday:
        await ctx.send("Invalid birthday format. Please use MMDD or DDMM format (e.g., 1225 for December 25).")
        return
    
    # Send privacy warning - handle users with DMs disabled
    try:
        await ctx.author.send(PRIVACY_WARNING)
    except discord.errors.Forbidden:
        # User has DMs disabled, send the message in the channel instead
        await ctx.send(f"⚠️ **{ctx.author.mention}**: I couldn't send you a privacy warning via DM because you have DMs disabled.\n\nPlease note that by setting your birthday, you're sharing personal information. You can disable announcements at any time using `!toggleannounce` and `!toggledms`.")
    
    # Set the birthday in the database
    if set_birthday(ctx.author.id, ctx.guild.id, parsed_birthday):
        month, day = parsed_birthday[:2], parsed_birthday[2:]
        await ctx.send(f"Your birthday has been set to {month}/{day}. You can use `!toggleannounce` to disable server announcements or `!toggledms` to disable DM messages.")
    else:
        await ctx.send("There was an error setting your birthday. Please try again later.")

@bot.command(name="clearbirthday")
async def clear_birthday_cmd(ctx):
    """Clear your birthday"""
    # Get command channel setting
    command_channel_id = get_server_setting(ctx.guild.id, "command_channel")
    
    # Check if command is allowed in this channel
    if command_channel_id and ctx.channel.id != int(command_channel_id) and not ctx.author.guild_permissions.administrator:
        command_channel = ctx.guild.get_channel(int(command_channel_id))
        if command_channel:
            await ctx.send(f"Please use {command_channel.mention} for birthday commands.")
            return
    
    # Check if user has a birthday set
    birthday_info = get_user_birthday(ctx.author.id, ctx.guild.id)
    if not birthday_info:
        await ctx.send("You don't have a birthday set in this server.")
        return
    
    # Clear the birthday from the database
    if clear_birthday(ctx.author.id, ctx.guild.id):
        await ctx.send("Your birthday has been cleared from this server.")
    else:
        await ctx.send("There was an error clearing your birthday. Please try again later.")

@bot.command(name="setbirthyear")
async def set_birth_year_cmd(ctx, year_str: str = None):
    """Opt-in to add your birth year"""
    if year_str is None:
        await ctx.send("Please provide your birth year. Example: `!setbirthyear 1995`")
        return
    
    # Validate year
    year = validate_year(year_str)
    if not year:
        await ctx.send("Invalid birth year. Please provide a valid year.")
        return
    
    # Check if user has registered a birthday
    birthday_info = get_user_birthday(ctx.author.id, ctx.guild.id)
    if not birthday_info:
        await ctx.send("Please set your birthday first using `!setbirthday`.")
        return
    
    # Send privacy warning
    try:
        await ctx.author.send(PRIVACY_WARNING + "\nAdding your birth year allows the bot to calculate your age. Use `!toggleshareage` to control whether your age is shared in birthday announcements.")
    except discord.errors.Forbidden:
        # User has DMs disabled, send the message in the channel instead
        await ctx.send(f"⚠️ **{ctx.author.mention}**: I couldn't send you a privacy warning via DM because you have DMs disabled.\n\nPlease note that adding your birth year allows the bot to calculate your age. You can control whether your age is shared using `!toggleshareage`.")
    
    # Set the birth year in the database
    if set_birth_year(ctx.author.id, ctx.guild.id, year):
        await ctx.send(f"Your birth year has been set to {year}. You can use `!toggleshareage` to control whether your age is shown in birthday announcements.")
    else:
        await ctx.send("There was an error setting your birth year. Please try again later.")

@bot.command(name="toggledms")
async def toggle_dms_cmd(ctx):
    """Toggle whether you receive birthday DMs"""
    result = toggle_user_setting(ctx.author.id, ctx.guild.id, "receive_dms")
    if result is not None:
        status = "enabled" if result == 1 else "disabled"
        await ctx.send(f"Birthday DMs are now {status}.")
    else:
        await ctx.send("Please set your birthday first using `!setbirthday`.")

@bot.command(name="toggleannounce")
async def toggle_announce_cmd(ctx):
    """Toggle whether your birthday is announced in servers"""
    result = toggle_user_setting(ctx.author.id, ctx.guild.id, "announce_in_servers")
    if result is not None:
        status = "enabled" if result == 1 else "disabled"
        await ctx.send(f"Server birthday announcements are now {status}.")
    else:
        await ctx.send("Please set your birthday first using `!setbirthday`.")

@bot.command(name="toggleshareage")
async def toggle_share_age_cmd(ctx):
    """Toggle whether your age is shared in birthday announcements"""
    # Check if user has a birth year set
    birthday_info = get_user_birthday(ctx.author.id, ctx.guild.id)
    if not birthday_info or not birthday_info[1]:  # Index 1 is birth_year
        await ctx.send("Please set your birth year first using `!setbirthyear`.")
        return
    
    result = toggle_user_setting(ctx.author.id, ctx.guild.id, "share_age")
    if result is not None:
        status = "enabled" if result == 1 else "disabled"
        await ctx.send(f"Age sharing in birthday announcements is now {status}.")
    else:
        await ctx.send("There was an error toggling age sharing. Please try again later.")

# Admin commands
@bot.command(name="setannouncechannel")
async def set_announce_channel_cmd(ctx, channel: discord.TextChannel = None):
    """Set the channel for birthday announcements (Admin only)"""
    if not is_admin(ctx.author) and ctx.author.id != MASTER_KEY_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    if not channel:
        await ctx.send("Please mention a channel. Example: `!setannouncechannel #birthdays`")
        return
    
    if set_server_setting(ctx.guild.id, "announce_channel", str(channel.id)):
        await ctx.send(f"Birthday announcements will now be sent to {channel.mention}.")
    else:
        await ctx.send("There was an error setting the announcement channel. Please try again later.")

@bot.command(name="clearuserbirthday")
async def clear_user_birthday_cmd(ctx, user: discord.Member = None):
    """Clear a user's birthday (Admin only)"""
    if not is_admin(ctx.author) and ctx.author.id != MASTER_KEY_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    if not user:
        await ctx.send("Please mention a user. Example: `!clearuserbirthday @username`")
        return
    
    # Check if user has a birthday set
    birthday_info = get_user_birthday(user.id, ctx.guild.id)
    if not birthday_info:
        await ctx.send(f"{user.display_name} doesn't have a birthday set in this server.")
        return
    
    # Clear the birthday from the database
    if clear_birthday(user.id, ctx.guild.id):
        await ctx.send(f"{user.display_name}'s birthday has been cleared from this server.")
    else:
        await ctx.send(f"There was an error clearing {user.display_name}'s birthday. Please try again later.")

@bot.command(name="setcommandchannel")
async def set_command_channel_cmd(ctx, channel: discord.TextChannel = None):
    """Set the channel for processing birthday commands (Admin only)"""
    if not is_admin(ctx.author) and ctx.author.id != MASTER_KEY_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    if not channel:
        await ctx.send("Please mention a channel. Example: `!setcommandchannel #commands`")
        return
    
    if set_server_setting(ctx.guild.id, "command_channel", str(channel.id)):
        await ctx.send(f"Birthday commands will now only be processed in {channel.mention}.")
    else:
        await ctx.send("There was an error setting the command channel. Please try again later.")

@bot.command(name="toggleeveryone")
async def toggle_everyone_cmd(ctx):
    """Toggle whether @everyone is mentioned in birthday announcements (Admin only)"""
    if not is_admin(ctx.author) and ctx.author.id != MASTER_KEY_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    # Get current setting or default to 0 (disabled)
    current_setting = get_server_setting(ctx.guild.id, "mention_everyone")
    new_setting = "0" if current_setting == "1" else "1"
    
    if set_server_setting(ctx.guild.id, "mention_everyone", new_setting):
        status = "enabled" if new_setting == "1" else "disabled"
        await ctx.send(f"@everyone mentions in birthday announcements are now {status}.")
    else:
        await ctx.send("There was an error toggling @everyone mentions. Please try again later.")

@bot.command(name="settimezone")
async def set_timezone_cmd(ctx, timezone: str = None):
    """Set the timezone for the server (Admin only)"""
    if not is_admin(ctx.author) and ctx.author.id != MASTER_KEY_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    if not timezone:
        await ctx.send("Please provide a timezone. Example: `!settimezone America/New_York`")
        return
    
    try:
        import pytz
        tz = pytz.timezone(timezone)
        if set_server_setting(ctx.guild.id, "timezone", timezone):
            await ctx.send(f"Server timezone has been set to {timezone}.")
        else:
            await ctx.send("There was an error setting the timezone. Please try again later.")
    except ImportError:
        await ctx.send("Timezone functionality is not available (pytz module not installed).")
    except Exception:
        await ctx.send("Invalid timezone. Please use a valid timezone identifier (e.g., 'America/New_York').")

@bot.command(name="help")
async def help_cmd(ctx):
    """Display help information"""
    help_embed = discord.Embed(
        title="Birthday Bot Help",
        description="Here are the commands you can use:",
        color=discord.Color.blue()
    )
    
    help_embed.add_field(
        name="User Commands",
        value="""
        `!setbirthday MMDD` - Set your birthday (MMDD or DDMM format)
        `!clearbirthday` - Clear your birthday from this server
        `!setbirthyear YYYY` - Add your birth year (optional)
        `!toggledms` - Toggle birthday DMs
        `!toggleannounce` - Toggle server announcements
        `!toggleshareage` - Toggle age sharing (requires birth year)
        """,
        inline=False
    )
    
    help_embed.add_field(
        name="Administrative Commands",
        value="Use `!adminhelp` to see administrative commands.",
        inline=False
    )
    
    help_embed.set_footer(text="Your privacy matters! Bot stores only the information you provide.")
    
    await ctx.send(embed=help_embed)

@bot.command(name="adminhelp")
async def admin_help_cmd(ctx):
    """Display admin help information"""
    if not is_admin(ctx.author) and ctx.author.id != MASTER_KEY_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    admin_embed = discord.Embed(
        title="Birthday Bot Admin Help",
        description="Here are the administrative commands:",
        color=discord.Color.gold()
    )
    
    admin_embed.add_field(
        name="Admin Commands",
        value="""
        `!setannouncechannel #channel` - Set channel for birthday announcements
        `!setcommandchannel #channel` - Set channel for birthday commands
        `!toggleeveryone` - Toggle @everyone mentions in announcements
        `!settimezone timezone` - Set server timezone (e.g., 'America/New_York')
        `!clearuserbirthday @user` - Clear a specific user's birthday
        """,
        inline=False
    )
    
    # Add special section for master user if the user is the master
    if ctx.author.id == MASTER_KEY_ID:
        admin_embed.add_field(
            name="Bot Owner Commands",
            value="""
            `!forceannounce @user` - Force birthday announcements for a user
            """,
            inline=False
        )
    
    admin_embed.set_footer(text="These commands can only be used by administrators or users with the 'birthday' role.")
    
    await ctx.send(embed=admin_embed)

async def send_birthday_dm(user, birth_year=None, share_age=0):
    """Send birthday DM to a user"""
    try:
        age_text = ""
        if birth_year and share_age == 1:
            age = calculate_age(birth_year)
            age_text = f"\nYou're turning {age} today! 🎂"
            
        await user.send(f"Happy Birthday, {user.mention}! 🎉🎂🎈{age_text}")
        return True
    except Exception as e:
        logger.error(f"Error sending DM to user {user.id}: {e}")
        return False

async def send_server_announcement(guild, member, channel_id, birth_year=None, share_age=0, mention_everyone=False):
    """Send birthday announcement to a server channel"""
    try:
        # Get the announcement channel
        channel = guild.get_channel(int(channel_id))
        if not channel:
            return False
        
        # Prepare announcement message
        age_text = ""
        if birth_year and share_age == 1:
            age = calculate_age(birth_year)
            age_text = f" They're turning {age} today!"
        
        message = f"🎉 Today is {member.mention}'s birthday!{age_text} Wish them a happy birthday! 🎂🎈"
        
        # Send announcement
        await channel.send(message, allowed_mentions=discord.AllowedMentions(everyone=mention_everyone))
        return True
    except Exception as e:
        logger.error(f"Error sending announcement in guild {guild.id}: {e}")
        return False

@bot.command(name="forceannounce")
async def force_announce_cmd(ctx, user: discord.Member = None):
    """Force a birthday announcement for a user (Master only)"""
    # Check if the command is used by the master user
    if ctx.author.id != MASTER_KEY_ID:
        await ctx.send("This command is restricted to the bot owner only.")
        return
    
    if not user:
        await ctx.send("Please mention a user. Example: `!forceannounce @username`")
        return
    
    # Get user's birthday info
    birthday_info = get_user_birthday(user.id, ctx.guild.id)
    
    # If no birthday info, attempt to create one for this announcement
    if not birthday_info:
        # Create a temporary record
        today = datetime.datetime.now().strftime("%m%d")
        if not set_birthday(user.id, ctx.guild.id, today):
            await ctx.send(f"Failed to create temporary birthday record for {user.display_name}")
            return
        
        # Get the newly created record
        birthday_info = get_user_birthday(user.id, ctx.guild.id)
        if not birthday_info:
            await ctx.send(f"Failed to retrieve birthday info for {user.display_name}")
            return
    
    # Extract birthday info
    _, birth_year, announce_in_servers, receive_dms, share_age = birthday_info
    
    results = []
    
    # Force DM if user accepts DMs
    if receive_dms == 1:
        dm_sent = await send_birthday_dm(user, birth_year, share_age)
        results.append(f"Birthday DM: {'✅ Sent' if dm_sent else '❌ Failed'}")
    else:
        results.append("Birthday DM: ⏭️ Skipped (user setting)")
    
    # Force server announcement if enabled
    if announce_in_servers == 1:
        # Check if announce channel is set
        announce_channel_id = get_server_setting(ctx.guild.id, "announce_channel")
        if announce_channel_id:
            # Determine if @everyone should be mentioned
            mention_everyone = get_server_setting(ctx.guild.id, "mention_everyone") == "1"
            
            announcement_sent = await send_server_announcement(
                ctx.guild, user, announce_channel_id, birth_year, share_age, mention_everyone
            )
            results.append(f"Server announcement: {'✅ Sent' if announcement_sent else '❌ Failed'}")
        else:
            results.append("Server announcement: ❌ Failed (no announcement channel set)")
    else:
        results.append("Server announcement: ⏭️ Skipped (user setting)")
    
    # Send summary
    summary = "\n".join(results)
    await ctx.send(f"Force announcement results for {user.display_name}:\n{summary}")

@tasks.loop(hours=1)
async def check_birthdays():
    """Background task to check for birthdays"""
    logger.info("Checking for birthdays...")
    
    try:
        # Check for UTC birthdays (for DMs)
        utc_date = get_current_date_mmdd()
        birthdays = get_birthdays_for_date(utc_date)
        
        for user_id, guild_id, birth_year, announce_in_servers, receive_dms, share_age in birthdays:
            # Send DM if enabled
            if receive_dms == 1:
                try:
                    user = await bot.fetch_user(user_id)
                    if user:
                        await send_birthday_dm(user, birth_year, share_age)
                except Exception as e:
                    logger.error(f"Error sending DM to user {user_id}: {e}")
        
        # Check for server-specific birthdays
        for guild in bot.guilds:
            # Get guild timezone
            guild_tz = get_guild_timezone(guild.id)
            guild_date = get_current_date_mmdd(guild_tz)
            
            # Skip if it's the same as UTC (already processed)
            if guild_date == utc_date:
                continue
            
            # Check for birthdays in this timezone
            birthdays = get_birthdays_for_date(guild_date)
            
            for user_id, guild_id, birth_year, announce_in_servers, receive_dms, share_age in birthdays:
                # Make sure user is in this guild and has server announcements enabled
                if guild_id != guild.id or announce_in_servers != 1:
                    continue
                
                # Check if announce channel is set
                announce_channel_id = get_server_setting(guild.id, "announce_channel")
                if not announce_channel_id:
                    continue
                
                try:
                    # Get the member
                    member = guild.get_member(user_id)
                    if not member:
                        continue
                    
                    # Determine if @everyone should be mentioned
                    mention_everyone = get_server_setting(guild.id, "mention_everyone") == "1"
                    
                    await send_server_announcement(
                        guild, member, announce_channel_id, birth_year, share_age, mention_everyone
                    )
                except Exception as e:
                    logger.error(f"Error sending announcement in guild {guild.id}: {e}")
    
    except Exception as e:
        logger.error(f"Error in birthday check task: {e}")

@check_birthdays.before_loop
async def before_check_birthdays():
    """Wait until the bot is ready before starting the task"""
    await bot.wait_until_ready()

if __name__ == '__main__':
    try:
        bot.run(BOT_TOKEN)
    except Exception as e:
        logger.error(f"Error starting the bot: {e}")
    finally:
        # Cleanup
        close_all_connections()
