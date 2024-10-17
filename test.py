from main import InvalidRangeError, parse_range
from ytmusicapi import YTMusic
from main import search_artists, get_artist_albums, get_album_tracks
from main import get_artist_singles
import pytest

IS_TEST_API = True


def test_basic_ranges():
    assert parse_range("1,2,3") == [1, 2, 3]
    assert parse_range("1-3") == [1, 2, 3]
    assert parse_range("1-3,5-7") == [1, 2, 3, 5, 6, 7]
    assert parse_range("1,3-5,7") == [1, 3, 4, 5, 7]


def test_group_ranges():
    assert parse_range("1,2,3", group=True) == [(1,), (2,), (3,)]
    assert parse_range("1-3", group=True) == [(1, 2, 3)]
    assert parse_range("1,3-5,7", group=True) == [(1,), (3, 4, 5), (7,)]


def test_invalid_notations():
    expected_message = r"Range string with one number"
    with pytest.raises(InvalidRangeError, match=expected_message):
        parse_range("1-")

    expected_message = r"Too much numbers specified"
    with pytest.raises(InvalidRangeError, match=expected_message):
        parse_range("1-2-3")

    expected_message = r"Start greater than the end"
    with pytest.raises(InvalidRangeError, match=expected_message):
        parse_range("5-3")


def test_edge_cases():
    assert parse_range("") == []
    assert parse_range(" 1 - 3 , 5- 7 ") == [1, 2, 3, 5, 6, 7]
    assert parse_range("a1-3b, c5-7d") == [1, 2, 3, 5, 6, 7]


def test_search_artists():
    if not IS_TEST_API:
        return

    artists = search_artists(YTMusic(), "KoRn")

    assert len(artists) > 0
    assert isinstance(artists[0]["name"], str)
    assert isinstance(artists[0]["browse_id"], str)


def test_get_artist_albums():
    if not IS_TEST_API:
        return

    korn_albums = get_artist_albums(YTMusic(), "UCdSgOgQ0WtelXBMKF3tDsqg")
    jinjer_albums = get_artist_albums(YTMusic(), "UCiwWdRzbLYheWL8MD1Sn8oQ")
    kertas_api = get_artist_albums(YTMusic(), "UCWpPmz4zQa-l-vERSkSb3uA")

    assert len(korn_albums) > 0  # KoRn has a bunch of albums.
    assert len(jinjer_albums) > 0  # Jinjer only have the profile page ones.
    assert kertas_api == []  # I don't know this one, but they have no albums.
    assert isinstance(korn_albums[0]["title"], str)
    assert isinstance(jinjer_albums[0]["browse_id"], str)


def test_get_album_tracks():
    if not IS_TEST_API:
        return

    album_tracks = get_album_tracks(YTMusic(), "MPREb_QAwdQjM3puj")

    assert len(album_tracks) > 0
    assert isinstance(album_tracks[0]["title"], str)
    assert isinstance(album_tracks[0]["video_id"], str)
