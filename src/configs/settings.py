import os
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv()

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
parsed_public_url = urlsplit(PUBLIC_BASE_URL)

if (
    parsed_public_url.scheme not in {"http", "https"}
    or not parsed_public_url.hostname
    or parsed_public_url.username is not None
    or parsed_public_url.password is not None
):
    raise RuntimeError(
        "PUBLIC_BASE_URL must be an HTTP or HTTPS URL without credentials"
    )
