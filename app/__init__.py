import os
import slugify
import re
import hashlib
from flask import Flask, render_template, request, jsonify, g, session, redirect, abort
from datetime import datetime
from app.init_db import init_db
from app.utils import get_db_connection
from app.services.authentication import is_username_taken, is_email_in_use, create_user, get_current_user, verify_password, user_model, get_user_by_email, get_user_model_by_id

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
        cursor.execute("SELECT * FROM shows ORDER BY tmdb_popularity DESC LIMIT 45")
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
            (show_id, get_current_user().uid, request.json["content"], datetime.utcnow(), parent_comment_id)
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

    @flask_app.route("/api/delete_comment/<int:comment_id>", methods = ["DELETE"])
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
        
        def recursively_delete( comment_id : int ):
            cursor.execute("SELECT * FROM show_comments WHERE comment_parent_id = ?", (comment_id,))
            children = cursor.fetchall()
            for child in children:
                recursively_delete(child["id"])
            cursor.execute("DELETE FROM show_comments WHERE id = ?", (comment_id,))
        recursively_delete(comment_id)
        db_conn.commit()
        return jsonify({"success": True}), 200

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