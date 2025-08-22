import os
from rich.console import Console
from discord.ext import commands
import discord
from openai import AsyncOpenAI

console = Console()

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.console = Console()
        self.openai_key = os.getenv("OPENAI_KEY")
    
    @commands.command()
    async def aiask(self, ctx: commands.Context, *, text: str):
        author = ctx.author
        
        client = AsyncOpenAI(api_key=self.openai_key)
        response = await client.responses.create(
            model="gpt-5-mini-2025-08-07",
            input=text,
            max_output_tokens=2000
        )
        
        if response.error:
            console.print(response.error)
            await ctx.send("There was an error while generating the response.")
            return
        if response.output_text == "":
            await ctx.send("No output text. Probably an error.")
            return

        text = f"{author.mention}: {text} \n \n AI: {response.output_text}"
        console.print(text)
        await ctx.send(text, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def tldr(self, ctx: commands.Context):
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        reply = await ctx.channel.fetch_message(reply.message_id)
        reply_content = reply.content

        client = AsyncOpenAI(api_key=self.openai_key)
        response = await client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": "You're an helpful assistant that summarize messages. Make it concise but keep its meaning and the details."},
                {"role": "user", "content": f"Summarize this: {reply_content}"}
            ],
            max_tokens=100
        )

        summary = response.choices[0].message.content
        await ctx.send(summary, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def tsmr(self, ctx: commands.Context):
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        reply = await ctx.channel.fetch_message(reply.message_id)
        reply_content = reply.content

        client = AsyncOpenAI(api_key=self.openai_key)
        response = await client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": "You're an helpful assistant that expands short texts into a well-detained and long explaination. Add a lot of details and complicated words."},
                {"role": "user", "content": f"Expand this: {reply_content}"}
            ],
            max_tokens=2500
        )

        expanded_text = response.choices[0].message.content
        await ctx.send(expanded_text, allowed_mentions=discord.AllowedMentions.none())

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
    console.print("AI cog loaded.")