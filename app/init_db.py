import random
import string
import time
import csv
import pymongo
from datetime import datetime
from app.utils import get_db
from app.services.authentication import create_user
def init_db():
    mongo_db_conn = get_db()
    try:
        mongo_db_conn.create_collection("users")
        mongo_db_conn.create_collection("shows")
        mongo_db_conn.create_collection("credits")
        mongo_db_conn.create_collection("show_comments")
        
        mongo_db_conn.users.create_index("uid", unique = True)
        mongo_db_conn.shows.create_index("id", unique = True)
        mongo_db_conn.shows.create_index("genres")
        mongo_db_conn.shows.create_index("production_countries")
        mongo_db_conn.shows.create_index("release_year")
        mongo_db_conn.shows.create_index("age_certification")
        mongo_db_conn.credits.create_index("title_id")
        mongo_db_conn.show_comments.create_index("show_id")
        mongo_db_conn.show_comments.create_index("user_id")
        mongo_db_conn.show_comments.create_index("comment_parent_id")
    except:
        return # Database already initialized or is being initialized by another thread
    
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
        username = "exampleUser",
        email = "user@example.com",
        unhashed_password = user_password
    )
    print(f"Created user 'user' at 'user@example.com' with password '{user_password}'")
    
    with open("./movie_data.csv", "r", encoding = "utf8") as f:
        """id,title,type,description,release_year,age_certification,runtime,genres,production_countries,seasons,imdb_id,imdb_score,imdb_votes,tmdb_popularity,tmdb_score"""
        file_reader = csv.DictReader(f)
        show_id_counter = 0
        for row in file_reader:
            imdb_id = row["imdb_id"]
            if imdb_id == "Unknown":
                continue
            imdb_popularity = round( float(row["imdb_score"]) * float(row["imdb_votes"]) )
            show_genre = row["genres"].split(", ")
            show_production_countries = row["production_countries"].split(", ")
            generated_show_id = int.from_bytes( ( (show_id_counter.to_bytes( 2, byteorder = "big" )) + int( time.time() * 1000 ).to_bytes( 6, byteorder = "big" )) , byteorder = "big" )
            mongo_db_conn.shows.insert_one({
                "id": generated_show_id,
                "title_id": row["id"],
                "title": row["title"],
                "show_type": row["type"],
                "description": row["description"],
                "release_year": row["release_year"],
                "age_certification": row["age_certification"],
                "show_runtime_minutes": row["runtime"],
                "seasons": row["seasons"],
                "imdb_id": row["imdb_id"],
                "imdb_score": row["imdb_score"],
                "imdb_votes": row["imdb_votes"],
                "tmdb_popularity": row["tmdb_popularity"],
                "tmdb_score": row["tmdb_score"],
                "imdb_popularity": imdb_popularity,
                "show_poster_url": None,
                
                "genres": show_genre,
                "production_countries": show_production_countries
            })
            show_id_counter += 1

    with open("./movie_credits.csv", "r", encoding="utf8") as f:
        credits_reader = csv.DictReader(f)
        for row in credits_reader:
            mongo_db_conn.credits.insert_one({
                "person_id": row["person_id"],
                "title_id": row["id"],
                "person_name": row["name"],
                "character_name": row["character"],
                "person_role": row["role"]
            })
    
    