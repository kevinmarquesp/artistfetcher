# artistfetcher

I was a little annoyed that some of the indie artists I follow on YouTube Music
were removing some of their songs from the platform. Besides that, I was also
frustrated that we don't really own much these days; if YouTube, Spotify, or
others decide to shut down their servers, they can.

So, I created this simple Python script that compiles (doesn't necessarily
download) all publications of a desired artist into a JSON file. This makes it
easy to fetch more information from there. The JSON file design allows users to
download content in whatever way they prefer. Here's an example of a line from
this file:

```json
{
  "artist_name":      "Korn",
  "artist_browse_id": "UCdSgOgQ0WtelXBMKF3tDsqg",
  "song_title":       "Love & Meth",
  "song_video_id":    "851NxKsneFk",
  "album_title":      "The Paradigm Shift",
  "album_browse_id":  "MPREb_UUPBhNFZYrL",
  "local_path":       "Korn/Albums/The_Paradigm_Shift"
}
```

It's as simple as that. Now you can use [`jq`](https://github.com/jqlang/jq), or
your favorite programming language, to interpret the data and download the song
wherever you want. There's even a `local_path` attribute with sanitized
directory names that might be useful for you!

> [!NOTE]
> Check out the `download.sh` script — you can use it to download all songs from
> an artist into a specific target folder. Feel free to use it as a template for
> your own scripts! If you think of something useful to add, like a script that
> fetches song lyrics, don't hesitate to make a pull request here. ❤️


## Steps to run this script

1.  Make sure you have the `ytmusicapi` Python package installed. Run `python3
    -m pip install ytmusicapi` to install it.
2.  Run the `main.py` script and pass the artist's name you want to search for.
    Once it finishes, it will generate a `[ARTIST NAME].json` file in the
    current directory.

Now you have all the data from this specific artist in one file. If you want to
download everything, you can use the helper `download.sh` script, which uses the
[`yt-dlp`](https://github.com/yt-dlp/yt-dlp) tool.

3.  Run `./download.sh . ~/Music` — the first argument is where all the `.json`
    files are located, and the second argument is the path where everything
    should be downloaded.


## Reference Manual

Usage: `artistfetcher [-h] [--target TARGET] [query ...]`

Positional arguments:  
+   `[query]`: The artist search query.

Options:  
+   `-h`, `--help`: Show this help message and exit.  
+   `--target`, `-t TARGET`: Directory where the artist's JSON files should be stored.
