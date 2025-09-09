# Ierzi Bot

# Discord.py Improrts
import discord
from discord import Interaction, Embed, Message, SelectOption, Game
from discord.ext import commands
from discord.ui import View, Select

# Cogs
from cogs.ai import AI
from cogs.economy import Economy
from cogs.fun import Fun
from cogs.marriages import Marriages
from cogs.reactions import Reactions
from cogs.songs import Songs
from cogs.search import Search

# Other
from rich.console import Console
# Both of these are useless since im hosting on railway, so I don't need to load the env
# (if yall wanna selfhost this idk)
import os
from dotenv import load_dotenv
import asyncio
import time
# I've heard there's an async version of this but ion wanna remake my whole bot for this :wilted_rose:
# It's not like a ton of ppl are using it anyway
import psycopg2

console = Console()

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()

token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle)
    await fill_embeds()
    console.print(f"Logged in as {bot.user}")

# Error handling
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Try again in {round(error.retry_after, 2)} seconds.")
    if isinstance(error, commands.CommandNotFound):
        # useless error
        return
    else:
        console.print(f"Ignored error in {ctx.command}: {error}" if ctx.command else f"Ignored error: {error}")

@bot.event
async def on_message(message: Message):
    if message.poll and message.channel.id == 1411714823405965342: # poll channel
        await message.create_thread(name=message.poll.question)
    
    await bot.process_commands(message)

# Cog loading
async def load_cogs():
    console.print("Loading cogs...")
    await bot.add_cog(AI(bot, console))
    console.print("AI cog loaded.")
    await bot.add_cog(Economy(bot, console))
    console.print("Economy cog loaded.")
    await bot.add_cog(Fun(bot, console))
    console.print("Fun cog loaded.")
    await bot.add_cog(Marriages(bot, console))
    console.print("Marriages cog loaded.")
    await bot.add_cog(Reactions(bot, console))
    console.print("Reactions cog loaded.")
    start = time.time()
    await bot.add_cog(Songs(bot, console))
    end = time.time()
    console.print(f"Songs cog loaded in {round(end - start, 2)} seconds.")
    await bot.add_cog(Search(bot, console))
    console.print("Search cog loaded.")
    console.print("All cogs loaded.")

# Other commands
@bot.command()
async def id(ctx: commands.Context, user: discord.Member):
    """Gets the ID of an user."""
    if not user:
        await ctx.send(ctx.author.id)
        return
    
    await ctx.send(user.id)

@bot.command()
async def profile(ctx: commands.Context, *user_id: int | tuple):
    """Gets the profile of an user based on an ID."""
    if user_id == None or user_id == ():
        await ctx.send("Gimme user ids. \n-# if you dont know what that is, ignore this")
    
    if isinstance(user_id, tuple):
        message = ""
        for id in user_id:
            user = bot.get_user(id) or await bot.fetch_user(id)
            message += f"{user.mention}\n"
        
        await ctx.send(message, allowed_mentions=discord.AllowedMentions.none())
        return

    user = bot.get_user(user_id) or await bot.fetch_user(user_id)
    
    await ctx.send(user.mention, allowed_mentions=discord.AllowedMentions.none())

@bot.command()
async def github(ctx: commands.Context):
    """cool github repo"""
    await ctx.send("https://github.com/Ierzi/ierzi-bot \n-# btw i have no fucking clue how contributing on github works")

#TODO: all of this
@bot.command()
async def roadmap(ctx: commands.Context):
    """features i wanna add"""
    features = [
        "debug thing with spendings ai", "add more reactions", 
        "fix !listmarrriages",  "custom emojis", 
        "fix the marriage database that is so messy",  
        "counter that increases every time fact says something racist, homophobic, transphobic, sexist and everythin",
        "achievements?", "other ai models", "pronouns"
        ]
    message = "Features I wanna add: \n"
    for feature in features:
        message += f"- {feature}\n"
    await ctx.send(message)

# help command
def get_commands(bot: commands.Bot):
    all_commands: list[tuple[str, str, str]] = [] # Format: Command name, cog name, command help
    for cog_name, cog in bot.cogs.items():
        for command in cog.get_commands():
            all_commands.append((command.name, cog_name, command.help))
    
    no_cogs_commands = [cmd for cmd in bot.commands if cmd.cog is None]
    if no_cogs_commands:
        for command in no_cogs_commands:
            all_commands.append((command.name, None, command.help))

    return all_commands

home_embed = Embed(
    title="Help Menu",
    description="Click on the buttons below to switch pages. Here are some uncategorized commands: \n\n"
)

ai_embed = Embed(
    title="AI Commands",
    description=""
)

economy_embed = Embed(
    title="Economy Commands",
    description=""
)

fun_embed = Embed(
    title="Fun Commands",
    description=""
)

marriages_embed = Embed(
    title="Marriage Commands",
    description=""
)

reactions_embed = Embed(
    title="Reaction Commands",
    description=""
)

songs_embed = Embed(
    title="Songs Commands",
    description=""
)

search_embed = Embed(
    title="Search Commands",
    description=""
)

async def fill_embeds(): 
    home_embed.description = "Use the select menu below to switch pages. Here are some uncategorized commands: \n\n"
    ai_embed.description = ""
    economy_embed.description = ""
    fun_embed.description = ""
    marriages_embed.description = ""
    reactions_embed.description = ""
    songs_embed.description = ""
    search_embed.description = ""

    all_commands = get_commands(bot)
    for command_name, cog_name, command_help in all_commands:
        match cog_name:
            case None:
                if command_name in ["download", "export", "load"]:
                    # Testing commands to ignore
                    continue
                home_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "AI":
                ai_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "Economy":
                economy_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "Fun":
                fun_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "Marriages":
                marriages_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "Reactions":
                reactions_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "Songs":
                songs_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "Search":
                search_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"

@bot.command()
async def help(ctx: commands.Context, category: str = None):
    """Shows this message."""
    view = View(timeout=300) # 5 minutes

    help_options = [
        SelectOption(label="Home", description="Homepage and uncategorized commands"),
        SelectOption(label="AI", description="AI commands"),
        SelectOption(label="Economy", description="Economy commands"),
        SelectOption(label="Fun", description="Fun commands"),
        SelectOption(label="Marriages", description="Marriage commands"),
        SelectOption(label="Reactions", description="Reaction commands"),
        SelectOption(label="Songs", description="Songs commands"),
        SelectOption(label="Search", description="Search commands"),
    ]
    help_select = Select(
        placeholder="select category",
        options=help_options
    )

    async def help_select_callback(interaction: Interaction):
        selected = help_select.values[0].lower()
        match selected:
            case "home":
                await interaction.response.edit_message(embed=home_embed)
            case "ai":
                await interaction.response.edit_message(embed=ai_embed)
            case "economy":
                await interaction.response.edit_message(embed=economy_embed)
            case "fun":
                await interaction.response.edit_message(embed=fun_embed)
            case "marriages":
                await interaction.response.edit_message(embed=marriages_embed)
            case "reactions":
                await interaction.response.edit_message(embed=reactions_embed)
            case "songs":
                await interaction.response.edit_message(embed=songs_embed)
            case "search":
                await interaction.response.edit_message(embed=search_embed)
            case _:
                await interaction.response.send_message("Invalid category.", ephemeral=True)

    help_select.callback = help_select_callback
    view.add_item(help_select)

    if category is None:
        await ctx.send(embed=home_embed, view=view)
    else:
        match category.lower():
            case "home":
                await ctx.send(embed=home_embed, view=view)
            case "ai":
                await ctx.send(embed=ai_embed, view=view)
            case "economy":
                await ctx.send(embed=economy_embed, view=view)
            case "fun":
                await ctx.send(embed=fun_embed, view=view)
            case "marriages":
                await ctx.send(embed=marriages_embed, view=view)
            case "reactions":
                await ctx.send(embed=reactions_embed, view=view)
            case "songs":
                await ctx.send(embed=songs_embed, view=view)
            case "search":
                await ctx.send(embed=search_embed, view=view)
            case _:
                await ctx.send("Invalid category.")
# @bot.command()
# async def debug(ctx: commands.Context):
#     """Ignore this"""
#     commands = await get_commands()
#     await ctx.send(commands)

async def main():
    await load_cogs()
    console.print("Bot is ready.")
    await bot.start(token)

asyncio.run(main())