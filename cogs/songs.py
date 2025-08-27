import discord
import aiohttp
from discord.ext import commands
from rich.console import Console
import random

class Songs(commands.Cog):
    async def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.deezer_playlist_url = "https://api.deezer.com/playlist/12419865223/tracks"
        self.songs = []
        await self.fetch_deezer_playlist()

    async def get_page(self, session: aiohttp.ClientSession, index: int):
        async with session.get(self.deezer_playlist_url if index == 0 else f"{self.deezer_playlist_url}?index={index * 25}") as response:
            data = await response.json()
            if response.status != 200:
                self.console.print(f"error: {response.status}")
                return None
            
            for song in data['data']:
                title = song['title']
                album = song['album']['title']
                artist = song['artist']['name']
                return title, album, artist

    async def fetch_deezer_playlist(self):
        # Song title - Album - Artist
        async with aiohttp.ClientSession() as session:
            async with session.get(self.deezer_playlist_url) as response:
                if response.status == 200:
                    data = await response.json()
                    total_songs = data['total']
                    songs: list[tuple[str, str, str]] = []
                    pages = (total_songs // 25) + 1
                    for page in range(pages):
                        title, album, artist = await self.get_page(session, page)
                        songs.append((title, album, artist))

                else:
                    self.console.print(f"Failed to fetch playlist: {response.status}")
        
        self.songs = songs

    @commands.command()
    async def recommendation(self, ctx: commands.Context):
        """Get a random cool song from my playlist"""
        if not self.songs:
            await ctx.send("No songs available (???)")
            return
        
        song = random.choice(self.songs)
        title, album, artist = song
        await ctx.send(f"**{title}** - {album} - {artist}")