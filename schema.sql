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
    last_daily TIMESTAMP,
    last_worked TIMESTAMP,
    last_robbed_bank TIMESTAMP,
    last_robbed_user TIMESTAMP
);


-- Marriages Table
CREATE TABLE marriages (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT REFERENCES users(user_id),
    user2_id BIGINT REFERENCES users(user_id)
);
