from discord import Embed, File, Interaction
from discord.ext import commands
from discord.ui import Button, View

from .utils.database import db

import aiohttp
import asyncio
from async_lru import alru_cache
import hashlib
import os
import random
import requests
from rich.console import Console
import xml.etree.ElementTree as ET

SongData = tuple[str, str, str] # Song title - Album - Artist
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def sign(params: dict, api_secret: str) -> str:
    params_for_sig = {k: v for k, v in params.items() if k != 'format'}
    signature_string = "".join(f"{k}{str(v)}" for k, v in sorted(params_for_sig.items())) + api_secret
    return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

class Songs(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.deezer_playlist_url = "https://api.deezer.com/playlist/12419865223/tracks"
        self.songs: list[SongData] = []
        self.fetch_deezer_playlist()
        self.blindtest_pages: dict[int, int] = {} # user_id -> page number 

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

        args = {
            "method": "auth.gettoken",
            "api_key": LASTFM_API_KEY,
            "format": "json"
        }

        base_url = "http://ws.audioscrobbler.com/2.0/"

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=args) as response:
                try:
                    response.raise_for_status()
                except Exception as e:
                    self.console.print(e)
                    await ctx.send("error :(")
                
                json_response: dict = await response.json()
                token = json_response.get("token")

        login_link = f"http://www.last.fm/api/auth/?api_key={LASTFM_API_KEY}&token={token}"

        self.console.print(login_link)

        login_embed = Embed(
            colour=0xD51007, # lastfm red
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

            # Ping the server every 5 seconds to check if the user has authenticated
            # 60 seconds / 5 = 12, so 12 attempts

            args = {
                "method": "auth.getSession",
                "api_key": LASTFM_API_KEY,
                "token": token
            }

            # Sign call
            args["api_sig"] = sign(args, os.getenv("LASTFM_API_SECRET"))

            for _ in range(12):
                await asyncio.sleep(5)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url}", params=args) as response:
                        try:
                            response.raise_for_status()
                        except Exception as e:
                            self.console.print(e)
                            continue
                        
                        data = await response.text()
                        xml = ET.fromstring(data)
                        status = xml.attrib.get("status")

                        if status == "ok":
                            sk = xml.find("session/key").text
                            name = xml.find("session/name").text

                            # Save the session key and username to the database
                            await db.execute("""
                                INSERT INTO users (user_id, lastfm_username, session_key)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (user_id) DO UPDATE SET lastfm_username = EXCLUDED.lastfm_username, session_key = EXCLUDED.session_key
                            """, ctx.author.id, name, sk)

                            login_button.label = "Logged in!"
                            self.console.print(f"{ctx.author} logged in.")
                            await interaction.edit_original_response(content="You are logged in!", view=view)
                            return
                        else:
                            await ctx.send("Error :(")
        
        login_button.callback = login_button_callback
        view.add_item(login_button)
        await ctx.send(embed=login_embed, view=view)

    async def _is_authenticated(self, user_id: int) -> bool:
        result = await db.fetchval("SELECT session_key FROM users WHERE user_id = $1", user_id)
        return result is not None

    @commands.command()
    async def checklogin(self, ctx: commands.Context):
        """Checks if the user is logged in to last.fm"""
        result = await self._is_authenticated(ctx.author.id)
        if result:
            await ctx.send("yes")
        else:
            await ctx.send("no")
    
    @commands.command()
    async def logoutlastfm(self, ctx: commands.Context):
        """Logs out the user from last.fm (deletes session key and username from database)"""
        await db.execute("UPDATE users SET lastfm_username = NULL, session_key = NULL WHERE user_id = $1", ctx.author.id)
        await ctx.send("Logged out.")
    
    @commands.command(aliases=("bt",))
    async def blindtest(self, ctx: commands.Context):
        """Gives a random song, and you have to guess its name."""
        # TODO: Add this
        # The Deezer API gives a preview of the song, which is a 30 second clip.
        # Like .px, add a button to shuffle name song, give up, and play again
        # Prolly implement an algorithm to accept an answer if it's close enough to the actual name
        # Add hints? 

        # 1. Check if user is authenticated
        is_auth = await self._is_authenticated(ctx.author.id)
        if not is_auth:
            await ctx.send("You didn't connect your last.fm account yet! Use !loginlastfm.")
            return
    
        # Get a random song from their listening history
        username = await db.fetchval("SELECT lastfm_username FROM users WHERE user_id = $1", ctx.author.id)
        args = {
            "method": "user.getrecenttracks",
            "user": username,
            "api_key": LASTFM_API_KEY,
            "format": "json",
            "limit": 200
        }

        if self.blindtest_pages.get(ctx.author.id) is not None:
            # Get a random page
            max_pages = self.blindtest_pages[ctx.author.id]
            random_page = random.randint(0, max_pages)
            args["page"] = random_page

        async with aiohttp.ClientSession() as session:
            async with session.get("http://ws.audioscrobbler.com/2.0/", params=args, timeout=30) as response:
                try:
                    response.raise_for_status()
                except Exception as e:
                    self.console.print(e)
                    await ctx.send("error :(")
                    return
                
                data = await response.json()
                tracks = data.get("recenttracks", {}).get("track", [])
                if not tracks:
                    await ctx.send("no tracks???")
                    return

                if args.get("page") is None:
                    # Save the number of pages for later
                    attr = data.get("recenttracks", {}).get("@attr", {})
                    total_pages = int(attr.get("totalPages", 0))
                    self.blindtest_pages[ctx.author.id] = total_pages
                
            tracks = [t for t in tracks if "date" in t]
            random_track = random.choice(tracks)

            song_name = random_track.get("name")
            artist_name = random_track.get("artist", {}).get("#text", "")
            
            # Ask deezer for a preview
            query = f"{song_name} {artist_name}"
            url = f"https://api.deezer.com/search?q={query}"

            async with session.get(url, timeout=30) as response:
                try:
                    response.raise_for_status()
                except Exception as e:
                    self.console.print(e)
                    await ctx.send("error :(")
                    return
                
                data = await response.json()
                results = data.get("data", [])
                if not results:
                    await ctx.send("error :(")
                    self.console.print("No results from Deezer for query: {query}")
                    return
                
                preview_url = results[0].get("preview")
                if not preview_url:
                    await ctx.send("error :(")
                    self.console.print("No preview available for song {song_name} by {artist_name}")
                    return
                
            # test send
            # await ctx.send(f"{preview_url}")

            # Download song
            async with session.get(preview_url) as response:
                try:
                    response.raise_for_status()
                except Exception as e:
                    self.console.print(e)
                    await ctx.send("error :(")
                    return
                
                song_data = await response.read()
                # Make file name original
                filename = f"{song_name}_{artist_name}.mp3"
                with open(filename, "wb") as f:
                    f.write(song_data)

            await ctx.send(file=File(filename))
    
    # Maybe add pixel jumble but unlimited? ion wanna pay for .fmbot supporter

async def setup():
    await db.execute("ALTER TABLE users ADD COLUMN lastfm_username VARCHAR(255) NULL, ADD COLUMN session_key VARCHAR(255) NULL;")
    