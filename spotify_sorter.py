"""Sortera eller slumpa dina egna Spotify-spellistor."""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

T = TypeVar("T")
TrackItem = dict[str, Any]


def require_environment() -> dict[str, str]:
    """Läs och validera konfiguration utan att skriva ut hemligheter."""
    load_dotenv()
    required = ("CLIENT_ID", "CLIENT_SECRET", "REDIRECT_URI", "SCOPE")
    values = {name: os.getenv(name, "").strip() for name in required}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SystemExit(f"Saknade miljövariabler: {', '.join(missing)}")
    return values


def spotify_call(operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Kör ett Spotify-anrop och respektera API:ts rate limit."""
    while True:
        try:
            return operation(*args, **kwargs)
        except spotipy.exceptions.SpotifyException as error:
            if error.http_status != 429:
                raise
            headers = error.headers or {}
            retry_after = int(headers.get("Retry-After", 5))
            print(f"Rate limit nådd. Väntar {retry_after} sekunder …")
            time.sleep(retry_after)


def all_pages(client: spotipy.Spotify, first_page: dict[str, Any]) -> list[dict[str, Any]]:
    """Hämta items från samtliga sidor i ett Spotify-svar."""
    items = list(first_page.get("items", []))
    page = first_page
    while page.get("next"):
        page = spotify_call(client.next, page)
        items.extend(page.get("items", []))
    return items


def valid_tracks(items: Iterable[TrackItem]) -> tuple[list[TrackItem], int]:
    """Filtrera bort borttagna eller otillgängliga poster."""
    valid: list[TrackItem] = []
    skipped = 0
    for item in items:
        track = item.get("track")
        if not track or not track.get("uri") or not track.get("artists"):
            skipped += 1
            continue
        valid.append(item)
    return valid, skipped


def release_date(item: TrackItem) -> tuple[int, int, int]:
    """Normalisera Spotify-datum med precision år, månad eller dag."""
    date_text = item["track"].get("album", {}).get("release_date", "")
    parts = date_text.split("-") if date_text else []
    numbers = [int(part) if part.isdigit() else 0 for part in parts[:3]]
    return tuple((numbers + [0, 0, 0])[:3])  # type: ignore[return-value]


def artist_key(item: TrackItem) -> tuple[str, tuple[int, int, int], str]:
    track = item["track"]
    return (
        track["artists"][0].get("name", "").casefold(),
        release_date(item),
        track.get("name", "").casefold(),
    )


def sort_tracks(items: list[TrackItem], choice: str, reverse: bool = False) -> list[TrackItem]:
    result = list(items)
    if choice == "1":
        return sorted(result, key=artist_key, reverse=reverse)
    if choice == "2":
        return sorted(result, key=release_date, reverse=reverse)
    random.shuffle(result)
    return result


def choose(prompt: str, choices: set[str]) -> str:
    while True:
        answer = input(prompt).strip()
        if answer in choices:
            return answer
        print(f"Ogiltigt val. Ange {' eller '.join(sorted(choices))}.")


def choose_playlist(playlists: list[dict[str, Any]]) -> dict[str, Any]:
    while True:
        answer = input("Ange numret på spellistan du vill sortera: ").strip()
        try:
            return playlists[int(answer)]
        except (ValueError, IndexError):
            print(f"Ange ett nummer mellan 0 och {len(playlists) - 1}.")


def add_in_batches(client: spotipy.Spotify, playlist_id: str, uris: list[str]) -> None:
    for start in range(0, len(uris), 100):
        spotify_call(client.playlist_add_items, playlist_id, uris[start : start + 100])


def reorder_playlist(
    client: spotipy.Spotify,
    playlist_id: str,
    current: list[TrackItem],
    target: list[TrackItem],
) -> None:
    """Flytta poster på plats utan att först tömma spellistan.

    Occurrence-numret gör att även dubbletter kan matchas entydigt.
    """
    def identities(items: list[TrackItem]) -> list[tuple[str, int]]:
        seen: dict[str, int] = {}
        result: list[tuple[str, int]] = []
        for item in items:
            uri = item["track"]["uri"]
            seen[uri] = seen.get(uri, 0) + 1
            result.append((uri, seen[uri]))
        return result

    working = identities(current)
    desired = identities(target)
    for destination, identity in enumerate(desired):
        source = working.index(identity)
        if source == destination:
            continue
        insert_before = destination if source > destination else destination + 1
        spotify_call(
            client.playlist_reorder_items,
            playlist_id,
            range_start=source,
            insert_before=insert_before,
        )
        working.insert(destination, working.pop(source))


def main() -> None:
    config = require_environment()
    client = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=config["CLIENT_ID"],
            client_secret=config["CLIENT_SECRET"],
            redirect_uri=config["REDIRECT_URI"],
            scope=config["SCOPE"],
        )
    )

    user_id = spotify_call(client.current_user)["id"]
    playlists = all_pages(client, spotify_call(client.current_user_playlists))
    owned = [item for item in playlists if item.get("owner", {}).get("id") == user_id]
    if not owned:
        raise SystemExit("Inga egna spellistor hittades.")

    print("Dina skapade spellistor:")
    for index, playlist in enumerate(owned):
        print(f"{index}: {playlist['name']}")
    playlist = choose_playlist(owned)

    raw_tracks = all_pages(client, spotify_call(client.playlist_items, playlist["id"]))
    tracks, skipped = valid_tracks(raw_tracks)
    print(f"Hämtade {len(tracks)} låtar.")
    if skipped:
        print(f"Hoppar över {skipped} borttagna eller otillgängliga poster.")
    if not tracks:
        raise SystemExit("Spellistan innehåller inga sorterbara låtar.")

    print("\nSortera efter:\n1: Artist\n2: Releasedatum\n3: Slumpa ordningen")
    sort_choice = choose("Ange 1, 2 eller 3: ", {"1", "2", "3"})
    reverse = False
    if sort_choice in {"1", "2"}:
        print("\nSorteringsordning:\n1: Stigande (äldst / A→Ö)\n2: Fallande (nyast / Ö→A)")
        reverse = choose("Ange 1 eller 2: ", {"1", "2"}) == "2"
    sorted_tracks = sort_tracks(tracks, sort_choice, reverse)

    print("\nVad vill du göra?\n1: Sortera om befintlig spellista\n2: Skapa en privat, sorterad kopia")
    action = choose("Ange 1 eller 2: ", {"1", "2"})
    if action == "1":
        if skipped:
            raise SystemExit(
                "Originalet kan inte sorteras säkert när otillgängliga poster finns. "
                "Kör igen och välj en sorterad kopia i stället."
            )
        reorder_playlist(client, playlist["id"], tracks, sorted_tracks)
        print("Den befintliga spellistan har sorterats om!")
        return

    new_playlist = spotify_call(
        client.user_playlist_create,
        user_id,
        name=f"{playlist['name']} (sorterad)",
        public=False,
    )
    add_in_batches(client, new_playlist["id"], [item["track"]["uri"] for item in sorted_tracks])
    print(f"Ny sorterad spellista skapad: {new_playlist['name']}")


if __name__ == "__main__":
    main()
