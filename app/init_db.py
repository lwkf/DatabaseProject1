import random
import string
import csv
from datetime import datetime
from app.utils import get_db_connection
from app.services.authentication import create_user
def init_db():
    conn = get_db_connection()
    with open("./app/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    #admin_password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    admin_password = "INF2003AdminPWD"
    create_user(
        username = "admin",
        email = "admin@example.com",
        unhashed_password = admin_password,
        admin_permissions = 0xFFFFFFFF
    )
    print(f"Created user 'admin' at 'admin@example.com' with password '{admin_password}'")

    user_password = "INF2003UserPWD"
    create_user(
        username = "user",
        email = "user@example.com",
        unhashed_password = user_password
    )
    print(f"Created user 'user' at 'user@example.com' with password '{user_password}'")
    
    cursor = conn.cursor()
    with open("./movie_data.csv", "r", encoding = "utf8") as f:
        """id,title,type,description,release_year,age_certification,runtime,genres,production_countries,seasons,imdb_id,imdb_score,imdb_votes,tmdb_popularity,tmdb_score"""
        file_reader = csv.DictReader(f)
        for row in file_reader:
            imdb_id = row["imdb_id"]
            if imdb_id == "Unknown":
                continue # Too lazy to handle this
            imdb_popularity = round( float(row["imdb_score"]) * float(row["imdb_votes"]) )
            cursor.execute(
        """INSERT INTO shows (title_id, title, show_type, description, release_year, age_ceritification, show_runtime_minutes, seasons, imdb_id, imdb_score, imdb_votes, tmdb_popularity, tmdb_score, imdb_popularity)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (row["id"], row["title"], row["type"], row["description"], row["release_year"], row["age_certification"], row["runtime"], row["seasons"], row["imdb_id"], row["imdb_score"], row["imdb_votes"], row["tmdb_popularity"], row["tmdb_score"], imdb_popularity))
            show_genre = row["genres"].split(", ")
            for genre in show_genre:
                cursor.execute(
                    """INSERT INTO show_genres (imdb_id, genre) VALUES (?,?)""", (imdb_id, genre)
                )
            show_production_countries = row["production_countries"].split(", ")
            for country in show_production_countries:
                cursor.execute(
                    """INSERT INTO show_production_countries (imdb_id, country) VALUES (?,?)""", (imdb_id, country)
                )

    with open("./movie_credits.csv", "r", encoding="utf8") as f:
        credits_reader = csv.DictReader(f)
        for row in credits_reader:
            cursor.execute(
                """INSERT INTO credits (person_id, title_id, person_name, character_name, person_role)
                   VALUES (?,?,?,?,?)""",
                (row["person_id"], row["id"], row["name"], row["character"], row["role"])
            )

    conn.commit()