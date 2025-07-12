-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user_levels table
CREATE TABLE IF NOT EXISTS user_levels (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    last_message_time TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create level_rewards table
CREATE TABLE IF NOT EXISTS level_rewards (
    level INTEGER PRIMARY KEY,
    reward_description TEXT NOT NULL,
    role_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some default level rewards
INSERT INTO level_rewards (level, reward_description) VALUES
    (50, 'Access to rutracker.org and bot search 🔍'),
    (75, 'Exclusive "Active Member" role 🌟'),
    (100, 'Ability to create custom role 👑'),
    (175, 'VIP status 💎'),
    (225, 'Special "Server Legend" role 🏆'),
    (250, 'Ability to pin messages 📌'),
    (275, 'Special "Server Star" role 🌠'),
    (300, 'Right to create personal channel 🏰'),
    (325, 'Immunity to slow mode ⚡'),
    (350, 'Search IP 🔍'),
    (375, 'Exclusive "Server Guardian" title 👨‍💼'),
    (400, 'All previous rewards + special "Emperor" status 👑'),
    (500, 'Chat moderator status 🛡️');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_levels_level ON user_levels(level);
CREATE INDEX IF NOT EXISTS idx_user_levels_xp ON user_levels(xp); 