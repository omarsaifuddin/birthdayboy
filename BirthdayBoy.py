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
async def set_birthday_channel(ctx, channel: discord.TextChannel):
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send("You must be an administrator to set the birthday channel.")
        return

    guild_id = str(ctx.guild.id)
    config = load_config()
    config[guild_id] = channel.id
    save_config(config)
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
        guild_config = config.get(guild_id, {})
        
        channel_id = guild_config.get("channel_id")
        if channel_id:
            channel = bot.get_channel(channel_id)
        else:
            channel = discord.utils.get(ctx.guild.text_channels, name='announcements')
        
        if channel:
            everyone_mention = guild_config.get("everyone_mention", False)

            message = "It's " + ctx.author.mention + "'s birthday! Happy Birthday " + ctx.author.mention + "!"
            if everyone_mention:
                message = "@everyone, " + message
            await channel.send(message)

    await ctx.send("Birthday saved.")


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Bot Commands", description="List of available commands", color=0x42f56c)
    embed.add_field(name="!set_birthday_channel #channel", value="Set the channel where birthday announcements are sent (Requires Administrative Privileges).", inline=False)
    embed.add_field(name="!birthday MMDD", value="Sets your birthday. If you provide a year, the bot will ignore it and advise you not to tell it that. I don't wanna know!", inline=False)
    embed.add_field(name="!help", value="Displays this help message, but you already knew that, didn't you?", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def simonsays(ctx, *, message: str):
    await ctx.send(message)

@bot.command()
async def set_everyone_mention(ctx, value: bool):
    if not ctx.message.author.guild_permissions.administrator:
        await ctx.send("You must be an administrator to change this setting!")
        return

    guild_id = str(ctx.guild.id)
    config = load_config()

    if guild_id not in config:
        config[guild_id] = {}

    config[guild_id]["everyone_mention"] = value
    save_config(config)
    await ctx.send(f"Everyone mention set to {value}.")

@tasks.loop(hours=24)
async def announce_birthdays():
    today_str = datetime.datetime.now().strftime("%m%d")
    birthdays = load_birthdays()
    config = load_config()

    for guild in bot.guilds:
        guild_id = str(guild.id)
        guild_config = config.get(guild_id, {})
        
        channel_id = guild_config.get("channel_id")
        if channel_id:
            channel = bot.get_channel(channel_id)
        else:
            channel = discord.utils.get(guild.text_channels, name='announcements')

        if not channel:
            continue

        everyone_mention = guild_config.get("everyone_mention", False)

        for member in guild.members:
            user_id = str(member.id)
            if user_id in birthdays and birthdays[user_id] == today_str:
                message = "It's " + member.mention + "'s birthday! Happy Birthday " + member.mention + "!"
                if everyone_mention:
                    message = "@everyone, " + message
                await channel.send(message)

bot.run(load_bot_token())
