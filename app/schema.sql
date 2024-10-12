-- Drop the users table if it already exists
DROP TABLE IF EXISTS users;

-- Create a new users table
CREATE TABLE users (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NULL,
    created_at DATETIME NOT NULL,
    admin_permissions BIGINT NOT NULL DEFAULT 0
);

-- Drop the credits table if it already exists
DROP TABLE IF EXISTS credits;

-- Create a new Credits table
-- CREATE TABLE credits (
    
-- );

-- Initial data


-- Drop the shows table if it already exists
DROP TABLE IF EXISTS shows;

-- Create a new shows table
CREATE TABLE shows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    show_type TEXT NOT NULL,
    release_year INTEGER NOT NULL,
    age_ceritification TEXT NOT NULL,
    show_runtime_minutes INTEGER NOT NULL,
    seasons INTEGER NULL DEFAULT 1,
    imdb_id TEXT NOT NULL,
    imdb_score REAL NOT NULL,
    imdb_votes INTEGER NOT NULL,
    tmdb_popularity FLOAT NOT NULL,
    tmdb_score FLOAT NOT NULL
);
CREATE INDEX imdb_score_index ON shows (imdb_score);

DROP TABLE IF EXISTS show_genres;
CREATE TABLE show_genres (
    imdb_id TEXT NOT NULL,
    genre TEXT NOT NULL,
    FOREIGN KEY (imdb_id) REFERENCES shows(imdb_id)
);
CREATE INDEX show_genres_imdb_id_index ON show_genres (imdb_id);

DROP TABLE IF EXISTS show_production_countries;
CREATE TABLE show_production_countries (
    imdb_id TEXT NOT NULL,
    country TEXT NOT NULL,
    FOREIGN KEY (imdb_id) REFERENCES shows(imdb_id)
);
CREATE INDEX show_production_countries_imdb_id_index ON show_production_countries (imdb_id);

DROP TABLE IF EXISTS show_comments;
CREATE TABLE show_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    comment TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    comment_parent_id INTEGER NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (show_id) REFERENCES shows(id),
    FOREIGN KEY (user_id) REFERENCES users(uid)
);
CREATE INDEX show_comments_show_id_index ON show_comments (show_id);
CREATE INDEX show_comments_user_id_index ON show_comments (user_id);
CREATE INDEX show_comments_comment_parent_id_index ON show_comments (comment_parent_id);