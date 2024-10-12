import requests
from app.utils import get_db_connection
from config import Config

web_config = Config()

def get_poster_for_show( show_id : int ) -> str | None:
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM shows WHERE id = ?", (show_id,))
    show = cursor.fetchone()
    if show is None:
        return None
    if show["show_poster_url"] is not None:
        return show["show_poster_url"]
    
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/find/{ show['imdb_id'] }?external_source=imdb_id",
            headers = {
                "Authorization": "Bearer " + web_config.THEMOVIEDB_API_KEY
            }
        )
        if response.status_code != 200:
            return None
        response_json = response.json()
        if len( response_json["movie_results"] ) == 0 and len( response_json["tv_results"] ) == 0:
            poster_url = "https://placehold.co/780x1170"
            return None
        else:
            result = response_json["movie_results"][0] if len( response_json["movie_results"] ) > 0 else response_json["tv_results"][0]
            poster_url = f"https://image.tmdb.org/t/p/w780{ result['poster_path'] }"
        cursor.execute("UPDATE shows SET show_poster_url = ? WHERE id = ?", (poster_url, show_id))
        db_conn.commit()
        return poster_url
    except Exception as e:
        return None