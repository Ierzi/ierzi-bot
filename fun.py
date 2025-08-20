import discord
from discord.ext import commands
import random
from rich.console import Console

console = Console()

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.command()
    async def istrans(self, ctx: commands.Context, user: discord.Member):
        if user.id == 1153301933231181824:
            await ctx.send("yes")
        elif user.id == 966351518020300841:
            await ctx.send("no")
        else:
            await ctx.send(random.choice(["no", "yes", "not yet"]))

    @commands.command()
    async def d20(self, ctx: commands.Context):
        roll = random.randint(1, 20)
        await ctx.send(f"{roll}")
    
    @commands.command()
    async def coinflip(self, ctx: commands.Context):
        result = random.choice(["heads", "tails"])
        await ctx.send(result)
    
    @commands.command()
    async def hello(ctx: commands.Context):
        await ctx.send(random.choice(["hi", "hello", "fuck you"]))


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
    console.print("Fun cog loaded.")