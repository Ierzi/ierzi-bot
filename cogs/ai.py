import os
from rich.console import Console
from discord.ext import commands
import discord
from openai import AsyncOpenAI
import asyncio

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
        async with ctx.typing():
            response = await client.chat.completions.create(
                model="gpt-5-mini-2025-08-07",
                messages=[
                    {"role": "system", "content": f"You're a helpful assistant that works in a Discord bot. Your goal is too answer people's questions or requests. Your user ID is {self.bot.user.id} and your name is Ierzi Bot."},
                    {"role": "user", "content": f"{author.name} asked: {text}"}
                ],
                max_tokens=2000
            )
        
            answer = response.choices[0].message.content

            splits = []
            if len(answer) > 2000:
                current_split = ""
                for character in answer:
                    current_split += character
                    if len(current_split) >= 1975 and character == " ":
                        splits.append(current_split)
                        current_split = ""

                if current_split:
                    splits.append(current_split)

        if splits:
            for split in splits:
                await ctx.send(split, allowed_mentions=discord.AllowedMentions.none())
                await asyncio.sleep(0.2)
            return
        
        output = f"{author.mention}: {text} \n \n AI: {answer}"
        self.console.print(output)
        await ctx.send(output, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def tldr(self, ctx: commands.Context):
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        reply = await ctx.channel.fetch_message(reply.message_id)
        reply_content = reply.content

        async with ctx.typing():
            client = AsyncOpenAI(api_key=self.openai_key)
            response = await client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"You're an helpful assistant that summarize messages. Make it concise but keep its meaning and the details. Your user ID is {self.bot.user.id} and your name is Ierzi Bot. Do not say anything else than the shorten text."},
                    {"role": "user", "content": f"Summarize this: {reply_content}"}
                ],
                max_tokens=200
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

        async with ctx.typing():
            client = AsyncOpenAI(api_key=self.openai_key)
            response = await client.chat.completions.create(
                model="gpt-4.1-mini-2025-04-14",
                messages=[
                    {"role": "system", "content": f"You're an helpful assistant that works in a Discord bot. Your goal is to expand short texts into a well-detailled and long explaination. Add a lot of details and complicated words. Your user ID is {self.bot.user.id} and your name is Ierzi Bot. Do not say anything else than the expanded text."},
                    {"role": "user", "content": f"Expand this: {reply_content}"}
                ],
                max_tokens=2000
            )

            expanded_text = response.choices[0].message.content

            splits = []
            if len(expanded_text) > 2000:
                splits = []
                current_split = ""
                for character in expanded_text:
                    current_split += character
                    if len(current_split) >= 1975 and character == " ":
                        splits.append(current_split)
                        current_split = ""

                if current_split:
                    splits.append(current_split)
        
        if splits:
                for split in splits:
                    await ctx.send(split, allowed_mentions=discord.AllowedMentions.none())
                    await asyncio.sleep(0.2)
                return
        
        await ctx.send(expanded_text, allowed_mentions=discord.AllowedMentions.none())


