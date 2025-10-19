# Ierzi Bot

# Discord.py Improrts
import discord
from discord import Interaction, Embed, Message, SelectOption, app_commands
from discord.activity import CustomActivity
from discord.ext import commands, tasks
from discord.ui import View, Select

# Cogs
from cogs.ai import AI
from cogs.birthday import BirthdayCog as Birthday
from cogs.economy import Economy
from cogs.fun import Fun
from cogs.marriages import Marriages
from cogs.reactions import Reactions
from cogs.search import Search
from cogs.songs import Songs

# Utilities
from cogs.utils import pronouns
from cogs.utils.database import db

# Other
import asyncio
from collections import OrderedDict
from datetime import datetime, timezone
from dotenv import load_dotenv # Dotenv is useless cause im hosting on railway
import os
import random
from rich.console import Console
from typing import Optional, Any
import time

console = Console()

load_dotenv()

token = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    command_prefix="!", 
    intents=intents, 
    help_command=None, 
    case_insensitive=True
)

experimental_branch = False

# Events
@bot.event
async def on_ready():
    # Change the presence based on the bot's number of servers
    guild_count = len(bot.guilds)
    await bot.change_presence(status=discord.Status.idle, activity=CustomActivity(f"dtupid - {guild_count} servers")) # Discord bot starter pack
    await fill_embeds()
    synced = await bot.tree.sync()
    console.print(f"Synced {len(synced)} commands.")
    console.print(f"Logged in as {bot.user}")
    await bot_loop.start()

    if bot.user.id == 1412488383178998044: #experimental bot id
        global experimental_branch
        experimental_branch = True

@tasks.loop(minutes=10)
async def bot_loop():
    #  Various tasks the bot runs in the background

    # Update bot presence
    guild_count = len(bot.guilds)
    await bot.change_presence(status=discord.Status.idle, activity=CustomActivity(f"dtupid - {guild_count} servers"))

    # I would add a clear last messages loop but using OrderedDict is better

# Error handling
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Try again in {round(error.retry_after, 2)} seconds.")
    if isinstance(error, commands.CommandNotFound):
        # useless error
        pass
    else:
        console.print(f"Ignored error in {ctx.command}: {error}" if ctx.command else f"Ignored error: {error}")

@bot.event
async def on_message(message: Message):
    now = datetime.now(tz=timezone.utc) # Save it early

    # Auto create threads in the poll channel
    if message.poll and message.channel.id == 1411714823405965342: 
        await message.create_thread(name=message.poll.question)
    
    if not message.author.id == bot.user.id:
        # @Ierzi Bot is this true
        if bot.user in message.mentions:
            if 'is this true' in message.content.lower() or 'is ts true' in message.content.lower():
                ai = AI(bot, console)
                ctx = await bot.get_context(message)
                # get reply

                reply_id = message.reference.message_id
                reply = await ctx.channel.fetch_message(reply_id)
                reply_content = reply.content
    
                response = await ai.isthistrue(ctx, reply_content)
                if isinstance(response, list):
                    for m in response:
                        await message.reply(m, allowed_mentions=discord.AllowedMentions.none())
                        await asyncio.sleep(0.2)
                    
                    return
                
                await message.reply(response, allowed_mentions=discord.AllowedMentions.none())
        
        # @Grok is this true
        if '@grok is this true' in message.content.lower() or '@grok is ts true' in message.content.lower():
            if random.choice([True, False]):
                await message.add_reaction("✅")
            else:
                await message.add_reaction("❌")

    # Finally, process commands
    await bot.process_commands(message)


# Cog loading
async def load_cogs():
    console.print("Loading cogs...")
    await bot.add_cog(AI(bot, console))
    console.print("AI cog loaded.")
    await bot.add_cog(Birthday(bot, console))
    console.print("Birthday cog loaded.")
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


#AI commands to add to the context menu
ai = AI(bot, console)
@bot.tree.context_menu(name="TLDR")
async def tldr(interaction: Interaction, message: Message):
    await interaction.response.defer()
    _tldr = await ai._tldr(message.content)
    if not _tldr:
        await interaction.followup.send("error :(", ephemeral=True)
        return
    
    await interaction.followup.send(_tldr)

@bot.tree.context_menu(name="TSMR")
async def tsmr(interaction: Interaction, message: Message):
    await interaction.response.defer()
    _tsmr = await ai._tsmr(message.content)
    if not _tsmr:
        await interaction.followup.send("error :(", ephemeral=True)
        return
    
    if isinstance(_tsmr, str):
        await interaction.followup.send(_tsmr)
        return
    
    for mess in _tsmr:
        await interaction.followup.send(mess)
        await asyncio.sleep(0.2)

@bot.tree.context_menu(name="Is this true?")
async def isthistrue(interaction: Interaction, message: Message):
    await interaction.response.defer()
    _isthistrue = await ai._isthistrue(message.content)
    if not _isthistrue:
        await interaction.followup.send("error :(", ephemeral=True)
        return
    
    if isinstance(_isthistrue, str):
        await interaction.followup.send(_isthistrue)
        return
    
    for mess in _isthistrue:
        await interaction.followup.send(mess)
        await asyncio.sleep(0.2)


# App commands
search = Search(bot, console)

@bot.tree.command(name="define", description="Look up the meaning of a word.")
@app_commands.describe(word="The word to get the definition from.")
async def define(interaction: Interaction, word: str):
    await interaction.response.defer()
    _define = await search._define(word)
    if _define is None:
        await interaction.followup.send("Word not found / Error.")
        return

    await interaction.followup.send(_define)

@bot.tree.command(name="ud", description="Look up the meaning of a word on the Urban Dictionary.")
@app_commands.describe(word="The word to search the meaning on Urban Dictionary.")
async def urban_dictionary(interaction: Interaction, word: str):
    await interaction.response.defer()
    _ud = search._urban_dictionary(word)
    if _ud is None:
        await interaction.followup.send("Word not found / Error.")
        return
    
    await interaction.followup.send(_ud)

# Other commands
@bot.command(name="id")
async def id_user(ctx: commands.Context, user: discord.User = None):
    """Gets the ID of an user."""
    if not user:
        await ctx.send(ctx.author.id)
        return
    
    await ctx.send(user.id)

@bot.command()
async def profile(ctx: commands.Context, *user_ids: int):
    """Gets the profile of user(s) by ID."""
    if not user_ids:
        await ctx.send("Gimme user ids. \n-# if you dont know what that is, ignore this")
        return

    if len(user_ids) == 1:
        uid = user_ids[0]
        user = bot.get_user(uid) or await bot.fetch_user(uid)
        await ctx.send(user.mention, allowed_mentions=discord.AllowedMentions.none())
        return

    message = ""
    for uid in user_ids:
        user = bot.get_user(uid) or await bot.fetch_user(uid)
        message += f"{user.mention}, "
    message = message[:-2] # remove the last comma
    await ctx.send(message, allowed_mentions=discord.AllowedMentions.none())

@bot.command()
async def github(ctx: commands.Context):
    """if you wanna contribute idk"""
    global experimental_branch
    if experimental_branch:
        await ctx.send("https://git.gay/Ierzi/ierzi-bot/src/branch/experimental \nhttps://github.com/Ierzi/ierzi-bot/tree/experimental")
        return
    
    await ctx.send("https://github.com/Ierzi/ierzi-bot \nhttps://git.gay/Ierzi/ierzi-bot (wtf is git.gay :sob:) \n-# btw i have no fucking clue how contributing on github works")

#TODO: all of this
@bot.command()
async def roadmap(ctx: commands.Context):
    """features i wanna add"""
    features = [
        "add more reactions", "fix !listmarriages", 
        "counter that increases every time fact says something racist, homophobic, transphobic, sexist and everythin",
        "achievements?", "other ai models", "custom pronouns", "more reactions", "custom ai models",
        "more songs commands but idk what to add", "more birthday commands", "do thing to request ideas by dming the bot"
        ]
    message = "Features I wanna add: \n"
    for feature in features:
        message += f"- {feature}\n"
    await ctx.send(message)

# help command
def get_commands(bot: commands.Bot) -> list[tuple[str, str, str]]:
    all_commands: list[tuple[str, str, str]] = [] # Format: Command name, cog name, command help
    for cog_name, cog in bot.cogs.items():
        for command in cog.get_commands():
            # Check if this is a group command with subcommands
            if isinstance(command, commands.Group) and command.commands:
                # Add the group command itself
                all_commands.append((command.name, cog_name, command.help))
                # Add all subcommands with their full name (group.subcommand)
                for subcommand in command.commands:
                    full_name = f"{command.name} {subcommand.name}"
                    all_commands.append((full_name, cog_name, subcommand.help))
            else:
                # Regular command
                all_commands.append((command.name, cog_name, command.help))
    
    no_cogs_commands = [cmd for cmd in bot.commands if cmd.cog is None]
    if no_cogs_commands:
        for command in no_cogs_commands:
            # Check if this is a group command with subcommands (for commands not in cogs)
            if isinstance(command, commands.Group) and command.commands:
                # Add the group command itself
                all_commands.append((command.name, None, command.help))
                # Add all subcommands with their full name (group.subcommand)
                for subcommand in command.commands:
                    full_name = f"{command.name} {subcommand.name}"
                    all_commands.append((full_name, None, subcommand.help))
            else:
                # Regular command
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

birthday_embed = Embed(
    title="Birthday Commands",
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
    birthday_embed.description = ""
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
                if command_name in ["download", "export", "load", 'fsp']:
                    # Testing commands to ignore
                    continue
                home_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "AI":
                ai_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
            case "BirthdayCog":
                birthday_embed.description += f"**{command_name}** - {command_help if command_help is not None else 'No description'} \n"
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
        SelectOption(label="Birthday", description="Birthday commands"),
        SelectOption(label="Economy", description="Economy commands"),
        SelectOption(label="Fun", description="Fun commands"),
        SelectOption(label="Marriages", description="Marriage commands"),
        SelectOption(label="Reactions", description="Reaction commands"),
        SelectOption(label="Search", description="Search commands"),
        SelectOption(label="Songs", description="Songs commands"),
    ]
    help_select = Select(
        placeholder="select category",
        options=help_options
    )

    async def help_select_callback(interaction: Interaction):
        selected = help_select.values[0].lower()
        match selected:
            case "home":
                await interaction.message.edit(embed=home_embed)
            case "ai":
                await interaction.message.edit(embed=ai_embed)
            case "birthday":
                await interaction.message.edit(embed=birthday_embed)
            case "economy":
                await interaction.message.edit(embed=economy_embed)
            case "fun":
                await interaction.message.edit(embed=fun_embed)
            case "marriages":
                await interaction.message.edit(embed=marriages_embed)
            case "reactions":
                await interaction.message.edit(embed=reactions_embed)
            case "songs":
                await interaction.message.edit(embed=songs_embed)
            case "search":
                await interaction.message.edit(embed=search_embed)

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
            case "birthday":
                await ctx.send(embed=birthday_embed, view=view)
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

# Pronouns Test
@bot.command(name="pronouns")
async def pronouns_set(ctx: commands.Context):
    """Set your pronouns."""
    user_id = ctx.author.id

    if user_id == 1206615811792576614: #fact
        await ctx.message.add_reaction("❌")
        return

    set_pronouns_embed = Embed(
        title="Set your pronouns!",
        # Manual description
        description="Choose your pronouns here. Currently supported pronouns: "
    )
    set_pronouns_embed.description += ", ".join(pronouns.all_pronouns)


    current_pronouns = await pronouns.get_pronouns(user_id)
    set_pronouns_embed.add_field(name="Current pronouns", value=f"Current pronouns: {current_pronouns}")

    view = View(timeout=500)
    pronouns_option = [
        SelectOption(label='he/him'),
        SelectOption(label='she/her'),
        SelectOption(label='they/them/themself'),
        SelectOption(label='they/them/themselves'),
        SelectOption(label="it/its"),
        SelectOption(label="one/one's"),
        SelectOption(label='any')
    ] # will add more pronouns later
    # to keep updated every time I add new pronouns

    pronouns_select = Select(
        placeholder='Select your pronouns...',
        options=pronouns_option
    )

    # Big callback function
    async def pronouns_select_callback(interaction: Interaction):
        selected = pronouns_select.values[0]
        match selected:
            case 'he/him':
                await pronouns.set_pronouns(user_id, 'he/him')
                set_pronouns_embed.set_field_at(0, value="Current pronouns: he/him")
                await interaction.message.edit(content="Set your pronouns to he/him.", embed=set_pronouns_embed)
                return
            case 'she/her':
                await pronouns.set_pronouns(user_id, 'she/her')
                set_pronouns_embed.set_field_at(0, value="Current pronouns: she/her")
                await interaction.message.edit(content="Set your pronouns to she/her.", embed=set_pronouns_embed)
                return
            case 'they/them/themselves':
                await pronouns.set_pronouns(user_id, 'they/them/themselves')
                set_pronouns_embed.set_field_at(0, value="Current pronouns: they/them/themselves")
                await interaction.message.edit(content="Set your pronouns to they/them/themselves.", embed=set_pronouns_embed)
                return
            case 'they/them/themself':
                await pronouns.set_pronouns(user_id, 'they/them/themself')
                set_pronouns_embed.set_field_at(0, value="Current pronouns: they/them/themself")
                await interaction.message.edit(content="Set your pronouns to they/them/themself.", embed=set_pronouns_embed)
                return
            case 'it/its':
                await pronouns.set_pronouns(user_id, 'it/its')
                set_pronouns_embed.set_field_at(0, value="Current pronouns: it/its")
                await interaction.message.edit(content='Set your pronouns to it/its.', embed=set_pronouns_embed)
                return
            case "one/one's":
                await pronouns.set_pronouns(user_id, "one/one's")
                set_pronouns_embed.set_field_at(0, value="Current pronouns: one/one's")
                await interaction.message.edit(content="Set your pronouns to one/one's.", embed=set_pronouns_embed)
            case 'any':
                await pronouns.set_pronouns(user_id, 'any')
                set_pronouns_embed.set_field_at(0, value="Current pronouns: any")
                await interaction.message.edit(content="Set your pronouns to any.", embed=set_pronouns_embed)
                return

    pronouns_select.callback = pronouns_select_callback
    view.add_item(pronouns_select)

    await ctx.send(embed=set_pronouns_embed, view=view)


async def try_pronouns(user_id: int):
    all_pronouns = await pronouns.get_pronoun(user_id, pronouns.ALL)

    # Sentences (thanks pronouns.page)
    subject = f'I think {all_pronouns[0]} is very nice. ' if all_pronouns[0] != 'they' else f'I think {all_pronouns[0]} are very nice. '
    _object = f'I met {all_pronouns[1]} recently. '
    possessive = f'Is this {all_pronouns[2]} cat? '
    possessive_2 = f'My favorite color is purple, {all_pronouns[3]} is yellow. '
    reflexive = f'{all_pronouns[0].capitalize()} did it all by {all_pronouns[4]}.'

    full = subject + _object + possessive + possessive_2 + reflexive
    return full

@bot.command(name="getpronouns")
async def get_pronouns(ctx: commands.Context, user: Optional[discord.User] = None):
    """Get someone's pronouns."""
    # Get user_id
    if user:
        user_id = user.id
    else:
        user_id = ctx.author.id
    
    _pronouns = await pronouns.get_pronouns(user_id, get_na=True)
    user_profile = user if user is not None else ctx.author
    user_id = user_profile.id

    if user:
        if _pronouns == 'na':
            await ctx.send(f"{user_profile.mention} didn't set their pronouns.")
            return
        else:
            await ctx.send(f"{user_profile.mention}'s pronouns are {_pronouns}.")
    else:
        if _pronouns == 'na':
            await ctx.send("You didn't set your pronouns! Use !pronouns to set them.")
            return
        else:
            await ctx.send(f"Your current pronouns are {_pronouns}.")
    
    # Test sentence with their pronouns
    test_sentence = await try_pronouns(user_id)
    await ctx.send(test_sentence)

@bot.command(name='fsp')
async def force_set_pronouns(ctx: commands.Context, user: discord.User, _pronouns: str):
    if ctx.author.id != 966351518020300841:
        await ctx.message.add_reaction("❌")
        return
    
    user_id = user.id
    
    if _pronouns not in pronouns.all_pronouns_hidden:
        await ctx.send("invalid pronouns")
        return

    await pronouns.set_pronouns(user_id, _pronouns)
    await ctx.message.add_reaction("👍")

async def main():
    await db.init_pool()
    try:
        await load_cogs() 
        console.print("Bot is ready.")
        await bot.start(token)
    finally:
        await db.close_pool()

asyncio.run(main())