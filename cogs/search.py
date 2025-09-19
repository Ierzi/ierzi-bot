import discord
from discord import Embed
from discord.ext import commands
from rich.console import Console
import aiohttp
from wikipediaapi import Wikipedia
import os
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

nltk.download("punkt")
nltk.download("stopwords")
nltk.download("punkt_tab")
nltk.download("wordnet")
nltk.download('averaged_perceptron_tagger_eng')

class Search(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.wiki_wiki = Wikipedia("IerziBot (ierziytb@gmail.com)")
        self.serp_key = os.getenv("SERP_KEY")
        self.MANUAL_FILTER = ["yes", "no", "true", "false"]

    @commands.command(name="ud")
    async def urban_dictionary(self, ctx: commands.Context, *, word: str):
        """Look up the meaning of a word on the Urban Dictionary."""
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
        """Look up the meaning of a word."""
        request_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

        async with aiohttp.ClientSession() as session:
            async with session.get(request_url) as r:
                r = await r.json()
                
        # r = requests.get(request_url).json()

        try:
            meanings = r[0]['meanings']
        except Exception as e:
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
    async def wiki(self, ctx: commands.Context, *, article: str):
        """Look up something on Wikipedia (only gives the summary)."""
        page = self.wiki_wiki.page(article)
        if not page.exists():
            await ctx.send("Page doesn't exist.")
            return
        
        await ctx.send(f"{ctx.author.mention}: **{article}** \n\n{page.summary}", allowed_mentions=discord.AllowedMentions.none())

    @commands.command()
    async def links(self, ctx: commands.Context):
        """Looks online for links about the replied message."""
        reply = ctx.message.reference
        if reply is None:
            await ctx.send("You didn't reply to a message.")
            return
        
        _reply = await ctx.channel.fetch_message(reply.message_id)
        message = _reply.content
        self.console.print(message)

        keywords = await self._keywords(message)
        self.console.print(keywords)
        
        # Convert keywords list to string for search query
        if isinstance(keywords, list):
            keywords_str = " ".join(keywords)
        else:
            keywords_str = str(keywords) if keywords else ""
            
        if not keywords_str.strip():
            await ctx.send("error :(")
            return

        async with ctx.typing():
            search_embed = Embed(
                title="Search results",
                description=""
            )

            # Search using SERPAPI
            params = {
                "engine": "google",
                "q": keywords_str,
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
        
        if not search_embed.description:
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
