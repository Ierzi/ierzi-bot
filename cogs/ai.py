from discord.ext import commands
import discord
from discord import Embed
from openai import AsyncOpenAI
from groq import AsyncGroq
import os
from rich.console import Console
import asyncio
import aiohttp
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download("punkt")
nltk.download("stopwords")
nltk.download("punkt_tab")
nltk.download("wordnet")
nltk.download('averaged_perceptron_tagger_eng')


class AI(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.openai_key = os.getenv("OPENAI_KEY")
        self.groq_key = os.getenv("GROQ_KEY")
        self.serp_key = os.getenv("SERP_KEY")
        self.console = console
        self.MANUAL_FILTER = ["yes", "no", "true", "false"]
    
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

    @commands.command()
    async def proof(self, ctx: commands.Context):
        """Looks online for proof (this is in the AI category cause it uses AI to find keywords)"""
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        _reply = await ctx.channel.fetch_message(reply.message_id)
        message = _reply.content
        self.console.print(message)

        keywords = await self._keywords(message)
        self.console.print(keywords)

        async with ctx.typing():
            search_embed = Embed(
                title="Search results",
                description=None
            )

            # Search using SERPAPI
            params = {
                "engine": "google",
                "q": keywords,
                "api_key": self.serp_key,
                "num": 3
            }
            async with aiohttp.ClientSession() as client:
                async with client.get("https://serpapi.com/search", params=params) as r:
                    response_json: dict = await r.json()
            
            self.console.print(response_json)
            result: dict
            for result in response_json.get('organic_results', []):
                title = result.get('title', 'No title')
                link = result.get('link', 'No link')
                search_embed.description += f"**{title}** - {link}\n"
        
        if search_embed.description is None:
            await ctx.send("No results found :(")
            return
        
        await ctx.send(embed=search_embed)

    # Helper commands
    async def _keywords(self, sentence: str):
        # 1. Tokenize
        words = word_tokenize(sentence.lower())

        # 2. Remove stopwords & non-alphabetic tokens
        stop_words = set(stopwords.words("english"))
        words = [w for w in words if w.isalpha() and w not in stop_words]

        # 3. Tag words
        tagged = nltk.pos_tag(words)

        # 4. Remove adjectives
        filtered = [(word, tag) for word, tag in tagged if not tag.startswith("JJ")]

        # 5. Lemmatize or whatever
        lemmatizer = WordNetLemmatizer()
        lemmatized = [lemmatizer.lemmatize(word, self._get_wordnet_pos(tag)) for word, tag in filtered]

        # 6. Remove duplicates
        uniqued = list(dict.fromkeys(lemmatized))

        # 7. Manually filter
        m_filter = [word for word in uniqued if word not in self.MANUAL_FILTER]

        return m_filter
    
    def _get_wordnet_pos(self, tag: str):
        if tag.startswith('J'):
            return wordnet.ADJ
        elif tag.startswith('V'):
            return wordnet.VERB
        elif tag.startswith('N'):
            return wordnet.NOUN
        elif tag.startswith('R'):
            return wordnet.ADV
        else:
            return wordnet.NOUN


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