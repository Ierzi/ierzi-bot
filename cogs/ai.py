from discord.ext import commands
import discord
from discord import File
from openai import AsyncOpenAI
from groq import AsyncGroq
import os
from rich.console import Console
import asyncio


class AI(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.openai_key = os.getenv("OPENAI_KEY")
        self.groq_key = os.getenv("GROQ_KEY")
        self.serp_key = os.getenv("SERP_KEY")
        self.console = console
    
    @commands.command()
    async def aiask(self, ctx: commands.Context, *, text: str):
        """Ask something to an ai."""
        client = AsyncGroq(api_key=self.groq_key)

        await ctx.typing()
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "user", "content": text}
            ],
        )

        output = response.choices[0].message.content
        outputs = []
        if len(output) > 2000:
            current_split = ""
            for char in output:
                current_split += char
                if len(current_split) > 1850 and char == " ":
                    outputs.append(current_split)
                    current_split = ""
            
            if current_split:
                outputs.append(current_split)

        if outputs:
            for mess in outputs:
                await ctx.send(mess, allowed_mentions=discord.AllowedMentions.none())
                await asyncio.sleep(0.2)
        message = f"{ctx.author.mention} asked: {text}\n\nAI: {output}"
            
        await ctx.send(message, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def tldr(self, ctx: commands.Context):
        """Reply to a messgae to shorten it."""
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
                    {"role": "system", "content": f"You're a helpful assistant that summarize messages in a Discord Bot. Make it concise but keep its meaning. Your user ID is {self.bot.user.id} and your name is Ierzi Bot. Do not say anything else than the shorten text."},
                    {"role": "user", "content": f"Summarize this: {reply_content}"}
                ],
                max_tokens=200
            )

        summary = response.choices[0].message.content
        await ctx.send(summary, allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def tsmr(self, ctx: commands.Context):
        """Reply to a message to expand it. The opposite of tldr lmao"""
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
                    {"role": "system", "content": f"You're a helpful assistant that works in a Discord bot. Your goal is to expand short texts into a well-detailled and long explaination. Add a lot of details and complicated words. Your user ID is {self.bot.user.id} and your name is Ierzi Bot. Do not say anything else than the expanded text."},
                    {"role": "user", "content": f"Expand this: {reply_content}"}
                ],
                max_tokens=3500
            )

            expanded_text = response.choices[0].message.content

            splits = []
            if len(expanded_text) > 2000:
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

    @commands.command()
    async def aitts(self, ctx: commands.Context, *, text: str):
        """Generates audio from the input text."""
        message_id = ctx.message.id
        async with ctx.typing():
            client = AsyncOpenAI(api_key=self.openai_key)
            output_file = f"audio_{message_id}.mp3"
            async with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=text
                ) as response:
                    await response.stream_to_file(output_file)
                    self.console.print(f"Generated audio for {message_id} in {output_file}")

        await ctx.send(file=File(output_file))
        os.remove(output_file)

    # TODO: I MIGHT BE ABLE TO GENERATE VIDEOS USING OPENAI'S API
    # @commands.command()
    # async def video(self, ctx: commands.Context, *, text: str):
    #     """Generate a video from a text."""
    #     async with ctx.typing():
    #         client = AsyncOpenAI(api_key=self.openai_key)
    #         response = await client.videos.create(
    #             prompt=text
    #         )
    #         video_id = response.id
    #         self.console.print(video_id)

    #         video_download_response = await client.videos.download_contemt(
    #             video_id=video_id
    #         )
    #         self.console.print(video_download_response)
    #         content = video_download_response.read()



    async def isthistrue(self, ctx: commands.Context, fact_checked_mess: str):
        # Using Groq cause it fast
        client = AsyncGroq(api_key=self.groq_key)

        await ctx.typing()
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": f"You're a helpful AI assistant that works in a Discord bot. Your goal is to tell if a message is true or not."},
                {"role": "user", "content": f'Is this true? {fact_checked_mess}'}
            ],
        )

        output = response.choices[0].message.content
        outputs = []
        if len(output) > 2000:
            current_split = ""
            for char in output:
                current_split += char
                if len(current_split) > 1850 and char == " ":
                    outputs.append(current_split)
                    current_split = ""
        
        if outputs:
            return outputs
        
        return output

    # External commands
    async def _tldr(self, message: str):
        """TLDR but doesnt send the messages"""
        client = AsyncOpenAI(api_key=self.openai_key)
        response = await client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": f"You're a helpful assistant that summarize messages in a Discord Bot. Make it concise but keep its meaning. Your user ID is {self.bot.user.id} and your name is Ierzi Bot. Do not say anything else than the shorten text."},
                {"role": "user", "content": f"Summarize this: {message}"}
            ],
            max_tokens=200
        )

        summary = response.choices[0].message.content
        return summary
    
    async def _tsmr(self, message: str):
        """TSMR but doesnt send the messages"""
        client = AsyncOpenAI(api_key=self.openai_key)
        response = await client.chat.completions.create(
            model="gpt-4.1-mini-2025-04-14",
            messages=[
                {"role": "system", "content": f"You're a helpful assistant that works in a Discord bot. Your goal is to expand short texts into a well-detailled and long explaination. Add a lot of details and complicated words. Your user ID is {self.bot.user.id} and your name is Ierzi Bot. Do not say anything else than the expanded text."},
                {"role": "user", "content": f"Expand this: {message}"}
            ],
            max_tokens=3500
        )

        expanded_text = response.choices[0].message.content

        splits = []
        if len(expanded_text) > 2000:
            current_split = ""
            for character in expanded_text:
                current_split += character
                if len(current_split) >= 1975 and character == " ":
                    splits.append(current_split)
                    current_split = ""

            if current_split:
                splits.append(current_split)
        
        return splits if splits else expanded_text
    
    async def _isthistrue(self, fact_checked_mess: str):
        """@IerziBot is this true but it doesnt type, send messsages or require context"""
        # Using Groq cause it fast
        client = AsyncGroq(api_key=self.groq_key)

        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": f"You're a helpful AI assistant that works in a Discord bot. Your goal is to tell if a message is true or not."},
                {"role": "user", "content": f'Is this true? {fact_checked_mess}'}
            ],
        )

        output = response.choices[0].message.content
        outputs = []
        if len(output) > 2000:
            current_split = ""
            for char in output:
                current_split += char
                if len(current_split) > 1850 and char == " ":
                    outputs.append(current_split)
                    current_split = ""
        
        if outputs:
            return outputs
        
        return output