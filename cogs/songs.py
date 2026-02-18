from discord import Embed, Interaction
from discord.ext import commands
from discord.ui import Button, View

from .utils.database import db
from .utils.variables import login_sessions

import aiohttp
from async_lru import alru_cache
import os
import random
import requests
from rich.console import Console
import string
from urllib.parse import urlencode

SongData = tuple[str, str, str] # Song title - Album - Artist
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

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
    
    @alru_cache()
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
    
    #TODO: Come back to this after adding an api route to get the session key and username
    # Idk how to do that lmao
    @commands.command(aliases=("llfm",))
    async def loginlastfm(self, ctx: commands.Context):
        if not LASTFM_API_KEY:
            await ctx.send("stupid ass ierzi forgot to add his environment variable")
            return
        
        state = "aaaaaaaaaaaa"
        while state in login_sessions:
            # Regenerate a new state
            state = str(random.choices(string.ascii_letters + string.digits, k=12))
            self.console.print(state)

        args = {
            "api_key": LASTFM_API_KEY,
            "cb": f"{self.bot.railway_url}/callback/last-fm/{urlencode(state)}",
        }

        login_link = f"http://www.last.fm/api/auth/?{urlencode(args)}"
        self.console.print(login_link)

        login_embed = Embed(
            colour=13963271, # lastfm red
            title="Login to Last.fm",
            description=f"{ctx.author.mention}, to use last.fm related commands, you need to add your last.fm account. Click on the button below to log in."
        )

        login_button = Button(label="Connect Last.fm account")
        view = View(timeout=300)

        async def login_button_callback(interaction: Interaction):
            if not interaction.user.id == ctx.author.id:
                await interaction.response.send_message("this is not your button vro :broken_heart:", ephemeral=True)
                return
            
            login_button.label = "Logging in..."
            login_button.disabled = True
            await interaction.response.send_message(f"{login_link}", ephemeral=True)
        
        login_button.callback = login_button_callback
        view.add_item(login_button)
        await ctx.send(embed=login_embed, view=view)

    @commands.command()
    async def checklogin(self, ctx: commands.Context):
        """Checks if the user is logged in to last.fm"""
        result = await db.fetchval("SELECT lastfm_username FROM users WHERE user_id = $1", ctx.author.id)
        self.console.print(result)
        if result:
            await ctx.send("yes")
        else:
            await ctx.send("no")

async def setup():
    await db.execute("ALTER TABLE users ADD COLUMN lastfm_username VARCHAR(255) NULL, ADD COLUMN session_key VARCHAR(255) NULL;")
    