import random
import time
import os
import slugify
import re
import hashlib
import urllib.parse
from flask import Flask, render_template, request, jsonify, g, session, redirect, abort, url_for, request
from datetime import datetime
from app.init_db import init_db
from app.utils import get_db
from app.services.authentication import is_username_taken, is_email_in_use, create_user, get_current_user, verify_password, user_model, get_user_by_email, get_user_model_by_id
from app.services.poster_fetching import get_poster_for_show

from config import Config
web_config = Config()

def create_app():
    flask_app = Flask(__name__, template_folder = "./templates")
    flask_app.secret_key = web_config.FLASK_SESSION_KEY
    flask_app.config["MONGO_URI"] = web_config.MONGODB_URI

    with flask_app.app_context():
        mongodb_conn = get_db()
        if "users" not in mongodb_conn.list_collection_names():
            init_db()
            print("Database initialised")

    @flask_app.route("/api/delete_movie/<int:show_id>", methods=["DELETE"])
    def delete_movie_handler(show_id: int):
        current_user = get_current_user()
        if current_user is None:
            return jsonify({"error": "Not logged in", "success": False}), 401
        if current_user.admin_permissions != 0xFFFFFFFF:
            return jsonify({"error": "Not authorized to delete movies", "success": False}), 403

        mongodb_conn = get_db()
        show_data = mongodb_conn.shows.find_one({"id": show_id})
        if show_data is None:
            return jsonify({"error": "Show not found", "success": False}), 404
        mongodb_conn.shows.delete_one({"id": show_id})
        mongodb_conn.show_comments.delete_many({"show_id": show_id})
        mongodb_conn.credits.delete_many({"title_id": show_data["title_id"]})

        return jsonify({"success": True}), 200
    
    @flask_app.route('/', methods = ["GET"])
    def home_page():
        mongodb_conn = get_db()
        shows = list(mongodb_conn.shows.find().sort("imdb_popularity", -1).limit( 45 ))
        return render_template("index.html", shows = shows)

    @flask_app.route('/login', methods = ["GET"])
    def login_page():
        if get_current_user() is not None:
            return redirect("/")
        return render_template("authentication/user_login.html")

    @flask_app.route('/register', methods = ["GET"])
    def register_page():
        if get_current_user() is not None:
            return redirect("/")
        return render_template("authentication/user_register.html")

    @flask_app.route('/shows/<int:show_id>/', methods = ["GET"])
    @flask_app.route('/shows/<int:show_id>/<show_slug>', methods = ["GET"])
    def show_page(show_id : int, show_slug : str):
        mongodb_conn = get_db()
        show_data = mongodb_conn.shows.find_one({ "id" : show_id })
        if show_data is None:
            return abort(404)
        expected_slug = slugify.slugify(show_data["title"], lowercase = False)
        if expected_slug is None or expected_slug == "":
            expected_slug = "unnamed"
        if show_slug is None or show_slug != expected_slug:
            return redirect(f"/shows/{show_id}/{expected_slug}")
        
        show_cast = list(mongodb_conn.credits.find({ "title_id" : show_data["title_id"] }))
        return render_template("show_details.html", show = show_data, show_genres = show_data["genres"], cast = show_cast, show_countries=show_data["production_countries"])

    @flask_app.route('/genres/<genre_name>', methods = ["GET"])
    def genre_page(genre_name : str):
        genre_name = genre_name.lower()
        mongodb_conn = get_db()
        shows = list(mongodb_conn.shows.find({ "genres" : genre_name }).sort("imdb_popularity", -1).limit( 60 ))
        return render_template("genre_page.html", genre_name = genre_name, shows = shows)
    
    @flask_app.route('/catalogue', methods=["GET"])
    def catalogue_page():
        genre = request.args.get('genre')
        search_query = request.args.get('query')
        release_year = request.args.get('release_year')
        country = request.args.get('country')
        show_type = request.args.get('show_type')
        age_certification = request.args.get('age_certification')

        mongodb_conn = get_db()
        
        query_params = {
            "genre": genre,
            "query": search_query,
            "release_year": release_year,
            "country": country,
            "show_type": show_type,
            "age_certification": age_certification
        }
        
        query_params = {k: v for k, v in query_params.items() if v}
        current_query_string = urllib.parse.urlencode(query_params)
        if request.query_string.decode('utf-8') != current_query_string:
            return redirect(f"{url_for('catalogue_page')}?{current_query_string}")

        query = {}
        if genre:
            query["genres"] = genre
        if search_query:
            query["title"] = {"$regex": search_query, "$options": "i"}
        if release_year:
            query["release_year"] = release_year
        if country:
            query["production_countries"] = country
        if show_type:
            query["show_type"] = show_type
        if age_certification:
            query["age_certification"] = age_certification

        shows = list(mongodb_conn.shows.find(query).sort("imdb_popularity", -1).limit(60))
        genres = mongodb_conn.shows.distinct("genres")
        genres.remove("-")
        countries = mongodb_conn.shows.distinct("production_countries")
        countries.remove("-")
        show_types = mongodb_conn.shows.distinct("show_type")
        age_certifications = mongodb_conn.shows.distinct("age_certification")
        release_years = mongodb_conn.shows.distinct("release_year")
        
        result_count = len(shows)
        result_text = f"Showing Top {min(result_count, 60)} results"
        if result_count == 0:
            result_text = "No show/movie found for"
        if search_query:
            result_text += f"  Search Query: '{search_query}'"
        if genre:
            result_text += f"  Genre: {genre}"
        if country:
            result_text += f" Country: {country}"
        if release_year:
            result_text += f" Year: {release_year}"
        if show_type:
            result_text += f" Type: {show_type}"
        if age_certification:
            result_text += f" Certification: {age_certification}"

        return render_template(
            'catalogue.html',
            shows=shows,
            genre_name=genre or 'All',
            genres=genres,
            countries=countries,
            show_types=show_types,
            age_certifications=age_certifications,
            release_years=release_years,
            result_text=result_text,
            genre=genre,
            country=country,
            release_year=release_year,
            show_type=show_type,
            age_certification=age_certification
        )

    @flask_app.route('/api/register', methods = ["POST"])
    def register_handler():
        if not request.is_json:
            return jsonify({"error": "Request must be JSON", "success": False}), 400
        if get_current_user() is not None:
            return jsonify({"error": "Already logged in", "success": False}), 400
        username_regex = re.compile(r"^[a-zA-Z0-9]+$")
        try:
            assert "username" in request.json, "Username is required"
            assert "email" in request.json, "Email is required"
            assert "password" in request.json, "Password is required"
            assert len(request.json["username"]) >= 4, "Username must be at least 4 characters"
            assert len(request.json["username"]) <= 20, "Username must be at most 20 characters"
            assert username_regex.match(request.json["username"]), "Username must only contain letters and numbers"
            assert len(request.json["email"]) <= 255, "Email must be at most 255 characters"
            assert len(request.json["password"]) >= 8, "Password must be at least 8 characters"
            assert len(request.json["password"]) <= 255, "Password must be at most 255 characters"
            assert not is_username_taken(request.json["username"]), "Username is already taken"
            assert not is_email_in_use(request.json["email"]), "Email is already in use"
        except AssertionError as e:
            return jsonify({"error": str(e), "success": False}), 400
        username = request.json["username"]
        email = request.json["email"].lower().strip()
        password = request.json["password"]
        new_user_id = create_user(
            username = username,
            email = email,
            unhashed_password = password
        )
        session["user_id"] = new_user_id
        return jsonify({"success": True, "user_id": new_user_id}), 200

    @flask_app.route('/api/login', methods = ["POST"])
    def login_handler():
        if not request.is_json:
            return jsonify({"error": "Request must be JSON", "success": False}), 400
        if get_current_user() is not None:
            return jsonify({"error": "Already logged in", "success": False}), 400
        try:
            assert "email" in request.json, "Email is required"
            assert "password" in request.json, "Password is required"
            assert len(request.json["email"]) <= 255, "Email must be at most 255 characters"
            assert len(request.json["password"]) <= 255, "Password must be at most 255 characters"
        except AssertionError as e:
            return jsonify({"error": str(e), "success": False}), 400
        email = request.json["email"].lower().strip()
        password = request.json["password"]
        target_user : user_model | None = get_user_by_email(email = email)
        if target_user is None:
            return jsonify({"error": "Email or password is incorrect", "success": False}), 400
        if not verify_password( password = password, hashed_password = target_user.hashed_password ):
            return jsonify({"error": "Email or password is incorrect", "success": False}), 400
        session["user_id"] = target_user.uid
        return jsonify({"success": True, "user_id": target_user.uid}), 200

    @flask_app.route('/api/logout', methods=['POST'])
    def logout_handler():
        session.pop('user_id', None)  # Remove the user_id from the session
        return jsonify({"success": True}), 200

    @flask_app.route('/profile')
    def profile():
        current_user = get_current_user()
        if current_user is None:
            return redirect("/login")
        mongodb_conn = get_db()
        comments_data = mongodb_conn.show_comments.find({ "user_id" : current_user.uid }).sort("created_at", -1)
        formatted_comments = []
        for comment in comments_data:
            show_data = mongodb_conn.shows.find_one({ "id" : comment["show_id"] })
            if show_data is None:
                continue
            formatted_comments.append({
                "comment": comment["comment"],
                "created_at": comment["created_at"].strftime("%B %d, %Y, %I:%M %p+00:00"),
                "title": show_data["title"],
                "show_id": show_data["id"],
                "is_deleted": comment["is_deleted"],
                "id": comment["id"]
            })

        return render_template('userProfile.html', user=current_user, comments=formatted_comments)

    @flask_app.route('/api/post_comment/<int:show_id>', methods = ["POST"])
    @flask_app.route('/api/post_comment/<int:show_id>/<int:parent_comment_id>', methods = ["POST"])
    def post_comment_handler( show_id : int, parent_comment_id : int | None = None ):
        if not request.is_json:
            return jsonify({"error": "Request must be JSON", "success": False}), 400
        if get_current_user() is None:
            return jsonify({"error": "Not logged in", "success": False}), 401
        mongodb_conn = get_db()
        show_data = mongodb_conn.shows.find_one({ "id" : show_id })
        if show_data is None:
            return jsonify({"error": "Show not found", "success": False}), 404
        try:
            assert "content" in request.json, "Content is required"
            assert len(request.json["content"]) >= 10, "Comment must be at least 10 characters long"
            assert len(request.json["content"]) <= 1024, "Comment must be at most 1024 characters long"
        except AssertionError as e:
            return jsonify({"error": str(e), "success": False}), 400
        
        if parent_comment_id:
            parent_comment_data = mongodb_conn.show_comments.find_one({ "id" : int( parent_comment_id ) })
            if parent_comment_data is None:
                return jsonify({"error": "Parent comment not found", "success": False}), 404
            if parent_comment_data["show_id"] != show_id:
                return jsonify({"error": "Parent comment does not belong to this show", "success": False}), 400
        generated_comment_id = int.from_bytes( ( (random.getrandbits( 8 ).to_bytes( 2, byteorder = "big" )) + int( time.time() * 1000 ).to_bytes( 6, byteorder = "big" )) , byteorder = "big" )
        mongodb_conn.show_comments.insert_one({
            "id": generated_comment_id,
            "user_id": get_current_user().uid,
            "show_id": show_id,
            "comment": request.json["content"],
            "created_at": datetime.now(),
            "comment_parent_id": parent_comment_id,
            "is_deleted": False
        })
        return jsonify({"success": True, "comment_id": generated_comment_id}), 200
    
    @flask_app.route("/api/get_comments/<int:show_id>", methods = ["GET"])
    @flask_app.route("/api/get_comments/<int:show_id>/<int:parent_comment_id>", methods = ["GET"])
    def get_comments_handler( show_id : int, parent_comment_id : int | None = None ):
        mongodb_conn = get_db()
        show_data = mongodb_conn.shows.find_one({ "id" : show_id })
        if show_data is None:
            return jsonify({"error": "Show not found", "success": False}), 404
        if parent_comment_id:
            parent_coment_data = mongodb_conn.show_comments.find_one({ "id" : parent_comment_id })
            if parent_coment_data is None:
                return jsonify({"error": "Parent comment not found", "success": False}), 404
            if parent_coment_data["show_id"] != show_id:
                return jsonify({"error": "Parent comment does not belong to this show", "success": False}), 400
        
        comments_data = mongodb_conn.show_comments.find({ "show_id" : show_id, "comment_parent_id" : parent_comment_id })
        serialized_comments = []
        for comment in comments_data:
            total_children = mongodb_conn.show_comments.count_documents({ "comment_parent_id" : comment["id"] })
            user_poster : user_model = get_user_model_by_id(comment["user_id"])
            if user_poster is None:
                continue
            serialized_comments.append({
                "id": str( comment["id"] ), # Javascript JSON parser struggles to parse large integers so we convert to string
                "user": {
                    "id": str( user_poster.uid ),
                    "username": user_poster.name,
                    "gravatar_hash": hashlib.sha256((user_poster.email.lower().strip()).encode("utf-8")).hexdigest()
                },
                "content": comment["comment"],
                "created_at": comment["created_at"].strftime("%B %d, %Y, %I:%M %p+00:00"),
                "total_children": total_children,
                "is_deleted": comment["is_deleted"]
            })
            
        return jsonify({"success": True, "comments": serialized_comments}), 200

    @flask_app.route("/api/delete_comment/<int:comment_id>", methods = ["UPDATE"])
    def delete_comment_handler( comment_id : int ):
        if get_current_user() is None:
            return jsonify({"error": "Not logged in", "success": False}), 401
        mongodb_conn = get_db()
        comment_data = mongodb_conn.show_comments.find_one({ "id" : comment_id })
        if comment_data is None:
            return jsonify({"error": "Comment not found", "success": False}), 404
        if comment_data["user_id"] != get_current_user().uid:
            return jsonify({"error": "Not authorized to delete this comment", "success": False}), 403
        
        mongodb_conn.show_comments.update_one({ "id" : comment_id }, { "$set" : { "comment" : "[deleted]", "is_deleted" : True } })
        return jsonify({"success": True}), 200

    @flask_app.route("/api/poster/<int:show_id>", methods = ["GET"])
    def get_poster_image( show_id : int ):
        mongodb_conn = get_db()
        show = mongodb_conn.shows.find_one({ "id" : show_id })
        if show is None:
            return jsonify({"error": "Show not found", "success": False}), 404
        poster_url = get_poster_for_show(show_id)
        if poster_url is None:
            return redirect("https://placehold.co/780x1170")
        return redirect(poster_url)

    @flask_app.before_request
    def before_request():
        if "user_id" in session:
            if not get_current_user():
                session.pop("user_id")

    @flask_app.context_processor
    def inject_user():
        current_user = get_current_user()
        gravatar_email_hash = hashlib.sha256((current_user.email.lower().strip()).encode("utf-8")).hexdigest() if current_user is not None else None
        return {
            "current_user": current_user,
            "gravatar_email_hash": gravatar_email_hash
        }
    flask_app.jinja_env.globals.update( float=float, int=int )

    return flask_app

if __name__ == '__main__':
    flask_app = create_app()
    flask_app.run(
        debug = True
    )