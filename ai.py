import os
from rich.console import Console
from discord.ext import commands
import discord
from openai import OpenAI

console = Console()

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.console = Console()
        self.openai_key = os.getenv("OPENAI_KEY")
    
    @commands.command()
    async def aiask(self, ctx: commands.Context, *, text: str):
        author = ctx.author
        thinking = await ctx.send("The ai is thinking...")

        client = OpenAI(api_key=self.openai_key)
        response = client.responses.create(
            model="gpt-5-mini",
            input=text,
            max_output_tokens=3000
        )

        text = f"{author.mention}: {text} \n \n AI: {response.output_text}"
        await thinking.delete()
        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
    console.print("AI cog loaded.")