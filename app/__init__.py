import os
import slugify
import re
import hashlib
from flask import Flask, render_template, request, jsonify, g, session, redirect, abort
from datetime import datetime
from app.init_db import init_db
from app.utils import get_db_connection
from app.services.authentication import is_username_taken, is_email_in_use, create_user, get_current_user, verify_password, user_model, get_user_by_email, get_user_model_by_id
from app.services.poster_fetching import get_poster_for_show

from config import Config
web_config = Config()

def create_app():
    flask_app = Flask(__name__, template_folder = "./templates")
    flask_app.secret_key = web_config.FLASK_SESSION_KEY
    
    if not os.path.exists("./database.db"):
        init_db()
    
    @flask_app.route('/', methods = ["GET"])
    def home_page():
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM shows ORDER BY imdb_popularity DESC LIMIT 45")
        shows = cursor.fetchall()
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
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM shows WHERE id = ?", (show_id,))
        show = cursor.fetchone()
        if show is None:
            return abort(404)
        expected_slug = slugify.slugify(show["title"], lowercase = False)
        if expected_slug is None or expected_slug == "":
            expected_slug = "unnamed"
        if show_slug is None or show_slug != expected_slug:
            return redirect(f"/shows/{show_id}/{expected_slug}")
        
        show_genres = cursor.execute("SELECT genre FROM show_genres WHERE imdb_id = ?", (show['imdb_id'],)).fetchall()
        cast = cursor.execute("SELECT person_name, character_name, person_role FROM credits WHERE title_id = ?", (show['title_id'],)).fetchall()
        show_countries = cursor.execute("SELECT country FROM show_production_countries WHERE imdb_id = ?", (show['imdb_id'],)).fetchall()
        return render_template("show_details.html", show = show, show_genres = show_genres, cast = cast,show_countries=show_countries )

    @flask_app.route('/genres/<genre_name>', methods = ["GET"])
    def genre_page(genre_name : str):
        genre_name = genre_name.lower()
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM shows JOIN show_genres ON shows.imdb_id = show_genres.imdb_id WHERE show_genres.genre = ? ORDER BY imdb_popularity DESC LIMIT 60", (genre_name,))
        shows = cursor.fetchall()
        return render_template("genre_page.html", genre_name = genre_name, shows = shows)
    
    @flask_app.route('/catalogue', methods=["GET"])
    def catalogue_page():
        genre = request.args.get('genre')  # Genre filter
        search_query = request.args.get('query')  # Search query
        release_year = request.args.get('release_year')  # Release year filter
        country = request.args.get('country')  # Country filter
        show_type = request.args.get('show_type')  # Show type filter
        age_certification = request.args.get('age_certification')  # Age certification filter

        query = "SELECT * FROM shows"
        params = []

        # Adding filters to the query
        where_clauses = []
        if genre:
            query += " JOIN show_genres ON shows.imdb_id = show_genres.imdb_id"
            where_clauses.append("show_genres.genre = ?")
            params.append(genre)

        if search_query:
            where_clauses.append("LOWER(title) LIKE ?")
            params.append(f"%{search_query.lower()}%")

        if release_year:
            where_clauses.append("release_year = ?")
            params.append(release_year)

        if country:
            query += " JOIN show_production_countries ON shows.imdb_id = show_production_countries.imdb_id"
            where_clauses.append("show_production_countries.country = ?")
            params.append(country)

        if show_type:
            where_clauses.append("show_type = ?")
            params.append(show_type)

        if age_certification:
            where_clauses.append("age_ceritification = ?")
            params.append(age_certification)

        # Combine where clauses
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        # Limit to top 60 shows
        query += " ORDER BY imdb_popularity DESC LIMIT 60"

        # Debugging output
        print(f"Executing query: {query} with params: {params}")

        # Connect to database and execute query
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute(query, params)
        shows = cursor.fetchall()

        # Fetch distinct genres, countries, show types, and age certifications for the dropdown filters
        cursor.execute("SELECT DISTINCT genre FROM show_genres WHERE genre != '-' ORDER BY genre")
        genres = [row['genre'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT country FROM show_production_countries WHERE country != '-' ORDER BY country")
        countries = [row['country'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT show_type FROM shows ORDER BY show_type")
        show_types = [row['show_type'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT age_ceritification FROM shows ORDER BY age_ceritification")
        age_certifications = [row['age_ceritification'] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT release_year FROM shows ORDER BY release_year DESC")
        release_years = [row['release_year'] for row in cursor.fetchall()]

    # Determine the number of results
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
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        # Fetch user comments from the database
        cursor.execute('''
            SELECT c.comment, c.created_at, s.title 
            FROM show_comments c 
            JOIN shows s ON c.show_id = s.id 
            WHERE c.user_id = ?
            ORDER BY c.created_at DESC
        ''', (current_user.uid,))

        comments = cursor.fetchall()  # Fetch all comments for the current user

        formatted_comments = [{
            'comment': comment['comment'],
            'created_at': datetime.strptime(comment['created_at'], "%Y-%m-%d %H:%M:%S.%f").strftime("%B %d, %Y, %I:%M %p"),
            'title': comment['title']
        } for comment in comments]

        return render_template('userProfile.html', user=current_user, comments=formatted_comments)

    @flask_app.route('/api/post_comment/<int:show_id>', methods = ["POST"])
    @flask_app.route('/api/post_comment/<int:show_id>/<int:parent_comment_id>', methods = ["POST"])
    def post_comment_handler( show_id : int, parent_comment_id : int | None = None ):
        if not request.is_json:
            return jsonify({"error": "Request must be JSON", "success": False}), 400
        if get_current_user() is None:
            return jsonify({"error": "Not logged in", "success": False}), 401
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM shows WHERE id = ?", (show_id,))
        show = cursor.fetchone()
        if show is None:
            return jsonify({"error": "Show not found", "success": False}), 404
        try:
            assert "content" in request.json, "Content is required"
            assert len(request.json["content"]) >= 10, "Comment must be at least 10 characters long"
            assert len(request.json["content"]) <= 1024, "Comment must be at most 1024 characters long"
        except AssertionError as e:
            return jsonify({"error": str(e), "success": False}), 400
        
        if parent_comment_id:
            cursor.execute("SELECT * FROM show_comments WHERE id = ?", (parent_comment_id,))
            parent_comment = cursor.fetchone()
            if parent_comment is None:
                return jsonify({"error": "Parent comment not found", "success": False}), 404
            if parent_comment["show_id"] != show_id:
                return jsonify({"error": "Parent comment does not belong to this show", "success": False}), 400
        cursor.execute(
            "INSERT INTO show_comments (show_id, user_id, comment, created_at, comment_parent_id) VALUES (?, ?, ?, ?, ?)",
            (show_id, get_current_user().uid, request.json["content"], datetime.now(), parent_comment_id)
        )
        db_conn.commit()
        comment_id = cursor.lastrowid
        return jsonify({"success": True, "comment_id": comment_id}), 200
    
    @flask_app.route("/api/get_comments/<int:show_id>", methods = ["GET"])
    @flask_app.route("/api/get_comments/<int:show_id>/<int:parent_comment_id>", methods = ["GET"])
    def get_comments_handler( show_id : int, parent_comment_id : int | None = None ):
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM shows WHERE id = ?", (show_id,))
        show = cursor.fetchone()
        if show is None:
            return jsonify({"error": "Show not found", "success": False}), 404
        if parent_comment_id:
            cursor.execute("SELECT * FROM show_comments WHERE id = ?", (parent_comment_id,))
            parent_comment = cursor.fetchone()
            if parent_comment is None:
                return jsonify({"error": "Parent comment not found", "success": False}), 404
            if parent_comment["show_id"] != show_id:
                return jsonify({"error": "Parent comment does not belong to this show", "success": False}), 400
        
        if parent_comment_id:
            cursor.execute(
                "SELECT * FROM show_comments WHERE show_id = ? AND comment_parent_id = ? ORDER BY created_at DESC",
                (show_id, parent_comment_id)
            )
        else:
            cursor.execute(
                "SELECT * FROM show_comments WHERE show_id = ? AND comment_parent_id IS NULL ORDER BY created_at DESC",
                (show_id,)
            )
        comments = cursor.fetchall()
        serialized_comments = []
        for comment in comments:
            total_children = cursor.execute("SELECT COUNT(*) FROM show_comments WHERE comment_parent_id = ?", (comment["id"],))
            total_children = total_children.fetchone()[0]
            user_poster : user_model = get_user_model_by_id(comment["user_id"])
            if user_poster is None:
                continue
            serialized_comments.append({
                "id": comment["id"],
                "user": {
                    "id": user_poster.uid,
                    "username": user_poster.name,
                    "gravatar_hash": hashlib.sha256((user_poster.email.lower().strip()).encode("utf-8")).hexdigest()
                },
                "content": comment["comment"],
                "created_at": f"{comment['created_at']}-00:00",
                "total_children": total_children
            })
            
        return jsonify({"success": True, "comments": serialized_comments}), 200

    @flask_app.route("/api/delete_comment/<int:comment_id>", methods = ["UPDATE"])
    def delete_comment_handler( comment_id : int ):
        if get_current_user() is None:
            return jsonify({"error": "Not logged in", "success": False}), 401
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM show_comments WHERE id = ?", (comment_id,))
        comment = cursor.fetchone()
        if comment is None:
            return jsonify({"error": "Comment not found", "success": False}), 404
        if comment["user_id"] != get_current_user().uid:
            return jsonify({"error": "Not authorized to delete this comment", "success": False}), 403
        
        def pseudo_del_comment( comment_id : int ):
            cursor.execute("UPDATE show_comments SET comment = '[deleted]', is_deleted = 'TRUE' WHERE id = ?", (comment_id,))

        pseudo_del_comment(comment_id)
        db_conn.commit()
        return jsonify({"success": True}), 200

    @flask_app.route("/api/poster/<int:show_id>", methods = ["GET"])
    def get_poster_image( show_id : int ):
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM shows WHERE id = ?", (show_id,))
        show = cursor.fetchone()
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

    return flask_app

if __name__ == '__main__':
    flask_app = create_app()
    flask_app.run(
        debug = True
    )