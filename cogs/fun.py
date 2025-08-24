import discord
from discord.ui import View, Button
from discord.ext import commands
import random
from rich.console import Console
import aiohttp

console = Console()

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def istrans(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id in [1153301933231181824, 966351518020300841, 1399689963284467723]: #apex, ierzi and the bot
            await ctx.send("no")
            return
        if user.id == 902148645753856020: #maja
            await ctx.send("yes")
            return
        if user.id == 1206615811792576614: #fa*t
            await ctx.send("yes, transfem. yes, fact she/her is real. yes, this message is personalized just for her <33")
            return
        
        await ctx.send(random.choice(["no", "yes"]))
    
    @commands.command()
    async def isgay(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id in [966351518020300841, 1399689963284467723]: #ierzi and the bot
            await ctx.send("no")
            return
        if user.id in [
            1279666598441123840, 1120940924910977064, 955623247725072476, 747918143745294356, 
            893298676003393536, 980436567531335700, 730885117656039466, 1220973198875693156     
            ]: # way too many people
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["no", "yes"]))

    @commands.command()
    async def isrich(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id == 1206615811792576614 or user.id == 1344010392506208340: #fa*t
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))

    @commands.command()
    async def ishomophobic(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id == 1206615811792576614 or user.id == 1344010392506208340: #fa*t
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))
    
    @commands.command()
    async def islesbian(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id in [1387497689259835563, 1076823281442754652, 953630995830165514, 1206615811792576614, 1344010392506208340]: #ace (2 accounts), syndey (lmao) and fa*t (both accounts)
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))

    @commands.command()
    async def roll(self, ctx: commands.Context, sides: int = 6):
        roll = random.randint(1, sides)
        await ctx.send(f"You rolled a {roll}")

    @commands.command()
    async def d20(self, ctx: commands.Context):
        roll = random.randint(1, 20)
        await ctx.send(f"{roll}")
    
    @commands.command()
    async def coinflip(self, ctx: commands.Context):
        result = random.choice(["heads", "tails"])
        await ctx.send(result)
    
    @commands.command()
    async def hello(self, ctx: commands.Context):
        await ctx.send(random.choice(["hi", "hello", "fuck you"]))
    
    @commands.command(name="2ball")
    async def twoball(self, ctx: commands.Context):
        """8ball but only 2 options, yes and no."""
        result = random.choice(["yes", "no"])
        await ctx.send(result)

    @commands.command()
    async def guessnumber(self, ctx: commands.Context, guess: int):
        """Guess the number between 0 and 10000."""
        number = random.randint(0, 10000)
        if number == guess:
            await ctx.send(f"Congrats {ctx.author.mention}, you guessed the right number {number}!")
            return
        
        await ctx.send("no.")
    
    @commands.command(name="ud")
    async def urban_dictionary(self, ctx: commands.Context, *, word: str):
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
        request_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as r:
                r = await r.json()
                
        # r = requests.get(request_url).json()

        try:
            meanings = r[0]['meanings']
        except Exception as e:
            console.print(e)
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

    @commands.command()
    async def cat(self, ctx: commands.Context):
        """Shows a cute cat picture :3"""
        request_url = "https://api.thecatapi.com/v1/images/search"

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as r:
                r = await r.json()
        
        cat_url = r[0]['url']

        embed = discord.Embed(
            title="Meow :3", 
            color=discord.Color.yellow()
        )
        embed.set_image(url=cat_url)
        await ctx.send(embed=embed)
