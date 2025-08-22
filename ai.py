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
        thinking = await ctx.send("The ai is thinking...", allowed_mentions=discord.AllowedMentions.none())

        client = OpenAI(api_key=self.openai_key)
        response = client.responses.create(
            model="gpt-5-mini-2025-08-07",
            input=text,
            max_output_tokens=3000
        )
        
        if response.error:
            console.print(response.error)
            await thinking.delete()
            await ctx.send("There was an error while generating the response.")
            return
        if response.output_text == "":
            await thinking.delete()
            await ctx.send("No output text. Probably an error.")
            return

        text = f"{author.mention}: {text} \n \n AI: {response.output_text}"
        console.print(text)
        await thinking.edit(content=text)

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
    console.print("AI cog loaded.")