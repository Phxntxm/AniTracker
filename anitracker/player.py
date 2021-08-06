from __future__ import annotations

from datetime import datetime
import re
import shlex
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple, Any, Dict

from anitracker import frozen_path, logger
from anitracker.utilities import UserStatus

if TYPE_CHECKING:
    from anitracker import AniTracker
    from anitracker.__main__ import MainWindow
    from anitracker.media import AnimeCollection, AnimeFile, SubtitleTrack

    EPISODE_TYPE = List[Tuple[AnimeFile, Optional[SubtitleTrack]]]


class Player:
    def __init__(
        self,
        anime: AnimeCollection,
        episodes: List[AnimeFile],
        parent: AniTracker,
        window: MainWindow,
    ) -> None:
        self.anime = anime
        self._window = window
        self._parent = parent
        self._standalone_episodes = episodes

        self._cached_episodes: Optional[EPISODE_TYPE] = None

    @property
    def episodes(self) -> EPISODE_TYPE:
        if self._cached_episodes is not None:
            return self._cached_episodes

        eps = []

        for ep in self._standalone_episodes:
            ep.load_subtitles(self._parent.standalone_subtitles)
            sub = self._get_sub_for_episode(ep)

            eps.append((ep, sub))

        self._cached_episodes = eps
        return eps

    @property
    def mpv(self) -> List[str]:
        # Setup the command
        cmd = []
        # ATM this doesn't support more than just windows or linux
        if not sys.platform.startswith(("linux", "win32")):
            raise TypeError("Unsupported platform")

        # Add the mpv command
        if frozen_path is not None:
            cmd.extend(shlex.split(f"{frozen_path}/mpv", posix=not sys.platform.startswith("win32")))  # type: ignore
        else:
            cmd.append("mpv")

        # Add the language priority
        cmd.append("--alang=jpn,en")

        # Smooths things out for larger playlists
        cmd.extend(["--profile=sw-fast", "--hwdec=auto"])

        # Add the status message
        cmd.extend(
            ["--term-status-msg='Perc: ::${percent-pos}:: Pos: ::${playback-time}::'"]
        )

        # Add the subtitle and file pairs
        for ep, sub in self.episodes:
            cmd.append(r"--{")
            cmd.append(ep.file)
            # Append subtitle track
            if sub:
                if sub.file:
                    cmd.append(f"--sub-file={sub.file}")
                else:
                    cmd.append(f"--sid={sub.id}")
            # Append progress if we can find it
            pos = self._parent._config.get_option(
                f"{self.anime.id}-{ep.episode_number}", section="EpisodeProgress"
            )
            if pos is not None:
                cmd.append(f"--start={pos}")
            cmd.append(r"--}")

        return cmd

    def start(self):
        episodes = list(self.episodes)

        logger.info(f"Running mpv command: {self.mpv}")

        proc = subprocess.Popen(
            self.mpv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )

        perc: int = 0
        last_updated: float = time.monotonic()
        # Start at the first episode in the playlist of course
        current_ep = episodes[0][0]

        # Parses the output of the MPV process to determine episode incrementing
        while proc.poll() is None:
            if proc.stdout is not None:
                stdout = proc.stdout.readline().decode().strip()
                # Skip if blank
                if not stdout:
                    continue
                if match := re.findall(
                    r"Perc: ::(\d+):: Pos: ::(\d{2}:\d{2}:\d{2})::", stdout
                ):
                    # The way this works is strange because of the escaping used
                    # to overwrite console. User friendly for viewing, not auto
                    # parsing friendly. In this same stdout line there will be every
                    # percentage update found during the watch, we want the latest (last)
                    perc_str, pos = match[-1]  # type: ignore
                    perc = int(perc_str)
                    if perc > 80:
                        now = time.monotonic()
                        # To prevent race conditions, lets ensure we don't try to update
                        # more than once in the span of 2 seconds. I've seen weird cases
                        # where the output sends the percentage for the previous episode
                        # at the exact time that it switches episodes. The order of my
                        # checking of things should prevent that causing an issue, but I've
                        # twice in hundreds of tests where the order seemed wrong. Realistically,
                        # sounds like a probable bug in MPV but unrealistic to get fixed as it
                        # will be low priority due to how niche it is
                        if now - last_updated > 2:
                            logger.info(
                                f"Updating episode {current_ep}, progress was {perc}%"
                            )
                            self._increment_episode(current_ep)
                        self._remove_position_for_episode(current_ep, self.anime, pos)
                        last_updated = now
                    else:
                        self._save_position_for_episode(current_ep, self.anime, pos)
                elif stdout.startswith("Playing: "):
                    # Now strip off the playing to get the filename
                    stdout = stdout.split("Playing: ")[1]
                    # Now find the file that matches the name
                    current_ep = next(f[0] for f in episodes if f[0].file == stdout)

            time.sleep(0.05)

    def _get_sub_for_episode(self, episode: AnimeFile) -> Optional[SubtitleTrack]:
        # If there's no subtitles, return None
        if not episode.subtitles:
            return None
        # Create copy so that we can pop safely
        subs = episode.subtitles.copy()
        # Set up a priority system, starting with least to most priority
        # Set the very first episode as the first priority
        priority = subs.pop(0)

        # Check if we want to skip songs_signs, and we have a songs/signs one
        # if we do, we want to skip it as priority if there is a non-songs/signs
        if self._parent._config["skip_songs_signs"] and priority.is_songs_signs:
            # Loop through all the leftover subs
            for sub_track in subs:
                # If we found one that's not signs/subs then set that as priority
                if not sub_track.is_songs_signs:
                    priority = sub_track
                    subs.pop(subs.index(priority))
                    break

        # If this is also the language we want, then we don't need to
        # do any more searching
        if self._parent._config["subtitle"] != priority.language:
            # Means our priority set isn't the language we want, so try to find one
            for sub_track in subs:
                if sub_track.language == self._parent._config["subtitle"]:
                    priority = sub_track
                    break

        # Now return whatever our highest priority was
        logger.info(f"Using subtitle track {priority} for episode {episode}")
        return priority

    def _increment_episode(self, episode: AnimeFile):
        # First skip this if it's not the next episode
        if self.anime.progress != episode.episode_number - 1:
            return

        # The update variables that will be sent
        vars: Dict[str, Any] = {"progress": episode.episode_number}

        # Include completion if this is the last episode
        if episode.episode_number == self.anime.episode_count:
            if self.anime.user_status == UserStatus.REPEATING:
                vars["status"] = UserStatus.COMPLETED
                vars["repeat"] = self.anime.repeat + 1
            else:
                vars["status"] = UserStatus.COMPLETED
                vars["completed_at"] = datetime.now().date()
        # If this was the first episode, include started at
        if (
            self.anime.progress == 0
            and self.anime.user_status is not UserStatus.REPEATING
        ):
            vars["started_at"] = datetime.now().date()

        self.anime.edit(self._parent._anilist, **vars)

        # Now trigger an update of the app
        self._window.anime_updater.start()

    def _save_position_for_episode(
        self, episode: AnimeFile, anime: AnimeCollection, position: str
    ):
        self._parent._config.set_option(
            f"{anime.id}-{episode.episode_number}",
            position,
            section="EpisodeProgress",
        )

    def _remove_position_for_episode(
        self, episode: AnimeFile, anime: AnimeCollection, position: str
    ):
        self._parent._config.remove_option(
            f"{anime.id}-{episode.episode_number}", section="EpisodeProgress"
        )
