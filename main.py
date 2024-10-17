#!/usr/bin/env python3

import re
from typing import TypedDict, ReadOnly, Optional
from ytmusicapi import YTMusic
import json
import os
import sys
from argparse import Namespace, ArgumentParser


class Algorithms:
    @staticmethod
    def flat[T](multi: list[T | list[T]]) -> list[T]:
        """Flattens a multi-dimentional list into a one-dimentional one. It'll
        result into a sorted list with all unique elements, be aware.
        """
        accumulator = []

        for item in multi:
            if not isinstance(item, list):
                accumulator.append(item)
                continue

            for sub_item in Algorithms.flat(item):
                accumulator.append(sub_item)

        return accumulator


class InvalidRangeError(Exception):
    def __init__(self, message="Invalid range error"):
        super().__init__(message)


def parse_range(notation: str, group=False) -> list[int] | list[tuple[int]]:
    """Parses a string notation representing ranges of integers into a list of
    integers or tuples of integers. The notation can specify individual numbers
    or ranges using a dash (-) to indicate a range. Multiple ranges should be
    separated by commas (,). The group option will make the parser to return
    the ranges groups (a list of tuples).

    The examples below shows the input string, the default output and the
    output retuned when the group option is active:
        - "1,2,3" returns [1, 2, 3] or [(1,), (2,), (3,)]
        - "1-3,5-7" returns [(1, 2, 3), (5, 6, 7)]
        - "10-12,15" returns [(10, 11, 12), (15,)]

    Quick notes: The function cleans the input by stripping invalid characters,
    such as spaces, and consolidates multiple dashes or commas; and ranges with
    only one number are considered individual numbers.
    """
    notation = notation.strip()
    notation = re.sub(r"[^0-9-,]", "", notation)
    notation = re.sub(r"-+", "-", notation)
    notation = re.sub(r",+", ",", notation)

    # This ';' is just a padding, to help the REGEX to match more easily...
    for invalid_range in re.finditer(r"\d-\D|\D-\d", f"{notation};"):
        start = invalid_range.start()

        raise InvalidRangeError(f"Range string with one number, at {start}")

    if notation == "":
        return []  # nothing was selected

    # Converts the string into a list with range groups as integer tuples.
    abstract: list[tuple[int]] = [tuple([int(digit)
                                         for digit in feat.split("-")
                                         if digit.isnumeric()])
                                  for feat in notation.split(",")]

    # This loop does the core language syntax validations.
    for pos, feat in enumerate(abstract):
        if len(feat) > 2:
            raise InvalidRangeError(f"Too much numbers specified, group {pos}")
        elif len(feat) == 2 and feat[0] > feat[1]:
            raise InvalidRangeError(f"Start greater than the end, group {pos}")

    if group:
        return [feat if len(feat) < 2 or feat[0] == feat[1] else
                tuple(range(feat[0], feat[1]+1)) for feat in abstract]

    # Before the flat and unique func
    result: list[int | list[int]] = [list(range(feat[0], feat[1] + 1))
                                     if len(feat) == 2 else feat[0]
                                     for feat in abstract]

    return Algorithms.flat(result)


class Artist(TypedDict):
    """All information of an artist necessary to fetch the other songs."""
    name: ReadOnly[str]
    browse_id: ReadOnly[str]  # Used to browse the albums, videos, etc.


def search_artists(ytmusic: YTMusic, query: str) -> list[Artist]:
    """Given a search query, this function will send that to the Youtube Music
    API and return the artists found on the "Artists" tab. The return dict is
    a sumarized one, with just the necessary information.
    """
    return [Artist(name=artist["artist"], browse_id=artist["browseId"])
            for artist in ytmusic.search(query, filter="artists")]


class Album(TypedDict):
    """Minimal album information to browse it's tracks."""
    title: ReadOnly[str]
    browse_id: ReadOnly[str]  # Used to browse it's contents.


def get_artist_albums(ytmusic: YTMusic, artist_browse_id: str) -> list[Album]:
    """Fetches all albums from an artist by its browse ID, returning the title
    and the browse ID of each playlist that this artist has. If the artist
    has no albums at all, it'll return an empty list.
    """
    artist = ytmusic.get_artist(artist_browse_id)

    if "albums" not in artist:
        return []

    albums = artist["albums"]
    albums_browse_id = albums["browseId"]  # For the artist's albums page.
    albums_params = albums["params"] if "params" in albums else None

    # Some artists has fewer albums, so they don't have an albums page.
    if albums_browse_id is None:
        return [Album(title=album["title"], browse_id=album["browseId"])
                for album in albums["results"]]

    # If the artist has an albums page, then fetch everything form there.
    albums_search_result = ytmusic.get_artist_albums(
        albums_browse_id, albums_params, limit=None)

    return [Album(title=album["title"], browse_id=album["browseId"])
            for album in albums_search_result]


class Song(TypedDict):
    """Minimal song information to allow the user to, e.g., download it."""
    title: ReadOnly[str]
    video_id: ReadOnly[str]  # Used to allow the user to do anything they want.


def get_album_tracks(ytmusic: YTMusic, album_browse_id: str) -> list[Song]:
    """Fetches all tracks from an artist album given an album browse ID. It'll
    return only the title and the video ID, which the user can use for
    downloading or extracting the song's audio. Also works for singles.
    """
    return [Song(title=str(track["title"]), video_id=track["videoId"])
            for track in ytmusic.get_album(album_browse_id)["tracks"]]


def get_artist_singles(ytmusic: YTMusic, artist_browse_id: str) -> list[Album]:
    """Uses the same logic in the get_artist_albums function: Feches the
    singles on the singles page, or in the artist profile if they hasn't, and
    return a list of song dicts with the song title and its video ID.
    """
    artist = ytmusic.get_artist(artist_browse_id)

    if "singles" not in artist:
        return []

    singles = artist["singles"]
    singles_browse_id = singles["browseId"]  # For the artist's singles page.
    singles_params = singles["params"] if "params" in singles else None

    # Some artists has no singles, so they don't have a singles page.
    if singles_browse_id is None:
        return [Album(title=single["title"], browse_id=single["browseId"])
                for single in singles["results"]]

    # If the artist has a singles page, then fetch everything form there.
    albums_search_result = ytmusic.get_artist_albums(
        singles_browse_id, singles_params, limit=None)

    return [Album(title=single["title"], browse_id=single["browseId"])
            for single in albums_search_result]


class ArtistData(TypedDict):
    """Song's data that's useful for the user for downloading into their PC."""
    artist_name: ReadOnly[str]
    artist_browse_id: ReadOnly[str]
    song_title: ReadOnly[str]
    song_video_id: ReadOnly[str]
    album_title: ReadOnly[Optional[str]]
    album_browse_id: ReadOnly[Optional[str]]
    local_path: ReadOnly[str]


def escape_filename_characters(filename: str) -> str:
    """Quick helper to make the song/artist names more filesystem friendly."""
    return f'{re.sub(r'[\\/*?:\'"<>|]', "-", filename)
              .replace("(", "[").replace(")", "]").replace(" ", "_")}'


def retrieve_artist_data(ytmusic: YTMusic, artist: Artist,
                         target="") -> list[ArtistData]:
    """Given an artist dict (with the name and browse ID), it'll fetch all
    album/single songs and compile into a massive list with all the songs of
    this artist. Each song of this list will have information about where it
    came from (albums and singles title and browse ID) and a recommended path
    to download it in the local system.

    For this local path, the artist name and album title will be sanitized.
    Which means that some characters will be removed/replaced to others; see
    the escape_filename_characters() function for more details.
    """
    albums = get_artist_albums(ytmusic, artist["browse_id"])
    singles = get_artist_singles(ytmusic, artist["browse_id"])

    full_data_list: list[ArtistData] = []
    escaped_artist_name = escape_filename_characters(artist["name"])

    for album in albums:  # TODO: Fetch each song in parallel.
        escaped_single_title = escape_filename_characters(album["title"])
        local_path = os.path.join(
            target, escaped_artist_name, "Albums", escaped_single_title)
        tracks = get_album_tracks(ytmusic, album["browse_id"])

        for track in tracks:
            full_data_list.append(ArtistData(
                artist_name=artist["name"],
                artist_browse_id=artist["browse_id"],
                song_title=track["title"],
                song_video_id=track["video_id"],
                album_title=album["title"],
                album_browse_id=album["browse_id"],
                local_path=local_path
            ))

    for single in singles:  # TODO: Fetch each song in parallel.
        escaped_single_title = escape_filename_characters(single["title"])
        local_path = os.path.join(
            target, escaped_artist_name, "Singles", escaped_single_title)
        tracks = get_album_tracks(ytmusic, single["browse_id"])

        for track in tracks:
            full_data_list.append(ArtistData(
                artist_name=artist["name"],
                artist_browse_id=artist["browse_id"],
                song_title=track["title"],
                song_video_id=track["video_id"],
                album_title=single["title"],
                album_browse_id=single["browse_id"],
                local_path=local_path
            ))

    return full_data_list


def drawn_artists_list_options(artists: list[Artist]) -> None:
    """Lists the artists with the key value, profile URL and name on stdout."""
    if len(artists) == 0:
        raise "Empty artists list not valid"

    print()
    for key, artist in list(enumerate(artists))[::-1]:
        name = artist["name"]
        browse_id = artist["browse_id"]

        div = "\033[30m|\033[m"

        print(f"\033[36m {key:<3}\033[m", div,
              f"\033[32mhttps://music.youtube.com/channel/{browse_id}\033[m",
              div, f"{name}", key == 0 and "\t\033[33m(DEFAULT)\033[m" or "")


def parse_args(args: list[str]) -> Namespace:
    """Parse the command line arguments, it's self documented..."""
    parser = ArgumentParser(
        prog="artistfetcher", description="Script to fetch all relevant data\
        from an Youtube Music artist. It'll store each artist information in\
        JSON format into a file. This can later be used to download each song\
        of them. It also includes a recommended path string with the artist\
        name and album title sanitized.")

    parser.add_argument(
        "--target", "-t", type=str, default=os.getcwd(), help="Directory where\
        the artist's JSON files should be stored.")

    parser.add_argument("query", nargs="*", help="Artist search query.")

    return parser.parse_args(args)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])

    query = " ".join(args.query)
    target = args.target

    if not os.path.isdir(target):
        raise Exception(f"Target {target} doesn't exist or isn't a directory!")

    ytmusic = YTMusic()
    artists = search_artists(ytmusic, query)

    # Let the user select what they want if there is more than one option.
    if len(artists) > 1:
        drawn_artists_list_options(artists)
        print()

        while True:
            filter = input("Select with \033[36m12\033[m, \033[36m1-8\033[m "
                           "or \033[36m5-6,12\033[m \033[32m-$\033[m ")
            try:
                selection = parse_range(filter)
            except Exception as err:
                print(f"\033[31mSelection error! {err}\033[m")
                continue

            if selection == []:
                selection = [0]

            if len(selection) > 0:
                break

        artists = [artist for key, artist in enumerate(artists)
                   if key in selection]
    print()

    for artist in artists:
        useful_data = retrieve_artist_data(ytmusic, artist)
        escaped_artist_name = escape_filename_characters(artist["name"])
        target_json_path = os.path.join(target, f"{escaped_artist_name}.json")

        with open(target_json_path, "w") as file:
            for data in useful_data:
                if data["song_video_id"] is None:  # Unavailable video.
                    continue

                print(f":: Writing \033[34m{data["artist_name"]}\033[m's "
                      f"\033[34m{data["song_title"]}\033[m song from "
                      f"\033[34m{data["album_title"]}\033[m")

                json.dump(data, file)
                file.write("\n")
