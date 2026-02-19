from cogs.utils.database import db
from .variables import login_sessions

from fastapi import FastAPI, Request
import os
import aiohttp
from urllib.parse import urlencode
import hashlib
import xml.etree.ElementTree as ET
from .variables import login_sessions

# TODO: Just found a way to do this without a server, when sending login link, use a button
# When button is clicked, opens the last.fm auth page and also starts a timer pinging getSession every 5 seconds to check if the user has authenticated for 120 seconds
# Like .fmbot does
# TODO: Add a public key, private key thing, for security
# TODO: Remove URLs from railway

app = FastAPI()
secret_key = os.getenv("SERVER_SECRET_KEY")
lastfm_api_key = os.getenv("LASTFM_API_KEY")
lastfm_secret_key = os.getenv("LASTFM_API_SECRET")

def sign(params: dict, api_secret: str) -> str:
    params_for_sig = {k: v for k, v in params.items() if k != 'format'}
    signature_string = "".join(f"{k}{str(v)}" for k, v in sorted(params_for_sig.items())) + api_secret
    return hashlib.md5(signature_string.encode("utf-8")).hexdigest()

@app.get("/callback/last-fm")
async def get_lastfm_data(request: Request):
    # getSession arguments
    token = request.query_params.get("token")

    if not token:
        return {"status": "error", "message": "Missing token"}
    
    args = {
        "method": "auth.getSession",
        "api_key": lastfm_api_key,
        "token": token,
    }
    # Sign API call
    args["api_sig"] = sign(args, lastfm_secret_key)

    # Make API call
    async with aiohttp.ClientSession() as session:
            async with session.get("http://ws.audioscrobbler.com/2.0/", params=args) as response:
                data = await response.text()
                xml = ET.fromstring(data)
                status = xml.attrib.get("status")

                if status != "ok":
                    error = xml.find("error")
                    if error is not None:
                        return {
                            "status": "error",
                            "code": error.attrib.get("code"),
                            "message": error.text
                        }
                    return {"status": "error", "message": "Unknown Last.fm error"}
                
                sk = xml.find("session/key").text
                name = xml.find("session/name").text

    # Get the corresponding discord ID from the state
    state = request.query_params.get("state")
    if not state or state not in login_sessions:
        return {"status": "error", "message": "Invalid state"}
    
    discord_id = login_sessions[state]

    try:
        await db.execute("""
            INSERT INTO users (user_id, lastfm_username, session_key)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET lastfm_username = $2, session_key = $3
        """, discord_id, name, sk)

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

