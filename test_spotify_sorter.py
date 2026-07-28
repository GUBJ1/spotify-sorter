import unittest
from unittest.mock import patch

import spotify_sorter as sorter


def item(uri: str, artist: str, title: str, date: str):
    return {"track": {"uri": uri, "name": title, "artists": [{"name": artist}], "album": {"release_date": date}}}


class FakeSpotify:
    def __init__(self):
        self.moves = []

    def playlist_reorder_items(self, playlist_id, **kwargs):
        self.moves.append((playlist_id, kwargs))


class SpotifySorterTests(unittest.TestCase):
    def setUp(self):
        self.tracks = [
            item("spotify:track:2", "Zebra", "Second", "2024"),
            item("spotify:track:1", "Alpha", "First", "2023-02-01"),
            item("spotify:track:3", "Alpha", "Third", "2023-01"),
        ]

    def test_artist_sort(self):
        result = sorter.sort_tracks(self.tracks, "1")
        self.assertEqual([track["track"]["uri"] for track in result], ["spotify:track:3", "spotify:track:1", "spotify:track:2"])

    def test_release_date_sort(self):
        result = sorter.sort_tracks(self.tracks, "2", reverse=True)
        self.assertEqual([track["track"]["uri"] for track in result], ["spotify:track:2", "spotify:track:1", "spotify:track:3"])

    def test_invalid_tracks_are_skipped(self):
        valid, skipped = sorter.valid_tracks([self.tracks[0], {"track": None}, {"track": {"uri": None}}])
        self.assertEqual(len(valid), 1)
        self.assertEqual(skipped, 2)

    @patch.object(sorter, "spotify_call", side_effect=lambda operation, *args, **kwargs: operation(*args, **kwargs))
    def test_reorder_moves_without_deleting(self, _spotify_call):
        fake = FakeSpotify()
        sorter.reorder_playlist(fake, "playlist", self.tracks, [self.tracks[1], self.tracks[2], self.tracks[0]])
        self.assertEqual(len(fake.moves), 2)
        self.assertEqual(fake.moves[0][1], {"range_start": 1, "insert_before": 0})

    @patch.object(sorter, "spotify_call", side_effect=lambda operation, *args, **kwargs: operation(*args, **kwargs))
    def test_reorder_handles_duplicate_uris(self, _spotify_call):
        fake = FakeSpotify()
        duplicate = item("spotify:track:1", "Alpha", "First", "2023")
        current = [duplicate, self.tracks[0], duplicate]
        target = [duplicate, duplicate, self.tracks[0]]
        sorter.reorder_playlist(fake, "playlist", current, target)
        self.assertEqual(len(fake.moves), 1)
        self.assertEqual(fake.moves[0][1], {"range_start": 2, "insert_before": 1})


if __name__ == "__main__":
    unittest.main()
