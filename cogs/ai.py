import discord
from discord import File
from discord.ext import commands
import asyncio
import os
from groq import AsyncGroq
from openai import AsyncOpenAI
from rich.console import Console

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
                {"role": "system", "content": f"You're a helpful AI assistant working in a Discord Bot. Your user ID is {self.bot.user.id} and your name is {self.bot.user}. While responding, do not use tables. You also really really love femboys."},
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
        """Reply to a message to shorten it."""
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
            # Thank you winter
            await ctx.send("I would be more than delighted to assist you in expanding upon any concise or succinct piece of text that you may have. Please feel free to provide the brief phrase, sentence, or passage that you wish to be elaborated into a more comprehensive, detailed, and intricate explanation. Upon receiving the specific text, I shall meticulously analyze its content and context, and then proceed to craft an extended version that incorporates a richer vocabulary, complex sentence structures, and an abundance of relevant details and nuances, thereby transforming the original succinct excerpt into a thoroughly developed and intellectually engaging exposition.")
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
    
    @commands.command()
    async def aitwist(self, ctx: commands.Context):
        """Tries to twist your words to get a new meaning out of them."""
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        reply = await ctx.channel.fetch_message(reply.message_id)
        reply_content = reply.content

        async with ctx.typing():
            client = AsyncGroq(api_key=self.groq_key)
            response = await client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": "Your goal is to twist the words of messages to get a new meaning out of them. Be creative and funny."},
                    {"role": "user", "content": f"Twist this message: {reply_content}"}
                ],
            )

        output = response.choices[0].message.content
        await ctx.send(output, allowed_mentions=discord.AllowedMentions.none())


    # # @commands.command()
    # # async def aivid(self, ctx: commands.Context, *, text: str):
    #     """Generate a video from a text."""
    #     # Doing this with aiohttp
    #     # cause yeah asyncopenai is weird
    #     async with ctx.typing():
    #         url = "https://api.openai.com/v1/videos"
    #         headers = {
    #             "Authorization": f"Bearer {self.openai_key}",
    #         }

    #         data = {
    #             "model": "sora-2",
    #             "prompt": text
    #         }

    #         async with aiohttp.ClientSession() as session:
    #             async with session.post(url, headers=headers, json=data) as r:
    #                 self.console.print(r.status)
    #                 if r.status != 200:
    #                     await ctx.send("Error generating video.")
    #                     self.console.print("Error generating video.")
    #                     self.console.print(await r.text())
    #                     return
                    
    #                 response_json = await r.json()
    #                 video_id = response_json["id"]
    #                 self.console.print("Got video ID")
    #                 self.console.print(f"Video ID: {video_id}")
                
    #             # Create an embed here to stop the bot from typing
    #             embed = Embed(
    #                 title=f"Video: {text}" if len(text) < 128 else f"Video: {text[:128]}...",
    #                 description="Generating video...",
    #                 color=discord.Color.red()
    #             )

    #             message = await ctx.send(embed=embed)

    #             # Poll for status
    #             status_url = f"{url}/{video_id}"
    #             while True:
    #                 await asyncio.sleep(10)
    #                 async with session.get(status_url, headers=headers) as s:
    #                     self.console.print("pinging...")
    #                     if s.status != 200:
    #                         embed.description = "Video generation failed :("
    #                         await message.edit(embed=embed)
    #                         self.console.print("error :(")
    #                         self.console.print(await s.text())
    #                         return

    #                     s_json = await s.json()
    #                     status = s_json["status"]
    #                     self.console.print("Job status:", status)
    #                     embed.description = f"Video generation status: {status}"
    #                     await message.edit(embed=embed)
    #                     if status in ("completed", "failed"):
    #                         self.console.print("Got status")
    #                         break

    #             if status != "completed":
    #                 self.console.print(f"Video generation didnt succeed: {s_json}")
    #                 embed.description = "Video generation failed :("
    #                 await message.edit(embed=embed)
    #                 return
                
    #             # Get video
    #             video_url = f"{status_url}/content"
    #             async with session.get(video_url, headers=headers) as v:
    #                 if v.status != 200:
    #                     embed.description = "Video generation failed :("
    #                     await message.edit(embed=embed)
    #                     self.console.print("Error getting video.")
    #                     self.console.print(v.status)
    #                     self.console.print(await v.text())
    #                     return
                    
    #                 video = await v.read()
    #                 self.console.print("Got video")

    #             async with aiofiles.open(f"{video_id}.mp4", "wb") as f:
    #                 await f.write(video)
                
    #             self.console.print(f"Video saved to {video_id}.mp4")

    #             embed.description = "Video generated successfully!"
    #             await message.edit(embed=embed)
    #             await message.reply(file=File(f"{video_id}.mp4"))
    #             os.remove(f"{video_id}.mp4")


    async def isthistrue(self, ctx: commands.Context, fact_checked_mess: str):
        # Using Groq cause it fast
        client = AsyncGroq(api_key=self.groq_key)

        await ctx.typing()
        response = await client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You're a helpful AI assistant that works in a Discord bot. Your goal is to tell if a message is true or not."},
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
                {"role": "system", "content": "You're a helpful AI assistant that works in a Discord bot. Your goal is to tell if a message is true or not."},
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