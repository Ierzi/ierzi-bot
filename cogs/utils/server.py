from fastapi import FastAPI
from pydantic import BaseModel
from cogs.utils.database import db
import os

app = FastAPI()
secret_key = os.getenv("SERVER_SECRET_KEY")

class LastFMData(BaseModel):
    discord_id: int
    username: str
    session_key: str

@app.post("/callback/last-fm")
async def get_lastfm_data(data: LastFMData):
    try:
        await db.execute("""
            INSERT INTO users (user_id, lastfm_username, session_key)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET lastfm_username = $2, session_key = $3
        """, data.discord_id, data.username, data.session_key)

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

