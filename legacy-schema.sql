-- Ierzi Bot Database Schema
-- inspired by https://github.com/milenakos/cat-bot/blob/main/schema.sql
-- might be useful one day idfk

-- Marriages
CREATE TABLE marriages (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL
);

-- Economy
CREATE TABLE economy (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    balance INT, 
    last_worked TIMESTAMP,
    last_daily TIMESTAMP
);

-- Economy Items
-- on 2nd thought this table is useless ill delete it later

-- Other
CREATE TABLE other (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE,
    json_data JSON
) -- Might rework this too to have dedicated categories like cat bot
  -- thank you cat bot for existing
  