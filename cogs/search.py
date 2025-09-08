import discord
from discord.ext import commands
from rich.console import Console
import aiohttp

class Search(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console

    @commands.command(name="ud")
    async def urban_dictionary(self, ctx: commands.Context, *, word: str):
        """Look up the meaning of a word on the Urban Dictionary."""
        request_url = f"https://unofficialurbandictionaryapi.com/api/search?term={word}&strict=true"

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as r:
                data = await r.json()
                definition = data['data'][0]['meaning']

        # r = requests.get(request_url)
        # if r.status_code != 200:
        #     if r.status_code == 404:
        #         console.print(f"{word} not found.")
        #         await ctx.send("Word not found.")
        #         return
        #     console.print("Invalid status code.")
        #     ctx.send(f"Invalid status code {r.status_code}")
        #     return
        
        # r_json = r.json()
        # definition = r_json["data"][0]["meaning"]

        await ctx.send(f"{ctx.author.mention}: **{word}** \n\n{definition}", allowed_mentions=discord.AllowedMentions.none())
    
    @commands.command()
    async def define(self, ctx: commands.Context, *, word: str):
        """Look up the meaning of a word."""
        request_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as r:
                r = await r.json()
                
        # r = requests.get(request_url).json()

        try:
            meanings = r[0]['meanings']
        except Exception as e:
            await ctx.send("Word not found / Error.")
            return
        
        message = f"{ctx.author.mention}: **{word}** \n\n"
        for meaning in meanings:
            message += f"**({meaning['partOfSpeech']})**\n"
            definitions = meaning['definitions']
            for i, definition in enumerate(definitions):
                d = definition['definition']
                message += f"{i + 1}. {d} \n"
            
            message += "\n"
        
        await ctx.send(message, allowed_mentions=discord.AllowedMentions.none())

    # TODO    
    # @commands.command()
    # async def wiki()