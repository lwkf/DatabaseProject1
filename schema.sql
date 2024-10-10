-- Drop the users table if it already exists
DROP TABLE IF EXISTS users;

-- Create a new users table
CREATE TABLE users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    pwd TEXT NOT NULL
);

-- Initial data
INSERT INTO users (name, email, pwd) VALUES ('admin', 'admin@admin.com', 'admINF2003');

-- Drop the comments table if it already exists
DROP TABLE IF EXISTS comments;

-- Create a new comments table
-- CREATE TABLE comments (
    
-- );

-- Drop the credits table if it already exists
DROP TABLE IF EXISTS credits;

-- Create a new Credits table
-- CREATE TABLE credits (
    
-- );

-- Initial data


-- Drop the shows table if it already exists
DROP TABLE IF EXISTS shows;

-- Create a new shows table
-- CREATE TABLE shows (
    
-- );