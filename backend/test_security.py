import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(__file__))

import main
import spotify
import ytm


class SecurityRegressionTests(unittest.TestCase):
    def setUp(self):
        with main._rate_limit_lock:
            main._request_times.clear()
        spotify._token_cache.update({"access_token": None, "expires_at": 0.0})

    def test_request_body_is_bounded(self):
        client = main.app.test_client()
        response = client.post(
            "/create",
            data=b"{" + (b"x" * (main.app.config["MAX_CONTENT_LENGTH"] + 1)) + b"}",
            content_type="application/json",
            environ_base={"REMOTE_ADDR": "198.51.100.10"},
        )
        self.assertEqual(response.status_code, 413)

    def test_errors_do_not_reflect_upstream_or_authentication_details(self):
        client = main.app.test_client()
        with patch.object(
            main,
            "create_ytm_playlist",
            side_effect=Exception("cookie secret should not be returned"),
        ):
            response = client.post(
                "/create",
                json={
                    "playlist_link": "https://open.spotify.com/playlist/"
                    + "A" * 22,
                    "auth_headers": "cookie: x\nx-goog-authuser: 0",
                },
                environ_base={"REMOTE_ADDR": "198.51.100.11"},
            )
        self.assertEqual(response.status_code, 500)
        self.assertNotIn(b"cookie secret", response.data)

    def test_create_requests_are_rate_limited(self):
        client = main.app.test_client()
        payload = {
            "playlist_link": "https://open.spotify.com/playlist/" + "A" * 22,
            "auth_headers": "cookie: x\nx-goog-authuser: 0",
        }
        with patch.object(
            main,
            "create_ytm_playlist",
            return_value={"count": 0, "tracks": []},
        ):
            for _ in range(main.RATE_LIMIT_MAX_REQUESTS):
                response = client.post(
                    "/create",
                    json=payload,
                    environ_base={"REMOTE_ADDR": "198.51.100.12"},
                )
                self.assertEqual(response.status_code, 200)

            response = client.post(
                "/create",
                json=payload,
                environ_base={"REMOTE_ADDR": "198.51.100.12"},
            )
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)

    def test_per_request_auth_file_is_removed_and_isolated(self):
        ytmusic = MagicMock()
        created_paths = []

        def construct(path):
            created_paths.append(path)
            self.assertTrue(os.path.exists(path))
            return ytmusic

        with patch.object(ytm.ytmusicapi, "setup"), patch.object(
            ytm, "YTMusic", side_effect=construct
        ), patch.object(ytm, "get_all_tracks", return_value=[]), patch.object(
            ytm, "get_playlist_name", return_value="Test playlist"
        ), patch.object(
            ytm,
            "get_video_ids",
            return_value=(['video-id'], {"count": 0, "tracks": []}),
        ):
            ytm.create_ytm_playlist(
                "https://open.spotify.com/playlist/" + "A" * 22,
                "cookie: x\nx-goog-authuser: 0",
            )

        self.assertEqual(len(created_paths), 1)
        self.assertNotEqual(os.path.basename(created_paths[0]), "header_auth.json")
        self.assertFalse(os.path.exists(created_paths[0]))

    def test_spotify_playlist_ids_are_validated_before_api_use(self):
        with self.assertRaises(ValueError):
            spotify.extract_playlist_id("https://example.com/playlist/not-valid")

        playlist_id = "A" * 22
        self.assertEqual(
            spotify.extract_playlist_id(
                f"https://open.spotify.com/playlist/{playlist_id}?si=test"
            ),
            playlist_id,
        )

    def test_spotify_token_is_cached(self):
        response = MagicMock(ok=True)
        response.json.return_value = {"access_token": "token", "expires_in": 3600}
        with patch.object(spotify.requests, "post", return_value=response) as post:
            self.assertEqual(spotify.get_spotify_access_token("id", "secret"), "token")
            self.assertEqual(spotify.get_spotify_access_token("id", "secret"), "token")
        self.assertEqual(post.call_count, 1)


if __name__ == "__main__":
    unittest.main()
