import discord
from discord.ui import View, Button
from discord.ext import commands
import random
from rich.console import Console
import requests

console = Console()

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def istrans(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id == 1153301933231181824: #apex
            await ctx.send("no")
            return
        if user.id == 966351518020300841: #ierzi
            await ctx.send("no")
            return
        if user.id == 1399689963284467723: #the bot
            await ctx.send("no")
            return
        if user.id == ctx.author.id:
            view = View()
            button = Button(
                label="Am I Trans?",
                url="https://amitrans.org/"
            )
            view.add_item(button)
            await ctx.send(view=view)
            return
        
        await ctx.send(random.choice(["no", "yes", "idk ask them"]))
    
    @commands.command()
    async def isrich(self, ctx: commands.Context, user: discord.Member = None):
        if user == None:
            user = ctx.author
        
        if user.id == 1206615811792576614 or user.id == 1344010392506208340:
            await ctx.send("yes")
            return
        
        await ctx.send(random.choice(["yes", "no"]))

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
    async def twoball(self, ctx: commands.Context, *, text: str):
        """8ball but only 2 options, yes and no"""
        result = random.choice(["yes", "no"])
        await ctx.send(result)

    @commands.command()
    async def guessnumber(self, ctx: commands.Context, guess: int):
        """Guess the number between 0 and 10000."""
        number = random.randint(0, 10000)
        if number == guess:
            await ctx.send(f"You guessed the right number! {number}")
            return
        
        await ctx.send("no.")
    
    @commands.command(name="ud")
    async def urban_dictionary(self, ctx: commands.Context, *, word: str):
        request_url = f"https://unofficialurbandictionaryapi.com/api/search?term={word}&strict=true"
        r = requests.get(request_url)
        if r.status_code != 200:
            if r.status_code == 404:
                console.print(f"{word} not found.")
                await ctx.send("Word not found.")
                return
            console.print("Invalid status code.")
            ctx.send(f"Invalid status code {r.status_code}")
            return
        
        r_json = r.json()
        definition = r_json["data"][0]["meaning"]

        console.print(f"[UD] - {word} definition: {definition}")
        await ctx.send(f"{ctx.author.mention}: {word} \n\n{definition}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
    console.print("Fun cog loaded.")