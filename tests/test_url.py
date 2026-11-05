import os
import unittest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from src.utils.url import normalize_url


class NormalizeUrlTests(unittest.TestCase):
    def test_normalizes_scheme_and_hostname(self):
        self.assertEqual(
            normalize_url("HTTPS://Example.COM"),
            "https://example.com/",
        )

    def test_removes_default_port(self):
        self.assertEqual(
            normalize_url("https://example.com:443/path"),
            "https://example.com/path",
        )

    def test_preserves_non_default_port(self):
        self.assertEqual(
            normalize_url("http://example.com:8080/path"),
            "http://example.com:8080/path",
        )

    def test_preserves_query_and_fragment(self):
        self.assertEqual(
            normalize_url("https://example.com/path?a=1#section"),
            "https://example.com/path?a=1#section",
        )

    def test_rejects_non_http_scheme(self):
        with self.assertRaises(ValueError):
            normalize_url("ftp://example.com/file")

    def test_rejects_embedded_credentials(self):
        values = (
            "https://user:pass@example.com",
            "https://user@example.com",
            "https://@example.com",
        )
        for value in values:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_url(value)

    def test_rejects_invalid_port(self):
        with self.assertRaises(ValueError):
            normalize_url("https://example.com:99999")

    def test_rejects_whitespace(self):
        with self.assertRaises(ValueError):
            normalize_url("https://example.com/a b")


if __name__ == "__main__":
    unittest.main()
