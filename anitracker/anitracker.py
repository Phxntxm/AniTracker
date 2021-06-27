import os
import shlex
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import DefaultDict, Dict, Generator, List, Union

import ffmpeg
from fuzzywuzzy import fuzz

from anitracker.config import Config
from anitracker.media import AnimeCollection, AnimeFile, UserStatus
from anitracker.sync import AniList


class AniTracker:
    def __init__(self) -> None:
        self._config = Config()
        self._animes: Dict[int, AnimeCollection] = {}

        self._anilist = AniList()
        self._anilist.from_config(self._config)

    @property
    def animes(self) -> Dict[int, AnimeCollection]:
        return self._animes

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

        # for testing
        anime = self.animes[112609]
        anime.edit(self._anilist, notes="Test update")

    def play_episode(self, episode: AnimeFile) -> bool:
        for sub_track in episode.subtitles:
            if sub_track.language == self._config["subtitle"]:
                if sub_track.is_songs_signs and self._config["skip_songs_signs"]:
                    continue
                else:
                    self._play_episode(episode, subtitle_id=sub_track.id)
                    return

        # If we couldn't find a subtitle track, just start it
        return self._play_episode(episode)

    def _play_episode(self, episode: AnimeFile, *, subtitle_id: int = 1) -> bool:
        if sys.platform.startswith("linux"):
            # Has mpv
            if subprocess.run(["which", "mpv"], capture_output=1).returncode == 0:
                return self._play_episode_mpv(episode, subtitle_id=subtitle_id)
            else:
                self._play_episode_default_linux(episode)
                return False
        elif sys.platform.startswith("win32"):
            self._play_episode_default_windows(episode)
            return False

    def _play_episode_default_linux(self, episode: AnimeFile):
        fmt = f"xdg-open '{episode.file}'"
        cmd = self._escape_linux_command(fmt)
        subprocess.run(cmd, capture_output=True)

    def _play_episode_default_windows(self, episode: AnimeFile):
        os.startfile(episode.file)

    def _play_episode_mpv(self, episode: AnimeFile, *, subtitle_id: int = 1) -> bool:
        filename = episode.file.replace("'", r"\'")
        fmt = r"mpv --fs --sid={} --term-status-msg=':${{percent-pos}}:' '{}'".format(
            subtitle_id, filename
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
        # First skip this if it's not the next episode
        if coll.progress != episode.episode_number - 1:
            return

        # The update variables that will be sent
        vars = {"progress": coll.progress + 1}

        # Include completion if this is the last episode
        if coll.progress == coll.episode_count - 1:
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
        eps = DefaultDict(list)
        try:
            dir = Path(self._config["animedir"]).expanduser()
        # No config setup for user, can't get anime
        except (KeyError, TypeError):
            return

        # Search through directory
        for anime in self._probe_dir(dir):
            # Get the collection based on name
            collection = self.get_anime(anime.title)

            # Only update episode if we find the collection
            if collection:
                eps[collection].append(anime)

        # Now that we've searched, clear the collection's episode list then update them
        # based on the new list of episodes found
        for anime in self.animes.values():
            anime.episodes.clear()

            for ep in eps.get(anime, []):
                anime.update_episode(ep)

    def _mediainfo(self, path: Path) -> Dict:
        try:
            data = ffmpeg.probe(path)
        except ffmpeg.Error:
            return {}
        else:
            return data

    def _probe_dir(self, path: Path) -> Generator[AnimeFile, None, None]:
        for file in path.rglob("*"):
            if file.is_dir():
                continue
            data = self._mediainfo(file)
            if not data:
                continue
            anime = AnimeFile.from_data(data)

            if data:
                # Search for a video track
                for stream in data["streams"]:
                    if stream["codec_type"] == "video":
                        yield anime
                        break
