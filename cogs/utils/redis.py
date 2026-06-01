from typing import Callable
from redis import asyncio as aioredis
import os
import functools
import hashlib
import json
import discord
from rich.console import Console
from dotenv import load_dotenv

console = Console()

load_dotenv()

redis_url = os.getenv("REDIS_URL")
console.print(f"Connecting to Redis at {redis_url}")
client = aioredis.from_url(redis_url, decode_responses=True) 

console.print(client.ping() and "Connected to Redis successfully!" or "Failed to connect to Redis.")

def handle_args(args, kwargs):
    for arg in args:
        if isinstance(arg, (discord.User, discord.Member, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.Role, discord.Emoji, discord.Guild)):
            yield arg.id
    
    for key, value in sorted(kwargs.items()):
        if isinstance(value, (discord.User, discord.Member, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.Role, discord.Emoji, discord.Guild)):
            yield key, value.id
        else:
            yield key, value


def make_cache_key(func: Callable, args, kwargs) -> str:
    key_data = (
        func.__module__,
        func.__qualname__,
        list(handle_args(args, kwargs)),
    )
    return "cache:" + hashlib.sha256(repr(key_data).encode()).hexdigest()


def redis_cache(expire: int = 1800): # 30 minutes
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = make_cache_key(func, args, kwargs)

            if client is None:
                return await func(*args, **kwargs)

            cached = await client.get(key)
            if cached is not None:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            console.print(f"Caching result for {func.__qualname__} with key {key}")
            await client.setex(key, expire, json.dumps(result))
            return result

        async def invalidate(*args, **kwargs):
            if client is None:
                return
            key = make_cache_key(func, args, kwargs)
            console.print(f"Invalidating cache for {func.__qualname__} with key {key}")
            await client.delete(key)

        wrapper.invalidate = invalidate
        return wrapper
    return decorator
