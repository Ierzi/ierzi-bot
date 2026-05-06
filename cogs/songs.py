from discord import Embed, File, Interaction, Message
from discord.ext import commands
from discord.ui import Button, View

from .utils.database import db
from .utils.variables import LONGER_VIEW_TIMEOUT

import aiohttp
import asyncio
from async_lru import alru_cache
import cv2
from difflib import SequenceMatcher
import hashlib
import os
import random
import requests
from rich.console import Console
import xml.etree.ElementTree as ET

SongData = tuple[str, str, str]  # Song title - Album - Artist
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")


def sign(params: dict, api_secret: str) -> str:
    params_for_sig = {k: v for k, v in params.items() if k != "format"}
    signature_string = (
        "".join(f"{k}{str(v)}" for k, v in sorted(params_for_sig.items())) + api_secret
    )
    return hashlib.md5(signature_string.encode("utf-8")).hexdigest()


class Songs(commands.Cog):
    def __init__(self, bot: commands.Bot, console: Console):
        self.bot = bot
        self.console = console
        self.deezer_playlist_url = "https://api.deezer.com/playlist/12419865223/tracks"
        self.songs: list[SongData] = []
        self.fetch_deezer_playlist()
        self.user_listening_pages: dict[int, int] = {}  # user_id -> page number
        self.active_games = []

    def get_page(self, index: int):
        url = (
            self.deezer_playlist_url
            if index == 0
            else f"{self.deezer_playlist_url}?index={index * 25}"
        )
        response = requests.get(url)
        if response.status_code != 200:
            self.console.print(f"error: {response.status_code}")
            return []
        data = response.json()
        songs = []
        for song in data["data"]:
            title = song["title"]
            album = song["album"]["title"]
            artist = song["artist"]["name"]
            songs.append((title, album, artist))
        return songs

    def _flag_from_country(self, country: str) -> str:
        if not country:
            return ""

        code = country.strip()
        if len(code) == 2 and code.isalpha():
            code = code.upper()
            return "".join(chr(ord(letter) + 0x1F1E6 - ord("A")) for letter in code)

        return country

    def _format_number(self, value: int) -> str:
        try:
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return str(value)

    def _make_hints(self, track_info: dict, artist_name: str) -> dict[str, str]:
        album_name = track_info.get("album", {}).get("title")
        release_date = track_info.get("wiki", {}).get("published")
        raw_tag = track_info.get("toptags", {}).get("tag")
        if isinstance(raw_tag, list) and raw_tag:
            genre = raw_tag[0].get("name")
        elif isinstance(raw_tag, dict):
            genre = raw_tag.get("name")
        else:
            genre = None

        duration = None
        raw_duration = track_info.get("duration")
        if raw_duration is not None:
            try:
                duration = int(raw_duration) // 1000
            except (TypeError, ValueError):
                duration = None

        listeners = track_info.get("listeners")
        playcount = track_info.get("playcount")
        artist_country = track_info.get("artist", {}).get("country")
        artist_flag = self._flag_from_country(artist_country) if artist_country else None

        raw_hints = {
            "duration": duration,
            "genre": genre,
            "artist_country": artist_flag,
            "popularity": listeners,
            "playcount": playcount,
            "release_date": release_date,
            "album_name": album_name,
            "artist_name": artist_name,
        }

        formatted_hints = {}
        for key, value in raw_hints.items():
            if value is None:
                continue

            if key == "duration":
                formatted_hints[key] = f"This track lasts {value} seconds."
            elif key == "genre":
                formatted_hints[key] = f"It belongs to the {value} genre."
            elif key == "artist_country":
                formatted_hints[key] = f"The artist is from {value}."
            elif key == "popularity":
                formatted_hints[key] = f"It has about {self._format_number(value)} listeners on Last.fm."
            elif key == "playcount":
                formatted_hints[key] = f"This track has been played {self._format_number(value)} times."
            elif key == "release_date":
                formatted_hints[key] = f"It was released on {value}."
            elif key == "album_name":
                formatted_hints[key] = f"The album is called {value}."
            elif key == "artist_name":
                formatted_hints[key] = f"The artist is {value}."
            else:
                formatted_hints[key] = str(value)

        hint_order = [
            "duration",
            "genre",
            "artist_country",
            "popularity",
            "playcount",
            "release_date",
            "album_name",
            "artist_name",
        ]

        return {key: formatted_hints[key] for key in hint_order if key in formatted_hints}

    def fetch_deezer_playlist(self):
        response = requests.get(self.deezer_playlist_url)
        if response.status_code == 200:
            data = response.json()
            total_songs = data["total"]
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
        preview = None

        # Fetch a preview from Deezer
        query = f"{title} {artist}"
        url = f"https://api.deezer.com/search?q={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    await ctx.send(f"Error fetching preview: {response.status}")
                else:
                    data = await response.json()
                    results = data.get("data", [])
                    if results:
                        preview_url = results[0].get("preview")
                        if preview_url:
                            async with session.get(preview_url) as response:
                                try:
                                    response.raise_for_status()
                                except Exception as e:
                                    self.console.print(e)
                                    await ctx.send("error :(")
                                    return

                                song_data = await response.read()
                                # Make file name original
                                preview = f"{title}_{artist}.mp3"
                                with open(preview, "wb") as f:
                                    f.write(song_data)
                        else:
                            self.console.print(
                                f"No preview available for {title} by {artist}"
                            )
                    else:
                        self.console.print(f"No results from Deezer for query: {query}")

        if preview:
            await ctx.send(
                f"**{title}** - {album} - {artist}",
                file=File(preview, filename="preview.mp3"),
            )
        else:
            await ctx.send(f"**{title}** - {album} - {artist}")

    @commands.command()
    async def getsong(self, ctx: commands.Context, index: int):
        """Gets a song based on an index."""
        if index > len(self.songs):
            await ctx.send(
                f"I don't have that many songs :sob: (only {len(self.songs):,})"
            )
            return

        title, album, artist = self.songs[index]
        preview = None

        # Fetch a preview from Deezer
        query = f"{title} {artist}"
        url = f"https://api.deezer.com/search?q={query}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    await ctx.send(f"Error fetching preview: {response.status}")
                else:
                    data = await response.json()
                    results = data.get("data", [])
                    if results:
                        preview_url = results[0].get("preview")
                        if preview_url:
                            async with session.get(preview_url) as response:
                                try:
                                    response.raise_for_status()
                                except Exception as e:
                                    self.console.print(e)
                                    await ctx.send("error :(")
                                    return

                                song_data = await response.read()
                                # Make file name original
                                preview = f"{title}_{artist}.mp3"
                                with open(preview, "wb") as f:
                                    f.write(song_data)
                        else:
                            self.console.print(
                                f"No preview available for {title} by {artist}"
                            )
                    else:
                        self.console.print(f"No results from Deezer for query: {query}")

        if preview:
            await ctx.send(
                f"**{title}** - {album} - {artist}",
                file=File(preview, filename="preview.mp3"),
            )
        else:
            await ctx.send(f"**{title}** - {album} - {artist}")

    @alru_cache()
    async def async_get_page(self, index: int):
        url = (
            self.deezer_playlist_url
            if index == 0
            else f"{self.deezer_playlist_url}?index={index * 25}"
        )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    self.console.print(f"Error while fetching playlist: {resp.status}")
                    return []

                data = await resp.json()
                songs = []
                for song in data["data"]:
                    title = song["title"]
                    album = song["album"]["title"]
                    artist = song["artist"]["name"]
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
                total_songs = resp_json["total"]
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

    @commands.command(aliases=("llfm",))
    async def loginlastfm(self, ctx: commands.Context):
        """Connect Ierzi Bot to your last.fm account."""
        if not LASTFM_API_KEY:
            await ctx.send("stupid ass ierzi forgot to add his environment variable")
            return

        args = {"method": "auth.gettoken", "api_key": LASTFM_API_KEY, "format": "json"}

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

        login_link = (
            f"http://www.last.fm/api/auth/?api_key={LASTFM_API_KEY}&token={token}"
        )

        self.console.print(login_link)

        login_embed = Embed(
            colour=0xD51007,  # lastfm red
            title="Login to Last.fm",
            description=f"{ctx.author.mention}, to use last.fm related commands, you need to add your last.fm account. Click on the button below to log in.",
        )

        login_button = Button(label="Connect Last.fm account")
        view = View(timeout=300)

        async def login_button_callback(interaction: Interaction):
            if not interaction.user.id == ctx.author.id:
                await interaction.response.send_message(
                    "this is not your button vro :broken_heart:", ephemeral=True
                )
                return

            login_button.label = "Logging in..."
            login_button.disabled = True

            await interaction.response.send_message(f"{login_link}", ephemeral=True)

            # Ping the server every 5 seconds to check if the user has authenticated
            # 180 seconds / 10 = 18, so 18 attempts

            args = {
                "method": "auth.getSession",
                "api_key": LASTFM_API_KEY,
                "token": token,
            }

            # Sign call
            args["api_sig"] = sign(args, os.getenv("LASTFM_API_SECRET"))

            for _ in range(36):
                await asyncio.sleep(10)
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
                            await db.execute(
                                """
                                INSERT INTO users (user_id, lastfm_username, session_key)
                                VALUES ($1, $2, $3)
                                ON CONFLICT (user_id) DO UPDATE SET lastfm_username = EXCLUDED.lastfm_username, session_key = EXCLUDED.session_key
                            """,
                                ctx.author.id,
                                name,
                                sk,
                            )

                            login_button.label = "Logged in!"
                            self.console.print(f"{ctx.author} logged in.")
                            await interaction.edit_original_response(
                                content="You are logged in!", view=view
                            )
                            return
                        else:
                            await ctx.send("Error :(")

        login_button.callback = login_button_callback
        view.add_item(login_button)
        await ctx.send(embed=login_embed, view=view)

    async def _is_authenticated(self, user_id: int) -> bool:
        result = await db.fetchval(
            "SELECT session_key FROM users WHERE user_id = $1", user_id
        )
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
        """Logs you out from last.fm"""
        await db.execute(
            "UPDATE users SET lastfm_username = NULL, session_key = NULL WHERE user_id = $1",
            ctx.author.id,
        )
        await ctx.send("Logged out.")

    # TODO: Add win streaks
    @commands.command(aliases=("blindtest", "bt", "mj"))
    async def musicjumble(self, ctx: commands.Context):
        """Guess the name of a random song from your listening history."""

        # * Check if user is authenticated
        is_auth = await self._is_authenticated(ctx.author.id)
        if not is_auth:
            await ctx.send(
                "You didn't connect your last.fm account yet! Use !loginlastfm."
            )
            return

        # * Check if there isnt another game in this channel already
        channel_id = ctx.channel.id
        if channel_id in self.active_games:
            await ctx.message.reply(
                "There is already a game in this channel!",
                mention_author=False,
            )
            return

        self.active_games.append(channel_id)

        async with ctx.typing():
            # * Get a random song from their listening history
            username = await db.fetchval(
                "SELECT lastfm_username FROM users WHERE user_id = $1", ctx.author.id
            )
            args = {
                "method": "user.getRecentTracks",
                "user": username,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "limit": 200,
            }

            if self.user_listening_pages.get(ctx.author.id) is not None:
                # Get a random page
                max_pages = self.user_listening_pages[ctx.author.id]
                random_page = random.randint(1, max_pages)
                args["page"] = random_page

            # * REQUESTS
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://ws.audioscrobbler.com/2.0/", params=args, timeout=30
                ) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        self.console.print(e)
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return

                    data = await response.json()
                    tracks = data.get("recenttracks", {}).get("track", [])
                    if not tracks:
                        await ctx.send("no tracks???")
                        return

                    if args.get("page") is None:
                        # Save the number of pages for later
                        attr = data.get("recenttracks", {}).get("@attr", {})
                        total_pages = int(attr.get("totalPages", 1))
                        self.user_listening_pages[ctx.author.id] = total_pages

                tracks = [t for t in tracks if "date" in t]
                random_track = random.choice(tracks)

                song_name = str(random_track.get("name"))
                artist_name = str(random_track.get("artist", {}).get("#text", ""))
                mbid = random_track.get("mbid")
                if not mbid:
                    self.console.print(f"No mbid for {song_name} by {artist_name}")

                # * Get some info about the song (for hints)
                hints_args = {
                    "method": "track.getInfo",
                    "api_key": LASTFM_API_KEY,
                    "format": "json",
                }
                if mbid:
                    hints_args["mbid"] = mbid
                else:
                    hints_args["artist"] = artist_name
                    hints_args["track"] = song_name

                async with session.get(
                    "http://ws.audioscrobbler.com/2.0/", params=hints_args, timeout=30
                ) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        self.console.print(e)
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return

                    data = await response.json()
                    track_info = data.get("track", {})
                    # await ctx.send(track_info if len(track_info) < 2000 else "track info too long")
                    if not track_info:
                        self.console.print(
                            f"No track info for {song_name} by {artist_name}"
                        )
                        self.console.print("no hints")

                    hints = self._make_hints(track_info, artist_name)
                    hints.pop("album_name")

                # * Ask deezer for a preview
                query = f"{song_name} {artist_name}"
                self.console.print(query)  # If i dont guess the song for debugging
                url = f"https://api.deezer.com/search?q={query}"
                # await ctx.send(url)

                async with session.get(url, timeout=30) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        self.console.print(e)
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return

                    data = await response.json()
                    results = data.get("data", [])
                    if not results:
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        self.console.print(f"No results from Deezer for query: {query}")
                        return

                    for result in results:
                        result_artist = result.get("artist", {}).get("name", "").lower()
                        if result_artist == artist_name.lower():
                            preview_url = result.get("preview")
                            if preview_url:
                                break

                    if not preview_url:
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        self.console.print(
                            f"No preview available for song {song_name} by {artist_name}"
                        )
                        return

                # test send
                # await ctx.send(f"{preview_url}")

                # * Download song
                async with session.get(preview_url) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        self.console.print(e)
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return

                    song_data = await response.read()
                    # Make file name original
                    filename = f"{song_name}_{artist_name}.mp3"
                    with open(filename, "wb") as f:
                        f.write(song_data)

        # * Make embed
        given_hints = []
        title = "Blind Test - Guess the song "
        hints_text = "\n"
        hints_index = 0
        embed = Embed(
            title="",  # Make title appear when shuffle song name
            description=f"{title}\n{hints_text}",
            colour=0xD51007,  # lastfm red
        )
        game_state = {"active": True, "guessed": False}

        view = View(timeout=75)

        # * Button callbacks
        async def hint_button_callback(interaction: Interaction):
            nonlocal hints_text, given_hints, hints_index
            if not hints:
                await interaction.response.send_message(
                    "No more hints available :(", ephemeral=True
                )
                return

            hint_keys = list(hints.keys())
            if hints_index >= len(hint_keys):
                await interaction.response.send_message(
                    "No more hints available :(", ephemeral=True
                )
                return

            next_hint = hints[hint_keys[hints_index]]
            given_hints.append(next_hint)
            hints_index += 1

            hints_text = "\n".join(f"- {hint}" for hint in given_hints)
            embed.description = f"{title}\n{hints_text}"
            await interaction.response.edit_message(embed=embed, view=view)

        async def shuffle_button_callback(interaction: Interaction):
            nonlocal song_name
            # Shuffle the song name, but like last.fm, only shuffle the words and keep the spaces
            name_parts = song_name.upper().split()
            shuffled_name_parts = []

            for part in name_parts:
                letters = list(part)
                random.shuffle(letters)
                shuffled_name_parts.append("".join(letters))

            shuffled_name = " ".join(shuffled_name_parts)
            embed.title = f"**`{shuffled_name}`**"
            await interaction.response.edit_message(embed=embed, view=view)

        async def giveup_button_callback(interaction: Interaction):
            nonlocal game_state
            game_state["active"] = False
            embed_result = Embed(
                title="Gave up...",
                description=f"The song was **{song_name}** by **{artist_name}**",
                colour=0xD51007,
            )
            for item in view.children:
                item.disabled = True

            self.active_games.remove(channel_id)
            view_gaveup = View(timeout=LONGER_VIEW_TIMEOUT)
            view_gaveup.add_item(play_again_button)

            await interaction.response.edit_message(view=view)
            await ctx.send(embed=embed_result, view=view_gaveup)
            return

        async def play_again_callback(interaction: Interaction):
            await interaction.response.defer()

            if channel_id in self.active_games:  # There's already a game in this channel
                await interaction.followup.send(
                    "There is already a game in this channel, you can't start a new one yett",
                    ephemeral=True,
                )
                return

            self.console.print("Play again button pressed")
            play_again_button.label = f"{interaction.user.display_name} is playing again!"
            play_again_button.disabled = True

            if not interaction.user.id == ctx.author.id:
                ctx.author = interaction.user

            await interaction.followup.edit_message(
                interaction.message.id, view=play_again_button.view
            )  # Disable play again button
            await self.musicjumble(ctx)

        hint_button = Button(label="Add hint")
        shuffle_button = Button(label="Shuffle song name")
        giveup_button = Button(label="Give up")
        play_again_button = Button(label="Play again")  # Not added to view yet

        hint_button.callback = hint_button_callback
        shuffle_button.callback = shuffle_button_callback
        giveup_button.callback = giveup_button_callback
        play_again_button.callback = play_again_callback

        view.add_item(hint_button)
        view.add_item(shuffle_button)
        view.add_item(giveup_button)

        bt_message = await ctx.send(
            file=File(filename, filename="preview.mp3"), embed=embed, view=view
        )
        os.remove(filename)

        # * Main game loop - 75 seconds to guess
        def check_message(msg: Message):
            return msg.channel == ctx.channel and not msg.author.bot

        def similarity_score(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        start_time = asyncio.get_event_loop().time()
        while game_state["active"]:
            try:
                # Wait for message with 75 second timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining = 75 - elapsed

                # TODO: Gradually add hints

                if remaining <= 0:
                    # Time's up
                    game_state["active"] = False
                    embed_timeout = Embed(
                        title="Nobody guesssed it...",
                        description=f"The song was **{song_name}** by **{artist_name}**",
                        colour=0xD51007,
                    )

                    view.clear_items()
                    timeout_view = View(timeout=LONGER_VIEW_TIMEOUT)
                    timeout_view.add_item(play_again_button)
                    self.active_games.remove(channel_id)

                    await bt_message.edit(view=view)  # Disable buttons
                    await ctx.send(embed=embed_timeout, view=timeout_view)
                    break

                msg = await self.bot.wait_for(
                    "message", check=check_message, timeout=remaining
                )
                elapsed = (
                    asyncio.get_event_loop().time() - start_time
                )  # After waiting, the elapsed time changed

                # Check if answer is correct
                similarity = similarity_score(msg.content, song_name)
                if similarity >= 0.7:  # 70%
                    await msg.add_reaction("✅")
                    game_state["active"] = False
                    game_state["guessed"] = True
                    embed_correct = Embed(
                        description=f"{msg.author.mention} guessed it! The song was **{song_name}** by **{artist_name}**\n Answered in {elapsed:.1f} seconds.",
                        colour=0xD51007,
                    )

                    view.clear_items()
                    correct_view = View(timeout=LONGER_VIEW_TIMEOUT)
                    correct_view.add_item(play_again_button)
                    self.active_games.remove(channel_id)

                    await bt_message.edit(view=view)  # Disable buttons
                    await ctx.send(embed=embed_correct, view=correct_view)
                    break
                else:
                    # Wrong answer, continue
                    await msg.add_reaction("❌")

            except asyncio.TimeoutError:
                # Time's up
                if game_state["active"]:  # Doesn't trigger if user gave up
                    game_state["active"] = False
                    embed_timeout = Embed(
                        title="Nobody guesssed it...",
                        description=f"The song was **{song_name}** by **{artist_name}**",
                        colour=0xD51007,
                    )

                    view.clear_items()
                    timeout_view = View(timeout=LONGER_VIEW_TIMEOUT)
                    timeout_view.add_item(play_again_button)
                    self.active_games.remove(channel_id)

                    await bt_message.edit(view=view)  # Disable buttons
                    await ctx.send(embed=embed_timeout, view=timeout_view)
                    break


    # Maybe add pixel jumble but unlimited? ion wanna pay for .fmbot supporter
    @commands.command(aliases=("pxu", "px")) # fm.bot has a different prefix
    async def pixeljumbleunlimited(self, ctx: commands.Context): 
        """Like the game on fm.bot but you can play more than 30 games a day (for free)."""

        # * Check if user is authenticated
        is_auth = await self._is_authenticated(ctx.author.id)
        if not is_auth:
            await ctx.send(
                "You didn't connect your last.fm account yet! Use !loginlastfm."
            )
            return

        # * Check if there isnt another game in this channel already
        channel_id = ctx.channel.id
        if channel_id in self.active_games:
            await ctx.message.reply(
                "There is already a game in this channel!",
                mention_author=False,
            )
            return

        self.active_games.append(channel_id)

        async with ctx.typing():
            # * Get a random song from their listening history
            username = await db.fetchval(
                "SELECT lastfm_username FROM users WHERE user_id = $1", ctx.author.id
            )
            args = {
                "method": "user.getRecentTracks",
                "user": username,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "limit": 200,
            }

            if self.user_listening_pages.get(ctx.author.id) is not None:
                # Get a random page
                max_pages = self.user_listening_pages[ctx.author.id]
                random_page = random.randint(1, max_pages)
                args["page"] = random_page

            # * REQUESTS
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://ws.audioscrobbler.com/2.0/", params=args, timeout=30
                ) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        self.console.print(e)
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return

                    data = await response.json()
                    tracks = data.get("recenttracks", {}).get("track", [])
                    if not tracks:
                        await ctx.send("no tracks???")
                        return

                    if args.get("page") is None:
                        # Save the number of pages for later
                        attr = data.get("recenttracks", {}).get("@attr", {})
                        total_pages = int(attr.get("totalPages", 1))
                        self.user_listening_pages[ctx.author.id] = total_pages

                tracks = [t for t in tracks if "date" in t]
                random_track = random.choice(tracks)

                song_name = str(random_track.get("name"))
                artist_name = str(random_track.get("artist", {}).get("#text", ""))
                mbid = random_track.get("mbid")
                if not mbid:
                    self.console.print(f"No mbid for {song_name} by {artist_name}")

                # * Get some info about the song (for hints)
                hints_args = {
                    "method": "track.getInfo",
                    "api_key": LASTFM_API_KEY,
                    "format": "json",
                }
                if mbid:
                    hints_args["mbid"] = mbid
                else:
                    hints_args["artist"] = artist_name
                    hints_args["track"] = song_name

                async with session.get(
                    "http://ws.audioscrobbler.com/2.0/", params=hints_args, timeout=30
                ) as response:
                    try:
                        response.raise_for_status()
                    except Exception as e:
                        self.console.print(e)
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return

                    data = await response.json()
                    track_info = data.get("track", {})
                    # await ctx.send(track_info if len(track_info) < 2000 else "track info too long")
                    if not track_info:
                        self.console.print(
                            f"No track info for {song_name} by {artist_name}"
                        )
                        self.console.print("no hints")

                    # Album name
                    album_name = track_info.get("album", {}).get("title")
                    # Artist name
                    artist_name = track_info.get("artist", {}).get("name")

                    hints = self._make_hints(track_info, artist_name)
                    hints.pop("album_name")
                    hints.pop("duration")

                    # Also get the album cover art
                    album_cover = track_info.get("album", {}).get("image", [])
                    if isinstance(album_cover, list) and album_cover:
                        album_cover_url = album_cover[-1].get("#text")  # Get largest image

                    else: # Should'nt happen but just in case
                        self.console.print(f"No album cover for {song_name} by {artist_name}")
                        await ctx.send("error :(")
                        self.active_games.remove(channel_id)
                        return 
                    
                    # Download album cover
                    async with session.get(album_cover_url) as response:
                        try:
                            response.raise_for_status()
                        except Exception as e:
                            self.console.print(e)
                            await ctx.send("error :(")
                            self.active_games.remove(channel_id)
                            return

                        cover_data = await response.read()
                        cover_filename = f"{album_name}_{artist_name}_cover_999.jpg" # Non-pixelated
                        with open(cover_filename, "wb") as f:
                            f.write(cover_data)
                    
                    # Make the different pixelated versions
                    pixel_sizes = [8, 16, 32, 64, 96, 999]  # From hardest to easiest
                    pixelated_filenames = {
                        size: f"{album_name}_{artist_name}_cover_{size}.jpg"
                        for size in pixel_sizes
                    }

                    # Generate images
                    for size in pixel_sizes:
                        if size == 999: 
                            continue

                        image = cv2.imread(cover_filename)
                        height, width = image.shape[:2]
                        t = cv2.resize(image, (width // size, height // size), interpolation=cv2.INTER_LINEAR)
                        pixelated = cv2.resize(t, (width, height), interpolation=cv2.INTER_NEAREST)

                        cv2.imwrite(pixelated_filenames[size], pixelated)
                    
                    # Test send all of them
                    # for size in pixel_sizes:
                    #     await ctx.send(file=File(pixelated_filenames[size], filename=f"pixel_{size}.jpg"))
    
        # * Make embed
        given_hints = []
        title = "Pixel Jumble Unlimited - Guess the Album"
        hints_text = "\n"
        hints_index = 0
        embed = Embed(
            title="",  # Make title appear when shuffle album name
            description=f"{title}\n{hints_text}",
            colour=0xD51007,  # lastfm red
        )
        game_state = {"active": True, "guessed": False}
        pixel_size_index = 0

        view = View(timeout=75)

        # * Button callbacks
        async def hint_button_callback(interaction: Interaction):
            nonlocal hints_text, given_hints, hints_index, pixel_size_index
            if not hints:
                await interaction.response.send_message(
                    "No more hints available :(", ephemeral=True
                )
                return

            hint_keys = list(hints.keys())
            if hints_index >= len(hint_keys):
                await interaction.response.send_message(
                    "No more hints available :(", ephemeral=True
                )
                return
            
            hints_index += 1
            if hints_index % 2 == 0:
                # Unblur image
                if pixel_size_index < len(pixel_sizes) - 1:
                    pixel_size_index += 1
                    await interaction.message.edit(
                        file=File(pixelated_filenames.get(pixel_sizes[pixel_size_index]), filename="preview.jpg"), embed=embed, view=view
                    )
            else:
                next_hint = hints[hint_keys[hints_index]]
                given_hints.append(next_hint)

                hints_text = "\n".join(f"- {hint}" for hint in given_hints)
                embed.description = f"{title}\n{hints_text}"
                await interaction.response.edit_message(embed=embed, view=view)

        async def shuffle_button_callback(interaction: Interaction):
            nonlocal album_name
            # Shuffle the song name, but like last.fm, only shuffle the words and keep the spaces
            name_parts = album_name.upper().split()
            shuffled_name_parts = []

            for part in name_parts:
                letters = list(part)
                random.shuffle(letters)
                shuffled_name_parts.append("".join(letters))

            shuffled_name = " ".join(shuffled_name_parts)
            embed.title = f"**`{shuffled_name}`**"
            await interaction.response.edit_message(embed=embed, view=view)

        async def giveup_button_callback(interaction: Interaction):
            nonlocal game_state
            game_state["active"] = False
            embed_result = Embed(
                title="Gave up...",
                description=f"The album was **{album_name}** ",
                colour=0xD51007,
            )
            for item in view.children:
                item.disabled = True

            self.active_games.remove(channel_id)
            view_gaveup = View(timeout=LONGER_VIEW_TIMEOUT)
            view_gaveup.add_item(play_again_button)

            await interaction.response.edit_message(view=view)
            await ctx.send(embed=embed_result, view=view_gaveup)
            return

        async def play_again_callback(interaction: Interaction):
            await interaction.response.defer()

            if channel_id in self.active_games:  # There's already a game in this channel
                await interaction.followup.send(
                    "There is already a game in this channel, you can't start a new one yett",
                    ephemeral=True,
                )
                return

            self.console.print("Play again button pressed")
            play_again_button.label = f"{interaction.user.display_name} is playing again!"
            play_again_button.disabled = True

            if not interaction.user.id == ctx.author.id:
                ctx.author = interaction.user

            await interaction.followup.edit_message(
                interaction.message.id, view=play_again_button.view
            )  # Disable play again button
            await self.pixeljumbleunlimited(ctx)

        hint_button = Button(label="Add hint")
        shuffle_button = Button(label="Shuffle album name")
        giveup_button = Button(label="Give up")
        play_again_button = Button(label="Play again")  # Not added to view yet

        hint_button.callback = hint_button_callback
        shuffle_button.callback = shuffle_button_callback
        giveup_button.callback = giveup_button_callback
        play_again_button.callback = play_again_callback

        view.add_item(hint_button)
        view.add_item(shuffle_button)
        view.add_item(giveup_button)

        bt_message = await ctx.send(
            file=File(pixelated_filenames.get(pixel_sizes[0]), filename="preview.mp3"), embed=embed, view=view
        )

        # * Main game loop - 40 seconds to guess
        def check_message(msg: Message):
            return msg.channel == ctx.channel and not msg.author.bot

        def similarity_score(a: str, b: str) -> float:
            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        start_time = asyncio.get_event_loop().time()
        while game_state["active"]:
            try:
                # Wait for message with 40 second timeout
                elapsed = asyncio.get_event_loop().time() - start_time
                remaining = 40 - elapsed

                if remaining <= 0:
                    # Time's up
                    game_state["active"] = False
                    embed_timeout = Embed(
                        title="Nobody guesssed it...",
                        description=f"The song was **{album_name}** by **{artist_name}**",
                        colour=0xD51007,
                    )

                    view.clear_items()
                    timeout_view = View(timeout=LONGER_VIEW_TIMEOUT)
                    timeout_view.add_item(play_again_button)
                    self.active_games.remove(channel_id)

                    await bt_message.edit(view=view)  # Disable buttons
                    await ctx.send(embed=embed_timeout, view=timeout_view)
                    break

                msg = await self.bot.wait_for(
                    "message", check=check_message, timeout=remaining
                )
                elapsed = (
                    asyncio.get_event_loop().time() - start_time
                )  # After waiting, the elapsed time changed

                # Check if answer is correct
                similarity = similarity_score(msg.content, album_name)
                if similarity >= 0.7:  # 70%
                    await msg.add_reaction("✅")
                    game_state["active"] = False
                    game_state["guessed"] = True
                    embed_correct = Embed(
                        description=f"{msg.author.mention} guessed it! The album was **{album_name}** by **{artist_name}**\n Answered in {elapsed:.1f} seconds.",
                        colour=0xD51007,
                    )

                    view.clear_items()
                    correct_view = View(timeout=LONGER_VIEW_TIMEOUT)
                    correct_view.add_item(play_again_button)
                    self.active_games.remove(channel_id)

                    await bt_message.edit(view=view)  # Disable buttons
                    await ctx.send(embed=embed_correct, view=correct_view)
                    break
                else:
                    # Wrong answer, continue
                    await msg.add_reaction("❌")

            except asyncio.TimeoutError:
                # Time's up
                if game_state["active"]:  # Doesn't trigger if user gave up
                    game_state["active"] = False
                    embed_timeout = Embed(
                        title="Nobody guesssed it...",
                        description=f"The album was **{album_name}** by **{artist_name}**",
                        colour=0xD51007,
                    )

                    view.clear_items()
                    timeout_view = View(timeout=LONGER_VIEW_TIMEOUT)
                    timeout_view.add_item(play_again_button)
                    self.active_games.remove(channel_id)

                    await bt_message.edit(view=view)  # Disable buttons
                    await ctx.send(embed=embed_timeout, view=timeout_view)
                    break


    # focusjumble / zoomjumble idk

async def setup():  
    # Username and session keys
    await db.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS lastfm_username VARCHAR(255) NULL, ADD COLUMN IF NOT EXISTS session_key VARCHAR(255) NULL;"
    )

    # Win streaks
    await db.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bt_winstreak INT NULL, ADD COLUMN IF NOT EXISTS pxu_winstreak INT NULL;"
    )

    # TODO
    # Stats (number of games played, number of wins...)
    # Maybe add a leaderboard later
