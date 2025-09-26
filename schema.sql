-- new schema

-- Users table
-- now directly contains the economy table
CREATE TABLE users (
    -- important things
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    -- pronouns
    pronouns TEXT, 
    -- economy related
    balance INT DEFAULT 0,
    last_daily TIMESTAMPTZ,
    last_worked TIMESTAMPTZ,
    last_robbed_bank TIMESTAMPTZ,
    last_robbed_user TIMESTAMPTZ
);


-- Marriages Table
CREATE TABLE marriages (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT REFERENCES users(user_id),
    user2_id BIGINT REFERENCES users(user_id)
);
