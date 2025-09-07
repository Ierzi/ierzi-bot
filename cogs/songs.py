import aiohttp
from discord.ext import commands
from rich.console import Console
import random
import requests

SongData = tuple[str, str, str] # Song title - Album - Artist

class Songs(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.deezer_playlist_url = "https://api.deezer.com/playlist/12419865223/tracks"
        self.songs: list[SongData] = []
        self.fetch_deezer_playlist()

    def get_page(self, index: int):
        url = self.deezer_playlist_url if index == 0 else f"{self.deezer_playlist_url}?index={index * 25}"
        response = requests.get(url)
        if response.status_code != 200:
            self.console.print(f"error: {response.status_code}")
            return []
        data = response.json()
        songs = []
        for song in data['data']:
            title = song['title']
            album = song['album']['title']
            artist = song['artist']['name']
            songs.append((title, album, artist))
        return songs

    def fetch_deezer_playlist(self):
        response = requests.get(self.deezer_playlist_url)
        if response.status_code == 200:
            data = response.json()
            total_songs = data['total']
            all_songs = []
            pages = (total_songs // 25) + 1
            for page in range(pages):
                songs = self.get_page(page)
                all_songs.extend(songs)
            self.songs = all_songs
        else:
            self.console.print(f"Failed to fetch playlist: {response.status_code}")

    @commands.command()
    async def recommendation(self, ctx: commands.Context):
        """Get a random cool song from my playlist"""
        if not self.songs:
            await ctx.send("No songs available (???)")
            return
        
        song = random.choice(self.songs)
        title, album, artist = song
        await ctx.send(f"**{title}** - {album} - {artist}")
    
    @commands.command()
    async def getsong(self, ctx: commands.Context, index: int):
        """Gets a song based on an index."""
        if index > len(self.songs):
            await ctx.send(f"I don't have that many songs :sob: (only {len(self.songs):,})")
            return

        title, album, artist = self.songs[index]
        await ctx.send(f"**{title}** - {album} - {artist}")
    
    async def async_get_page(self, index: int):
        url = self.deezer_playlist_url if index == 0 else f"{self.deezer_playlist_url}?index={index * 25}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    self.console.print(f"Error while fetching playlist: {resp.status}")
                    return []
                
                data = await resp.json()
                songs = []
                for song in data['data']:
                    title = song['title']
                    album = song['album']['title']
                    artist = song['artist']['name']
                    songs.append((title, album, artist))
                return songs

    @commands.command()
    async def fetchplaylist(self, ctx: commands.Context):
        """Can only be used by Ierzi. Fetches the last songs added to my playlist."""
        user_id = ctx.author.id
        if user_id != 966351518020300841:
            await ctx.send("no.")

        async with aiohttp.ClientSession() as session:
            async with session.get(self.deezer_playlist_url) as resp:
                if resp.status != 200:
                    await ctx.send(f"Error {resp.status} :(")
                    return
                
                resp_json = await resp.json()
                total_songs = resp_json['total']
                all_songs = []
                pages = (total_songs // 25) + 1
                for page in range(pages):
                    songs = await self.async_get_page(page)
                    all_songs.extend(songs)
                
        self.songs = all_songs
        await ctx.message.add_reaction("👍")
    
    @commands.command(aliases=("pl",))
    async def playlistlength(self, ctx: commands.Context):
        """Gives how many songs are in my playlist."""
        await ctx.send(f"{format(len(self.songs), ',')} songs.")