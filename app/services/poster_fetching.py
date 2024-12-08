import requests
from app.utils import get_db
from config import Config

web_config = Config()

def get_poster_for_show( show_id : int ) -> str | None:
    mongodb_conn = get_db()
    show_data = mongodb_conn.shows.find_one({ "id" : show_id })
    if show_data is None:
        return None
    if show_data["show_poster_url"] is not None:
        return show_data["show_poster_url"]
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/find/{ show_data['imdb_id'] }?external_source=imdb_id",
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
        mongodb_conn.shows.update_one({ "id" : show_id }, { "$set" : { "show_poster_url" : poster_url } })
        return poster_url
    except Exception as e:
        return None