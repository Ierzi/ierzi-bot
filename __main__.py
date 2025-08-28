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

console = Console()

load_dotenv()
token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    await bot.add_cog(Songs(bot, console))
    console.print("Songs cog loaded.")
    console.print("All cogs loaded.")

# Other commands
@bot.command()
async def id(ctx: commands.Context, user: discord.Member):
    if not user:
        await ctx.send(ctx.author.id)
        return
    
    await ctx.send(user.id)

@bot.command()
async def profile(ctx: commands.Context, *user_id: int | tuple):
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
async def wiki(ctx: commands.Context):
    """cool github wiki"""
    view = View()
    wiki_button = Button(
        label="Wiki",
        url="https://github.com/Ierzi/ierzi-bot/wiki/"
    )
    view.add_item(wiki_button)
    await ctx.send(view=view)

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
        "UPDATE THE WIKI", "cat videos", "fix the marriage database that is so messy",  
        "counter that increases every time fact says something racist, homophobic, transphobic, sexist and everythin",
        "achievements?", "other ai models"
        ]
    message = "Features I wanna add: \n"
    for feature in features:
        message += f"- {feature}\n"
    await ctx.send(message)

# help command

home_embed = Embed(
    title="Help",
    description="test command im reworking on the help menu"
)

class HelpView(View):
    @discord.ui.button(label="Home", style=ButtonStyle.gray)
    async def home_button(self, interaction: Interaction, button: Button):
        await interaction.message.edit()

@bot.command()
async def test_command(ctx: commands.Context):
    await ctx.send(embed=home_embed, view=HelpView())

# @bot.command()
# async def debug(ctx: commands.Context, fake_n_marriages: int | None = None):
#     """Ignore this"""
#     marriages = await get_marriages()
#     console.print(marriages)

async def main():
    await load_cogs()
    console.print("Bot is ready.")
    await bot.start(token)

asyncio.run(main())