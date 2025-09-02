-- new schema

-- Users table
-- now directly contains the economy table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    balance INT DEFAULT 0,
    last_daily TIMESTAMP,
    last_worked TIMESTAMP
);


-- Marriages Table
CREATE TABLE marriages (
    id SERIAL PRIMARY KEY,
    user1_id REFERENCES users(user_id),
    user2_id REFERENCES users(user_id)
);
