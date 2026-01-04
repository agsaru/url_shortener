from hashids import Hashids
import os
from dotenv import load_dotenv

load_dotenv()

salt = os.getenv("HASHED_SALT", "default_salt")
hashids = Hashids(salt=salt, min_length=6)

def encode_id(id_val: int) -> str:
    return hashids.encode(id_val)