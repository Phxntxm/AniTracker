import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union

import anitopy
import requests
from bs4 import BeautifulSoup as bs
from rapidfuzz import fuzz

from anitracker import __version__
from anitracker.config import Config
from anitracker.media import AnimeCollection, AnimeFile, UserStatus
from anitracker.media.anime import SubtitleTrack
from anitracker.sync import AniList

video_file_extensions = [
    "webm",
    "mkv",
    "flv",
    "flv",
    "vob",
    "ogv",
    "ogg",
    "drc",
    "gif",
    "gifv",
    "mng",
    "avi",
    "mts",
    "m2ts",
    "ts",
    "mov",
    "qt",
    "wmv",
    "yuv",
    "rm",
    "rmvb",
    "viv",
    "asf",
    "amv",
    "mp4",
    "m4p",
    "m4v",
    "mpg",
    "mp2",
    "mpeg",
    "mpe",
    "mpv",
    "mpg",
    "mpeg",
    "m2v",
    "m4v",
    "svi",
    "3gp",
    "3g2",
    "mxf",
    "roq",
    "nsv",
    "flv",
    "f4v",
    "f4p",
    "f4a",
    "f4b",
]
subtitle_file_extensions = ["ass", "cmml", "lrc", "sami", "ttml", "srt", "ssa", "usf"]


class AniTracker:
    def __init__(self) -> None:
        self._config = Config()
        self._animes: Dict[int, AnimeCollection] = {}

        self._anilist = AniList()
        self._episodes: Dict[Tuple[str, int], AnimeFile] = {}
        self._standalone_subtitles: Dict[Tuple[str, int], str] = {}
        self._anilist.from_config(self._config)

    @property
    def animes(self) -> Dict[int, AnimeCollection]:
        return self._animes

    def missing_eps(self, anime: AnimeCollection) -> str:
        have = [ep.episode_number for ep in self.get_episodes(anime)]
        missing = [f"{n}" for n in range(1, anime.episode_count) if n not in have]

        return ", ".join(missing)

    def get_anime(
        self, title: str = "", id: Union[int, None] = None
    ) -> Union[AnimeCollection, None]:
        if id is not None:
            return self._animes[id]
        for _, anime in self.animes.items():
            if title:
                for a_title in [
                    anime.english_title,
                    anime.romaji_title,
                    anime.native_title,
                ]:
                    if fuzz.ratio(a_title, title) > 90:
                        return anime

        return None

    def refresh_from_anilist(self):
        # First get all the media
        media = self._anilist.get_collection()

        # Now, there is no harm in leaving stale data... so all we're going to do is update
        # the ones we find, and add the new ones

        # The lists are separated by status
        for l in media["data"]["MediaListCollection"]["lists"]:
            for entry in l["entries"]:
                old = self._animes.get(entry["mediaId"])

                if old:
                    old.update_data(entry)
                else:
                    anime = AnimeCollection.from_data(entry)

                    self._animes[anime.id] = anime

    def get_episodes(self, anime: AnimeCollection) -> List[AnimeFile]:
        l = []

        for key, value in self._episodes.items():
            if key[0] in anime.titles:
                l.append(value)

        return l

    def get_episode(
        self, anime: AnimeCollection, episode_num: int
    ) -> Optional[AnimeFile]:
        for title in anime.titles:
            episode = self._episodes.get((title, episode_num))

            if episode:
                return episode

        return None

    def play_episode(self, anime: AnimeCollection, episode_num: int) -> bool:
        episode = self.get_episode(anime, episode_num)

        if episode is None:
            return False

        # Load the subtitles for this file before proceeding
        episode.load_subtitles(self._standalone_subtitles)

        for sub_track in episode.subtitles:
            if sub_track.language == self._config["subtitle"]:
                if sub_track.is_songs_signs and self._config["skip_songs_signs"]:
                    continue
                else:
                    return self._play_episode(episode, subtitle=sub_track)

        # Next check if there ARE subtitles, if we couldn't find one that
        # matches, but there is one... choose the first
        if episode.subtitles:
            return self._play_episode(episode, subtitle=episode.subtitles[0])

        # If we couldn't find a subtitle track, just start it
        return self._play_episode(episode)

    def _play_episode(
        self, episode: AnimeFile, *, subtitle: Optional[SubtitleTrack] = None
    ) -> bool:
        if sys.platform.startswith("linux"):
            # Has mpv
            if subprocess.run(["which", "mpv"], capture_output=True).returncode == 0:
                return self._play_episode_mpv(episode, subtitle=subtitle)
            else:
                self._play_episode_default_linux(episode)
                return False
        elif sys.platform.startswith("win32"):
            self._play_episode_default_windows(episode)
            return False

        return False

    def _play_episode_default_linux(self, episode: AnimeFile):
        fmt = f"xdg-open '{episode.file}'"
        cmd = self._escape_linux_command(fmt)
        subprocess.run(cmd, capture_output=True)

    def _play_episode_default_windows(self, episode: AnimeFile):
        f = episode.file.replace("/", "\\")
        subprocess.run(["start", f'"{f}"'])

    def _play_episode_mpv(
        self, episode: AnimeFile, *, subtitle: Optional[SubtitleTrack] = None
    ) -> bool:
        filename = episode.file.replace("'", r"\'")

        if subtitle is not None:
            if subtitle.file is not None:
                fmt = r"mpv --fs --sub-file='{}' --term-status-msg=':${{percent-pos}}:' '{}'".format(
                    subtitle.file, filename
                )
            else:
                fmt = r"mpv --fs --sid={} --term-status-msg=':${{percent-pos}}:' '{}'".format(
                    subtitle.id, filename
                )
        else:
            fmt = r"mpv --fs --term-status-msg=':${{percent-pos}}:' '{}'".format(
                filename
            )
        cmd = self._escape_linux_command(fmt)

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        between_colon: bool = False
        buffer: str = ""
        perc: int = 0

        # This entire thing is for reading the status message, to determine
        # percentage through the episode.... with that we determine if we want to
        # set this episode as completed
        while proc.poll() is None:
            if proc.stderr is not None:
                c = proc.stderr.read(1).decode()
                # Percentage looks like this :50:
                # We need to mark beginning and end, because spaces/newlines
                # when doing overwriting text in console is inconsistent
                if c == ":":
                    # If we're already between colons, this is the end
                    if between_colon:
                        # Turn the buffer into a number
                        perc = int(buffer)
                        # Reset the buffer
                        buffer = ""
                        between_colon = False
                    # This is the start to a new buffer
                    else:
                        between_colon = True
                # If it's a digit add to the buffer
                elif c.isdigit():
                    buffer += c
            time.sleep(0.1)

        if perc > 80:
            self._increment_episode(episode)
            return True
        else:
            return False

    def _escape_linux_command(self, string: str) -> List[str]:
        sh = shlex.shlex(string, posix=True)
        sh.escapedquotes = "\"'"
        sh.whitespace_split = True
        return list(sh)

    def _increment_episode(self, episode: AnimeFile):
        coll = self.get_anime(episode.title)
        if coll is None:
            return

        # First skip this if it's not the next episode
        if coll.progress != episode.episode_number - 1:
            return

        # The update variables that will be sent
        vars: Dict[str, Any] = {"progress": episode.episode_number}

        # Include completion if this is the last episode
        if episode.episode_number == coll.episode_count:
            if coll.user_status == UserStatus.REPEATING:
                vars["status"] = UserStatus.COMPLETED
                vars["repeat"] = coll.repeat + 1
            else:
                vars["status"] = UserStatus.COMPLETED
                vars["completed_at"] = datetime.now().date()
        # If this was the first episode, include started at
        if coll.progress == 0 and coll.user_status is not UserStatus.REPEATING:
            vars["started_at"] = datetime.now().date()

        coll.edit(self._anilist, **vars)

    def _refresh_anime_folder(self):
        try:
            dir = Path(self._config["animedir"]).expanduser()
        # No config setup for user, can't get anime
        except (KeyError, TypeError):
            return

        # Clear the dict
        self._episodes.clear()
        # Search through directory
        for anime in self._probe_dir(dir):
            self._episodes[(anime.title, anime.episode_number)] = anime

    def _probe_dir(self, path: Path) -> Generator[AnimeFile, None, None]:
        # Look at every file in the path
        for file in path.rglob("*"):
            # Ignore directories, recursion is handled by rglob
            if file.is_dir():
                continue

            try:
                data = anitopy.parse(file.name)
            except ValueError:
                continue
            else:
                # If we couldn't parse it, continue
                if data is None:
                    continue
                # Skip if it doesn't match the format for anime
                if not (data.get("anime_title") and data.get("episode_number")):
                    continue

                # At this point it's probably a file we care about, whether that's a video or
                # a subtitle track.. so throw the filename in there
                data["file_name"] = str(file)

                # If it's a video file just yield it
                if data.get("file_extension", "").lower() in video_file_extensions:
                    yield AnimeFile.from_data(data)
                # Otherwise if it's a subtitle track, store it
                if data.get("file_extension", "").lower() in subtitle_file_extensions:
                    self._standalone_subtitles[
                        (data["anime_title"], int(data["episode_number"]))
                    ] = str(file)

    def search_nyaa(self, query: str) -> Iterator[List]:
        url = "https://nyaa.si/"
        params = {"f": 0, "c": "0_0", "q": query, "s": "seeders", "o": "desc"}
        headers = {"User-Agent": f"AniTracker/{__version__} (Language=py)"}

        with requests.get(url, params=params, headers=headers) as r:
            soup = bs(r.text, features="html.parser")
            body = soup.find("tbody")

            if body is not None:
                for result in body.findAll("tr"):
                    children = result.findAll("td")

                    yield [
                        children[1].find("a", href=re.compile(r"^/view/\d+$")).text,
                        children[3].text,
                        children[4].text,
                        children[5].text,
                        children[6].text,
                        children[7].text,
                        children[2]
                        .find("a", href=re.compile(r"^magnet:.*$"))
                        .get("href"),
                    ]
