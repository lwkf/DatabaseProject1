import hashlib
import random
import time
from argon2 import PasswordHasher
from datetime import datetime
from flask import session, g
from app.utils import get_db
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
    mongodb_conn = get_db()
    user_data = mongodb_conn.users.find_one({ "uid" : user_id })
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
    mongodb_conn = get_db()
    user_data = mongodb_conn.users.find_one({ "name" : username.lower().strip() })
    return user_data is not None

def is_email_in_use( email : str ) -> bool:
    mongodb_conn = get_db()
    user_data = mongodb_conn.users.find_one({ "email" : email.lower().strip() })
    return user_data is not None

def get_user_by_email( email : str ) -> user_model | None:
    mongodb_conn = get_db()
    user_data = mongodb_conn.users.find_one({ "email" : email.lower().strip() })
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
    mongo_db_conn = get_db()
    generated_user_id = int.from_bytes( ( (random.getrandbits( 8 ).to_bytes( 2, byteorder = "big" )) + int( time.time() * 1000 ).to_bytes( 6, byteorder = "big" )) , byteorder = "big" )
    hashed_password = hash_password_for_user( unhashed_password, generated_user_id )
    mongo_db_conn.users.insert_one({
        "uid" : generated_user_id,
        "name" : username,
        "email" : email.lower(),
        "password" : hashed_password,
        "created_at" : datetime.utcnow(),
        "admin_permissions" : admin_permissions
    })
    
    return generated_user_id
    
def get_current_user() -> user_model:
    if "user_id" not in session:
        return None
    if "current_user" in g:
        return g.current_user
    current_user = get_user_model_by_id( session["user_id"] )
    g.current_user = current_user
    return current_user