#!/usr/bin/env python3

from sys import stderr, argv
from json import dumps
from re import sub

# Secure import. This block halts the script if the user forgot to install the
# required *ytmusicapi* library.

try:
    from ytmusicapi import YTMusic

except ModuleNotFoundError as err:
    stderr.write("This scripts depends on the ytmusicapi module!")
    stderr.write(err)

    exit(1)


class Algo:
    """Collection of wrapper function that makes the Python's list functions a
    little bit easier to use. Just that, every method should be dead simple.
    """
    @staticmethod
    def filter(arr: list, func: callable) -> list:
        return list(filter(func, arr))

    @staticmethod
    def map(arr: list, func: callable) -> list:
        return list(map(func, arr))

    @staticmethod
    def flat(arr: list) -> list:
        """Transforms a multi dimensional lists into a one dimensional. This
        function was not meant to be used with insanilly large lists!
        """
        result = []

        for elm in arr:
            if not isinstance(elm, list):
                result.append(elm)
                continue

            for sub in Algo.flat(elm):
                result.append(sub)

        return result


class Draw:
    """
    """
    @staticmethod
    def artists_list(artists: list[dict]) -> None:
        """
        """
        if len(artists) == 0:
            raise "Empty artists list not valid "

        print()
        for key, artist in list(enumerate(artists))[::-1]:
            name = artist["name"]
            id = artist["id"]

            div = "\033[30m|\033[m"

            print(f"\033[36m {key:<3}\033[m", div,
                  f"\033[32mhttps://music.youtube.com/channel/{id}\033[m", div,
                  f"{name}", key == 0 and "\t\033[33m(DEFAULT)\033[m" or "")
        print()


def parse_filter_string(filter: str) -> list[int]:
    """This function is a language parser that parses those range strings,
    similar to what the yay package manager does. It'll return a list of
    integers that corresponds with what selection range string the user
    provided.

    Use numbered strings, like `'4'`, or ranges with `'0-5'`, you can also
    use multiple selection types separated with `','`, e. g.: `1-5,10,20-21`.

    Invalid characeters (anything that isn't numbers or `-` and `,`) **will be
    excluded**; such as invalid range strings. Also, the result list will have
    only unique elements and empty selection results into selecting `0`.
    """
    filter = sub(r"[^0-9-,]", "", filter.replace(" ", ""))
    result = []

    if filter == "":
        return [0]

    for feat in filter.split(","):
        if feat == "":
            continue

        if "-" not in feat:
            result.append(int(feat))
            continue

        rang_strs = Algo.filter(feat.split("-"), lambda e: e)  # Exlude empty.
        rang = Algo.map(rang_strs, lambda e: int(e))

        if len(rang) != 2 or rang[0] > rang[1]:
            continue

        for num in range(rang[0], rang[1] + 1):
            result.append(num)

    return list(set(result))


class Fetch:
    """
    """
    @staticmethod
    def albums(ytmusic: YTMusic, artist_id: str) -> list[dict]:
        """
        """
        artist = ytmusic.get_artist(artist_id)
        results = []

        albums = artist["albums"]
        browse_id = albums["browseId"]
        params = albums["params"] if "params" in albums else None

        if browse_id is None:
            results = albums["results"]
        else:
            results = ytmusic.get_artist_albums(browse_id, params, limit=None)

        return [{
            "title": album["title"],
            "id": album["browseId"],
            "artist": artist["name"],
            "artist_id": artist_id
        } for album in results]

    @staticmethod
    def album_songs(ytmusic: YTMusic, album_id: str) -> list[dict]:
        """
        """
        results = ytmusic.get_album(album_id)["tracks"]

        return [{
            "title": track["title"],
            "album": track["album"],
            "video_id": track["videoId"]
        } for track in results]


def main() -> None:
    """
    """
    query = " ".join(argv[1:])  # All shell parameters becomes a single string.

    ytmusic = YTMusic()
    artists = Algo.map(ytmusic.search(query, filter="artists"),
                       lambda art: {"name": art["artist"],
                                    "id": art["browseId"]})

    if len(artists) > 1:
        Draw.artists_list(artists)

        while True:
            filter = input("Select with \033[36m12\033[m, \033[36m1-8\033[m "
                           "or \033[36m5-6,12\033[m \033[32m-$\033[m ")
            mask = parse_filter_string(filter)

            if len(mask) > 0:
                print()
                break

        artists = [art for key, art in enumerate(artists) if key in mask]

    for artist in artists:
        albums = Fetch.albums(ytmusic, artist["id"])
        album_songs = []

        for album in albums:
            album_id = album["id"]
            album_songs += Fetch.album_songs(ytmusic, album_id)

        print(dumps(album_songs, indent=2))


if __name__ == "__main__":
    main()
