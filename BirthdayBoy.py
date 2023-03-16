#BirthdayBoX
import discord
from discord.ext import commands, tasks
import json
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')
config_filename = "config.json"
birthdays_filename = "birthdays.json"
#birthdays.json and config.json can be otherwise completely empty *.json files, only containing {}

def load_bot_token():
    with open("credentials.json", "r") as f:
        credentials = json.load(f)
    return credentials["bot_token"]
'''credentials.json should look like this:
{
    "bot_token": "YOUR_BOT_TOKEN_HERE"
}
'''
def load_birthdays():
    with open(birthdays_filename, "r") as f:
        return json.load(f)

def save_birthdays(birthdays):
    with open(birthdays_filename, "w") as f:
        json.dump(birthdays, f)

def load_config():
    with open(config_filename, "r") as f:
        return json.load(f)

def save_config(config):
    with open(config_filename, "w") as f:
        json.dump(config, f)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    announce_birthdays.start()

@bot.event

async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower() == "so wavy":
        await message.channel.send("Fuck New York")

    await bot.process_commands(message)

@bot.command()

#When called, sets a role to the "role_id" config.
async def setrole(ctx, role: discord.Role):
    role_id = role.id   
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send("You must be an administrator to set the role ping.")
        return
    guild_id = str(ctx.guild.id)
    config = load_config()
    #Adding role mentions
    config[guild_id]["role_id"] = role_id
    config[guild_id]["role_mention"] = True
    save_config(config)

#If the role_id entered is empty, it resets "role_mention" boolean to False
@setrole.error
async def setrole_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('Invalid role! Please mention a valid role.')

    elif isinstance(error, commands.MissingRequiredArgument):
        guild_id = str(ctx.guild.id)
        config = load_config()
        config[guild_id]["role_mention"] = False
        await ctx.send('Role mention removed from message')

@bot.command()
async def setchannel(ctx, channel: discord.TextChannel):
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send("You must be an administrator to set the birthday channel.")
        return

    guild_id = str(ctx.guild.id)
    config = load_config()

    # Ensure the guild_id key exists and is a dictionary
    if guild_id not in config or not isinstance(config[guild_id], dict):
        config[guild_id] = {}

    config[guild_id]["channel_id"] = channel.id

    
    await ctx.send(f"Birthday channel set to {channel.mention}")

#await ctx.author.send("Your birth year has been stripped from our database. Please be careful with who you share your information with online.")
@bot.command()
async def birthday(ctx, date_str: str):
    user_id = str(ctx.author.id)
    birthdays = load_birthdays()

    if len(date_str) == 8:
        date_str = date_str[:-4]

    try:
        date = datetime.datetime.strptime(date_str, "%m%d").date()
    except ValueError:
        await ctx.send("Invalid date format. Please use MMDD or DDMM.")
        return

    age = datetime.datetime.now().year - int(date_str[-4:])
    if age < 18:
        await ctx.author.send("Your birth year has been stripped from our database. Please be careful with who you share your information with online.")

    birthdays[user_id] = date.strftime("%m%d")
    save_birthdays(birthdays)

    if date.strftime("%m%d") == datetime.datetime.now().strftime("%m%d"):
        guild_id = str(ctx.guild.id)
        config = load_config()
        guild_config = config.get(guild_id)
        if not isinstance(guild_config, dict):
            guild_config = {}
        
        channel_id = guild_config.get("channel_id")
        if channel_id:
            channel = bot.get_channel(channel_id)
        else:
            channel = discord.utils.get(ctx.guild.text_channels, name='birthdays')


            channel = discord.utils.get(ctx.guild.text_channels, name='birthdays')
        
        role_mention = guild_config.get("role_mention")
        if channel:
            everyone_mention = guild_config.get("everyone_mention", False)

            message = "It's " + ctx.author.mention + "'s birthday! Happy Birthday " + ctx.author.mention + "!"
            
                #Checks if role_mention = True
            if role_mention:
                #Pulls role_id from JSON
                role_id = guild_config.get("role_id")
                #Checks if it's not empty - this should temporarily resolve if the config is empty
                if role_id is not None:

                    message = ", " + message
                    message = f'<@&{role_id}>, {message}'

            if everyone_mention:
                message = "@everyone, " + message
            
            await channel.send(message)

    await ctx.send("Birthday saved.")


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of available commands", color=0x42f56c)
    embed.add_field(name=f"{bot.command_prefix}setchannel #channel", value="Set the channel where birthday announcements are sent. \n(Requires Administrative Privileges.)", inline=False)
    embed.add_field(name=f"{bot.command_prefix}birthday MMDD", value="Sets your birthday. If you provide a year, the bot will ignore it and advise you not to tell it that. I don't wanna know!", inline=False)
    embed.add_field(name=f"{bot.command_prefix}mentionall true/false", value="Toggles whether or not the bot mentions everyone or not. \nFor your sanity, this behaviour is disabled by default. (Requires Administrative Privileges.)", inline=False)
    embed.add_field(name=f"{bot.command_prefix}help", value="Displays this help message, but you already knew that, didn't you?", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def simonsays(ctx, *, message: str):
    await ctx.send(message)

@bot.command()
async def mentionall(ctx, value: bool):
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send("You must be an administrator to change this setting!")
        return

    guild_id = str(ctx.guild.id)
    config = load_config()

    # Ensure the guild_id key exists and is a dictionary
    if guild_id not in config or not isinstance(config[guild_id], dict):
        config[guild_id] = {}

    config[guild_id]["everyone_mention"] = value
    save_config(config)
    await ctx.send(f"Everyone mention set to {value}.")
    
@tasks.loop(hours=24)
async def announce_birthdays():
    today_str = datetime.datetime.now().strftime("%m%d")
    birthdays = load_birthdays()
    config = load_config()
    print(f"Config: {config}")  # Add this line for debugging

    for guild in bot.guilds:
        guild_id = str(guild.id)
        guild_config = config.get(guild_id)
        print(f"Guild ID: {guild_id}, Guild Config: {guild_config}")  # Add this line for debugging
        if not isinstance(guild_config, dict):
            guild_config = {}

        channel_id = guild_config.get("channel_id")
        if channel_id:
            channel = bot.get_channel(channel_id)
        else:
            channel = discord.utils.get(guild.text_channels, name='birthdays')

        if not channel:
            continue
        everyone_mention = guild_config.get("everyone_mention", False)

        
        role_mention = guild_config.get("role_mention", False)
        
        for member in guild.members:
            user_id = str(member.id)
            if user_id in birthdays and birthdays[user_id] == today_str:
                message = "It's " + member.mention + "'s birthday! Happy Birthday " + member.mention + "!"

                #Checks if role_mention = True
                if role_mention:
                    #Pulls role_id from JSON
                    role_id = guild_config.get("role_id")
                    #Checks if it's not empty - this should temporarily resolve if the config is empty
                    if role_id is not None:
                        message = ", " + message
                        message = f'<@&{role_id}>, {message}'

                if everyone_mention:

                    message = "@everyone, " + message

                await channel.send(message)


bot.run(load_bot_token())
