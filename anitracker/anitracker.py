from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING

import anitopy
import requests
from bs4 import BeautifulSoup as bs
from rapidfuzz import fuzz

from anitracker import __version__
from anitracker.config import Config
from anitracker.media import AnimeCollection, AnimeFile, UserStatus
from anitracker.media.anime import SubtitleTrack
from anitracker.sync import AniList

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
        self._standalone_subtitles: Dict[Tuple[str, int], str] = {}
        self._anilist.from_config(self._config)

    @property
    def animes(self) -> Dict[int, AnimeCollection]:
        return self._animes.copy()

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
        for _, anime in self.animes.items():
            if title:
                for a_title in [
                    anime.english_title,
                    anime.romaji_title,
                    anime.native_title,
                ]:
                    if exact_name_match and a_title.lower() == title.lower():
                        return anime
                    elif not exact_name_match and fuzz.ratio(a_title, title) > 90:
                        return anime

        return None

    def remove_anime(self, id: int):
        del self._animes[id]

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

    def get_episode(self, anime: AnimeCollection, episode_num: int) -> Optional[AnimeFile]:
        for title in anime.titles:
            episode = self._episodes.get((title, episode_num))

            if episode:
                return episode

        return None

    def play_episode(self, anime: AnimeCollection, episode_num: int, window: MainWindow):
        episode = self.get_episode(anime, episode_num)

        if episode is None:
            raise TypeError(f"Could not find episode {episode_num} for {anime}")

        # Start with just this episode
        self._play_episodes([(episode, self._get_sub_for_episode(episode))], window)

    def play_episodes(self, anime: AnimeCollection, starting_episode: int, window: MainWindow):
        """Starts a playlist for an anime from this episode on"""
        episodes: List[Tuple[AnimeFile, Optional[SubtitleTrack]]] = []

        for index in range(starting_episode, anime.episode_count + 1):
            episode = self.get_episode(anime, index)

            if episode:
                episode.load_subtitles(self._standalone_subtitles)
                episodes.append((episode, self._get_sub_for_episode(episode)))

        if episodes:
            self._play_episodes(episodes, window)

    def _get_sub_for_episode(self, episode: AnimeFile) -> Optional[SubtitleTrack]:
        for sub_track in episode.subtitles:
            if sub_track.language == self._config["subtitle"]:
                if sub_track.is_songs_signs and self._config["skip_songs_signs"]:
                    continue
                else:
                    return sub_track

        # If we're here we didn't find one that matched, so just use the first one
        if episode.subtitles:
            return episode.subtitles[0]

    def _get_mpv_command(self, episodes: List[Tuple[AnimeFile, Optional[SubtitleTrack]]]) -> List[str]:
        # Setup the command
        cmd = []
        # ATM this doesn't support more than just windows or linux
        if not sys.platform.startswith(("linux", "win32")):
            raise TypeError("Unsupported platform")

        # Add the mpv command
        if hasattr(sys, "_MEIPASS"):
            cmd.extend(shlex.split(f"{sys._MEIPASS}/mpv", posix=False))  # type: ignore
        else:
            cmd.append("mpv")

        # Add the normal flags
        cmd.extend(["--term-status-msg='Perc: ::${percent-pos}:: Pos: ::${playback-time}::'"])
        coll = self.get_anime(episodes[0][0].title, exact_name_match=True)

        # Add the subtitle and file pairs
        for ep, sub in episodes:
            cmd.append(r"--{")
            cmd.append(ep.file)
            # Append subtitle track
            if sub:
                if sub.file:
                    cmd.append(f"--sub-file={sub.file}")
                else:
                    cmd.append(f"--sid={sub.id}")
            # Append progress if we can find it
            if coll is not None:
                pos = self._config.get_option(f"{coll.id}-{ep.episode_number}", section="EpisodeProgress")
                if pos is not None:
                    cmd.append(f"--start={pos}")
            cmd.append(r"--}")

        return cmd

    def _play_episodes(self, episodes: List[Tuple[AnimeFile, Optional[SubtitleTrack]]], window: MainWindow):
        cmd = self._get_mpv_command(episodes)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        perc: int = 0
        # Starting the first episode in the playlist of course
        current_ep = episodes[0][0]

        # Parses the output of the MPV process to determine episode incrementing
        while proc.poll() is None:
            if proc.stdout is not None:
                stdout = proc.stdout.readline().decode().strip()
                # Skip if blank
                if not stdout:
                    continue
                if match := re.findall(r"Perc: ::(\d+):: Pos: ::(\d{2}:\d{2}:\d{2})::", stdout):
                    # The way this works is strange because of the escaping used
                    # to overwrite console. User friendly for viewing, not auto
                    # parsing friendly. In this same stdout line there will be every
                    # percentage update found during the watch, we want the latest (last)
                    perc_str, pos = match[-1]  # type: ignore
                    perc = int(perc_str)
                    if perc > 80:
                        self._increment_episode(current_ep, window)
                        self._remove_position_for_episode(current_ep, pos)
                    else:
                        self._save_position_for_episode(current_ep, pos)
                elif stdout.startswith("Playing: "):
                    # Now strip off the playing to get the filename
                    stdout = stdout.split("Playing: ")[1]
                    # Now find the file that matches the name
                    current_ep = next(f[0] for f in episodes if f[0].file == stdout)

            time.sleep(0.05)

    def _escape_linux_command(self, string: str) -> List[str]:
        sh = shlex.shlex(string, posix=True)
        sh.escapedquotes = "\"'"
        sh.whitespace_split = True
        return list(sh)

    def _increment_episode(self, episode: AnimeFile, window: MainWindow):
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

        # Now trigger an update of the app
        window.anime_updater.start()

    def _save_position_for_episode(self, episode: AnimeFile, position: str):
        coll = self.get_anime(episode.title, exact_name_match=True)
        if coll is not None:
            self._config.set_option(f"{coll.id}-{episode.episode_number}", position, section="EpisodeProgress")

    def _remove_position_for_episode(self, episode: AnimeFile, position: str):
        coll = self.get_anime(episode.title, exact_name_match=True)
        if coll is not None:
            self._config.remove_option(f"{coll.id}-{episode.episode_number}", section="EpisodeProgress")

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
                    result = AnimeFile.from_data(data)
                    if isinstance(result, list):
                        for r in result:
                            yield r
                    elif isinstance(result, AnimeFile):
                        yield result
                # Otherwise if it's a subtitle track, store it
                if data.get("file_extension", "").lower() in subtitle_file_extensions:
                    self._standalone_subtitles[(data["anime_title"], int(data["episode_number"]))] = str(file)

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
                        children[2].find("a", href=re.compile(r"^magnet:.*$")).get("href"),
                    ]
