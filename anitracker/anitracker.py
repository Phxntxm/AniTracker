from __future__ import annotations

import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

import requests
from aniparser import parse
from bs4 import BeautifulSoup as bs
from bs4.element import Tag
from rapidfuzz import fuzz

from anitracker import user_agent, logger, frozen_path
from anitracker.config import Config
from anitracker.media import AnimeCollection, AnimeFile, UserStatus
from anitracker.media.anime import NyaaResult, SubtitleTrack
from anitracker.sync import AniList
from anitracker.player import Player

if TYPE_CHECKING:
    from anitracker.__main__ import MainWindow

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
        self.standalone_subtitles: Dict[Tuple[str, int], str] = {}
        self._anilist.from_config(self._config)

    @property
    def animes(self) -> Dict[int, AnimeCollection]:
        return self._animes.copy()

    # I'm lazy and have to test things a lot
    @classmethod
    def _test_setup(cls):
        inst = cls()
        inst._anilist.verify()
        inst._refresh_anime_folder()
        inst.refresh_from_anilist()
        return inst

    def missing_eps(self, anime: AnimeCollection) -> str:
        have = [ep.episode_number for ep in self.get_episodes(anime)]
        missing = [f"{n}" for n in range(1, anime.episode_count + 1) if n not in have]

        return ", ".join(missing)

    def get_anime(
        self,
        title: str = "",
        *,
        id: Union[int, None] = None,
        exact_name_match: bool = False,
    ) -> Union[AnimeCollection, None]:
        if id is not None:
            return self._animes[id]
        # If there's no title, just return None
        if not title:
            return None

        # Now loop through all the names
        for anime in self.animes.values():
            if exact_name_match:
                if self._anime_is_title(anime, title, ratio=100):
                    return anime
            else:
                if self._anime_is_title(anime, title):
                    return anime

        return None

    def remove_anime(self, id: int):
        del self._animes[id]

    def refresh_from_anilist(self):
        # First get all the media
        logger.debug(f"Retrieving info from anilist")
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

        for (e_title, _), episode in self._episodes.items():
            if self._anime_is_title(anime, e_title):
                l.append(episode)

        return l

    def get_episode(
        self, anime: AnimeCollection, episode_num: int
    ) -> Optional[AnimeFile]:
        for (e_title, e_number), episode in self._episodes.items():
            # Don't try to check if this isn't even the right episode number
            if e_number != episode_num:
                continue
            # If it is the right episode number, check all the titles
            if self._anime_is_title(anime, e_title):
                return episode

        return None

    def play_episode(
        self, anime: AnimeCollection, episode_num: int, window: MainWindow
    ):
        episode = self.get_episode(anime, episode_num)

        if episode is None:
            raise TypeError(f"Could not find episode {episode_num} for {anime}")

        player = Player(anime, [episode], self, window)
        player.start()

    def start_playlist(
        self, anime: AnimeCollection, starting_episode: int, window: MainWindow
    ):
        """Starts a playlist for an anime from this episode on"""
        episodes = [
            ep
            for ep in self.get_episodes(anime)
            if ep.episode_number >= starting_episode
        ]
        episodes.sort(key=lambda e: e.episode_number)

        player = Player(anime, episodes, self, window)
        player.start()

    def _anime_is_title(
        self, anime: AnimeCollection, title: str, *, ratio: int = 80
    ) -> bool:
        """Compares an anime to a title, using a fuzzy match to try for best
        possibility of matching. This also will check all the titles of an anime"""
        for _title in anime.titles:
            if fuzz.ratio(title, _title, processor=True) >= ratio:
                return True

        return False

    def _refresh_anime_folder(self):
        try:
            dir = Path(self._config["animedir"]).expanduser()
        # No config setup for user, can't get anime
        except (KeyError, TypeError):
            return

        logger.info(f"Reloading anime folder: {dir}")
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

            data = parse(file)
            # Skip if it doesn't match the format for anime
            if not data["is_anime"] or "episode" not in data:
                continue

            # If it's a video file just yield it
            if data.get("extension", "").lower() in video_file_extensions:
                result = AnimeFile.from_data(data)
                if isinstance(result, list):
                    for r in result:
                        yield r
                elif isinstance(result, AnimeFile):
                    yield result
            # Otherwise if it's a subtitle track, store it
            if data.get("extension", "").lower() in subtitle_file_extensions:
                self.standalone_subtitles[
                    (data["anime_title"], int(data["episode"]))
                ] = str(file)

    def search_nyaa(self, query: str) -> Iterator[NyaaResult]:
        url = "https://nyaa.si/"
        params = {"f": 0, "c": "0_0", "q": query, "s": "seeders", "o": "desc"}
        headers = {"User-Agent": user_agent}

        with requests.get(url, params=params, headers=headers) as r:
            soup = bs(r.text, features="html.parser")
            body = soup.find("tbody")

            if isinstance(body, Tag):
                for result in body.findAll("tr"):
                    yield NyaaResult.from_data(result)
