import discord
from discord import ButtonStyle, Interaction, Embed, Message
from discord.ext import commands
from discord.ui import Button, View
from rich.console import Console
import os
from dotenv import load_dotenv
import asyncio
from cogs.ai import AI
from cogs.economy import Economy
from cogs.fun import Fun
from cogs.marriages import Marriages
from cogs.reactions import Reactions
from cogs.songs import Songs
import time
import psycopg2
import json
from datetime import datetime, timezone, timedelta
import ast

console = Console()

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cur = conn.cursor()


load_dotenv()
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle)
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

@bot.command()
async def roadmap(ctx: commands.Context):
    """features i wanna add"""
    features = [
        "debug thing with spendings ai", "add more reactions", 
        "fix !listmarrriages",  "custom emojis", 
        "fix the marriage database that is so messy",  
        "counter that increases every time fact says something racist, homophobic, transphobic, sexist and everythin",
        "achievements?", "other ai models"
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

async def fill_embeds(): 
    home_embed.description = "Click on the buttons below to switch pages. Here are some uncategorized commands: \n\n"
    ai_embed.description = ""
    economy_embed.description = ""
    fun_embed.description = ""
    marriages_embed.description = ""
    reactions_embed.description = ""
    songs_embed.description = ""

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


@bot.command()
async def help(ctx: commands.Context, category: str = None):
    """Shows this message."""
    await fill_embeds()
    view = View()
    
    home_button = Button(label="Home", style=ButtonStyle.green)
    async def home_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=home_embed, view=view)

    home_button.callback = home_button_callback
    view.add_item(home_button)

    ai_button = Button(label="AI", style=ButtonStyle.primary)
    async def ai_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=ai_embed, view=view)

    ai_button.callback = ai_button_callback
    view.add_item(ai_button)

    economy_button = Button(label="Economy", style=ButtonStyle.primary)
    async def economy_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=economy_embed, view=view)

    economy_button.callback = economy_button_callback
    view.add_item(economy_button)

    fun_button = Button(label="Fun", style=ButtonStyle.primary)
    async def fun_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=fun_embed, view=view)

    fun_button.callback = fun_button_callback
    view.add_item(fun_button)

    marriages_button = Button(label="Marriages", style=ButtonStyle.primary)
    async def marriages_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=marriages_embed, view=view)

    marriages_button.callback = marriages_button_callback
    view.add_item(marriages_button)

    reactions_button = Button(label="Reactions", style=ButtonStyle.primary)
    async def reactions_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=reactions_embed, view=view)

    reactions_button.callback = reactions_button_callback
    view.add_item(reactions_button)

    songs_button = Button(label="Songs", style=ButtonStyle.primary)
    async def songs_button_callback(interaction: Interaction):
        await interaction.message.edit(embed=songs_embed, view=view)

    songs_button.callback = songs_button_callback
    view.add_item(songs_button)

    if category is None:
        await ctx.send(embed=home_embed, view=view)
    else:
        match category.lower():
            case "home":
                await ctx.send(embed=home_embed)
            case "ai":
                await ctx.send(embed=ai_embed)
            case "economy":
                await ctx.send(embed=economy_embed)
            case "fun":
                await ctx.send(embed=fun_embed)
            case "marriages":
                await ctx.send(embed=marriages_embed)
            case "reactions":
                await ctx.send(embed=reactions_embed)
            case "songs":
                await ctx.send(embed=songs_embed)
            case _:
                await ctx.send("Invalid category.")

# @bot.command()
# async def debug(ctx: commands.Context):
#     """Ignore this"""
#     commands = await get_commands()
#     await ctx.send(commands)


# Exporting and importing database
# Using Railway's volumes
VOLUME_PATH = "/data"

# Marriage dict is formatted like this
# {'id': 5, 'user1_id': 1206615811792576614, 'user2_id': 1387497689259835563}


@bot.command()
async def export(ctx: commands.Context, table: str):
    """Ignore this"""
    rows = None
    table_name = table.lower()
    if table_name not in ["marriages", "economy"]:
        await ctx.send("invalid table name")
        return
    
    # Marriages Table
    if table_name == "marriages":
        cur.execute("SELECT * FROM marriages")
        collums = [str(desc.name) for desc in cur.description]
        rows = [dict(zip(collums, row)) for row in cur.fetchall()]

        with open(os.path.join(VOLUME_PATH, "export_marriages.txt"), "w") as file:
            file.write(str(rows))

    # Economy Table
    elif table_name == "economy":
        cur.execute("SELECT * FROM economy")
        collums = [str(desc.name) for desc in cur.description]
        rows = [dict(zip(collums, row)) for row in cur.fetchall()]

        with open(os.path.join(VOLUME_PATH, "export_economy.txt"), "w") as file:
            file.write(str(rows))

    # Im removing the items table

    
    await ctx.message.add_reaction("👍")

@bot.command()
async def download(ctx: commands.Context, table: str):
    """Ignore this"""
    table_name = table.lower()
    if table_name not in ["marriages", "economy"]:
        await ctx.send("invalid table name")
        return
    
    export_file = os.path.join(VOLUME_PATH, f"export_{table_name}.txt")
    # If the file doesnt exist
    if not os.path.exists(export_file):
        await ctx.send("export first")
        return
    
    await ctx.send(file=discord.File(export_file))

@bot.command()
async def load(ctx: commands.Context, table: str):
    """Load dictionary data from attachment into database"""
    table_name = table.lower()
    if table_name not in ["marriages", "economy"]:
        await ctx.send("invalid table name")
        return
    
    if not ctx.message.attachments:
        await ctx.send("Please attach a file with the data to import")
        return
        
    attachment = ctx.message.attachments[0]
    data_bytes = await attachment.read()
    data_str = data_bytes.decode()
    
    try:
        # Parse the string representation of a list of dictionaries
        # Since the data contains datetime objects, we need to use eval() with datetime in scope
        import datetime
        data = eval(data_str, {"__builtins__": {}, "datetime": datetime})
        
        if not isinstance(data, list):
            await ctx.send("Data should be a list of dictionaries")
            return
            
    except (ValueError, SyntaxError, NameError) as e:
        await ctx.send(f"Error parsing data: {e}")
        return

    # Create the tables based on schema.sql
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        balance INT DEFAULT 0,
        last_daily TIMESTAMP,
        last_worked TIMESTAMP
    );""")
    conn.commit()

    cur.execute("""CREATE TABLE IF NOT EXISTS marriages (
        id SERIAL PRIMARY KEY,
        user1_id REFERENCES users(user_id),
        user2_id REFERENCES users(user_id)
    );""")
    conn.commit()

    # Load data based on table type
    try:
        if table_name == "economy":
            # Clear existing data
            cur.execute("DELETE FROM users")
            
            # Insert economy data into users table
            for record in data:
                cur.execute("""
                    INSERT INTO users (user_id, balance, last_daily, last_worked) 
                    VALUES (%s, %s, %s, %s)
                """, (
                    record['user_id'],
                    record.get('balance', 0),
                    record.get('last_daily'),
                    record.get('last_worked')
                ))
                
        elif table_name == "marriages":
            # Clear existing data
            cur.execute("DELETE FROM marriages")
            
            # Insert marriage data
            for record in data:
                cur.execute("""
                    INSERT INTO marriages (user1_id, user2_id) 
                    VALUES (%s, %s)
                """, (
                    record['user1_id'],
                    record['user2_id']
                ))
                
        
        conn.commit()
        await ctx.send(f"Successfully loaded {len(data)} records into {table_name} table")
        
    except Exception as e:
        conn.rollback()
        await ctx.send(f"Error loading data: {e}")
    

async def main():
    await load_cogs()
    console.print("Bot is ready.")
    await bot.start(token)

asyncio.run(main())