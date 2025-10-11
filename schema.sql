-- new schema

-- Users table
-- now directly contains the economy table
CREATE TABLE users (
    -- important things
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    -- pronouns
    pronouns TEXT, 
);

CREATE TABLE economy (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id),
    balance NUMERIC(5, 12) DEFAULT 0.00,
    last_daily TIMESTAMPTZ,
    last_worked TIMESTAMPTZ,
    last_robbed_bank TIMESTAMPTZ,
    last_robbed_user TIMESTAMPTZ,
    items JSONB NOT NULL DEFAULT '[]'::JSONB
);

-- Marriages Table
CREATE TABLE marriages (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT REFERENCES users(user_id),
    user2_id BIGINT REFERENCES users(user_id)
);

-- Birthdays Table
CREATE TABLE birthdays (
    user_id BIGINT PRIMARY KEY, -- I kinda fucked up while making this, but it's too late to change it now
    day INT NOT NULL,
    month INT NOT NULL,
    year INT
);