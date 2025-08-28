import discord
from discord import ButtonStyle, Interaction, Embed, Colour
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

console = Console()

load_dotenv()
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle)
    console.print(f"Logged in as {bot.user}")

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
        "debug thing with spendings ai", "fix !aiask", "add more reactions", 
        "fix !listmarrriages",  "custom emojis", "song recommendation based on my playlist",
        "cat videos", "fix the marriage database that is so messy",  
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

@bot.command()
async def debug(ctx: commands.Context):
    """Ignore this"""
    commands = await get_commands()
    await ctx.send(commands)

async def main():
    await load_cogs()
    console.print("Bot is ready.")
    await bot.start(token)

asyncio.run(main())