# Ierzi Bot

random discord bot i made

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/4c7d5176352e4378afd8e549c04a28ca)](https://app.codacy.com/gh/Ierzi/ierzi-bot/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

hi abby

## Run it locally

Needs Python 3.14, a Discord bot token, and Postgres.

```sh
# 1. Postgres (Arch; use your distro's equivalent otherwise)
sudo pacman -S --needed postgresql
initdb -D ~/pgdata -E UTF8
pg_ctl -D ~/pgdata -l ~/pgdata/logfile start
createdb ierzibot
psql -d ierzibot -f schema.sql

# 2. Bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set TOKEN, keep DATABASE_URL as-is for the DB above
python __main__.py
```

Only `TOKEN` and the database are required. Every other key in
`.env.example` is optional and just enables extra commands (AI, search,
songs, …) — the bot runs without them.
