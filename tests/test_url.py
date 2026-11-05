import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest

from src.utils.url import normalize_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("HTTPS://Example.COM", "https://example.com/"),
        (
            "https://example.com:443/path",
            "https://example.com/path",
        ),
        (
            "http://example.com:8080/path",
            "http://example.com:8080/path",
        ),
        (
            "https://example.com/path?a=1#section",
            "https://example.com/path?a=1#section",
        ),
        (
            "https://example.com/path?b=2&a=1",
            "https://example.com/path?a=1&b=2",
        ),
    ],
)
def test_normalize_url(url, expected):
    assert normalize_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/file",
        "https://user:pass@example.com",
        "https://user@example.com",
        "https://@example.com",
        "https://example.com:99999",
        "https://example.com/a b",
    ],
)
def test_normalize_url_rejects_invalid_urls(url):
    with pytest.raises(ValueError):
        normalize_url(url)
