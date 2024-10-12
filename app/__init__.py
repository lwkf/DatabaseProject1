import os
import slugify
import re
import hashlib
from flask import Flask, render_template, request, jsonify, g, session, redirect, abort
from app.init_db import init_db
from app.utils import get_db_connection
from app.services.authentication import is_username_taken, is_email_in_use, create_user, get_current_user, verify_password, user_model, get_user_by_email

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
        cursor.execute("SELECT * FROM shows ORDER BY imdb_score DESC LIMIT 45")
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
        return render_template("show_details.html", show = show, show_genres = show_genres)

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