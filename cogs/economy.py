from .utils.database import db

async def update_tables():
    # Just remaking the database schema lmao
    # Max balance is 999,999,999,999.99
    await db.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                user_id BIGINT PRIMARY KEY,
                balance numeric(15, 2) NOT NULL DEFAULT 0.00,
                money_lost numeric(15, 2) NOT NULL DEFAULT 0.00,

                last_daily TIMESTAMPTZ,
                last_worked TIMESTAMPTZ,
                last_robbed_bank TIMESTAMPTZ,
                last_robbed_user TIMESTAMPTZ,

                items JSONB NOT NULL DEFAULT '[]'::JSONB
                );
    """)
    # Remove old columns (see schemaa.sql)
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS balance""")
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS last_daily""")
    await db.execute("""ALTER TABLE users DROP COLUMN IF EXISTS last_worked""")

    # Also since this is an old bot, add the new collumns
    await db.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS pronouns TEXT""")