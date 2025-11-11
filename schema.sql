-- Schema v3

-- Users table
-- now directly contains the birthday table
CREATE TABLE users (
    -- important things
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    -- pronouns
    pronouns TEXT, 
    -- birthday
    day SMALLINT NULL,
    month SMALLINT NULL,
    year SMALLINT NULL,
    timezone VARCHAR(50) NULL
);

CREATE TABLE economy (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    balance NUMERIC(15, 12) DEFAULT 0.00,
    money_lost NUMERIC(18, 2) DEFAULT 0.00,
    last_daily TIMESTAMPTZ,
    last_worked TIMESTAMPTZ,
    last_robbed_bank TIMESTAMPTZ,
    last_robbed_user TIMESTAMPTZ,
    rebirths INT NOT NULL DEFAULT 0
);

-- Marriages Table
CREATE TABLE marriages (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT REFERENCES users(user_id),
    user2_id BIGINT REFERENCES users(user_id)
);

