import hashlib
from argon2 import PasswordHasher
from datetime import datetime
from flask import session, g
from app.utils import get_db_connection
from app.enums.AdminPermissions import AdminPermission
from config import Config

web_config = Config()

class user_model():
    uid : int = 0
    name : str = ""
    email : str = ""
    hashed_password : str = ""
    created_at : datetime = datetime.utcnow()
    admin_permissions : int = 0
    
    def __init__( self, uid : int, name : str, email : str, hashed_password : str, created_at : datetime, admin_permissions : int ):
        self.uid = uid
        self.name = name
        self.email = email
        self.hashed_password = hashed_password
        self.created_at = created_at
        self.admin_permissions = admin_permissions

def _get_argon_salt( user_id : int ) -> bytes:
    return ( hashlib.sha512( (web_config.FLASK_SESSION_KEY + str(user_id)).encode("utf-8") ) ).digest()
def _get_password_hasher() -> PasswordHasher:
    return PasswordHasher(
        time_cost=16,
        memory_cost=2**14,
        parallelism=2,
        hash_len=32,
        salt_len=16
    )

def get_user_model_by_id( user_id : int ) -> user_model | None:
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE uid = ?", (user_id,))
    user_data = cursor.fetchone()
    if user_data is None:
        return None
    return user_model(
        uid = user_data["uid"],
        name = user_data["name"],
        email = user_data["email"],
        hashed_password = user_data["password"],
        created_at = user_data["created_at"],
        admin_permissions = user_data["admin_permissions"]
    )
    
def verify_password( password : str, hashed_password : str ) -> bool:
    try:
        _get_password_hasher().verify( hash = hashed_password, password = password )
        return True
    except:
        return False

def hash_password_for_user( password : str, user_id : int ) -> str:
    return _get_password_hasher().hash( password = password, salt = _get_argon_salt( user_id ) )

def does_have_permission( permission : AdminPermission, user_permissions : int ) -> bool:
    return ( user_permissions >> permission.value ) & 1 == 1

def is_username_taken( username : str ) -> bool:
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(name) = ?", (username.lower().strip(),))
    return cursor.fetchone() is not None

def is_email_in_use( email : str ) -> bool:
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    return cursor.fetchone() is not None

def get_user_by_email( email : str ) -> user_model | None:
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    user_data = cursor.fetchone()
    if user_data is None:
        return None
    return get_user_model_by_id( user_data["uid"] )

def create_user(
    username : str,
    email : str,
    unhashed_password : str,
    admin_permissions : int = 0
) -> int:
    """
        Creates a user in the database and returns their user ID
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, created_at, admin_permissions) VALUES (?, ?, ?, ?)",
        (username, email.lower(), datetime.utcnow(), admin_permissions)
    )
    db_conn.commit()
    user_id = cursor.lastrowid
    
    hashed_password = hash_password_for_user( unhashed_password, user_id )
    cursor.execute(
        "UPDATE users SET password = ? WHERE uid = ?",
        (hashed_password, user_id)
    )
    db_conn.commit()
    return user_id
    
def get_current_user() -> user_model:
    if "user_id" not in session:
        return None
    if "current_user" in g:
        return g.current_user
    current_user = get_user_model_by_id( session["user_id"] )
    g.current_user = current_user
    return current_user