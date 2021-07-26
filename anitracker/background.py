from __future__ import annotations

import os
import sys
import tempfile
import traceback
from time import sleep
from typing import TYPE_CHECKING, Optional, Union, List
import webbrowser

import requests
from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker.media import AnimeCollection, Anime

if TYPE_CHECKING:
    from anitracker.__main__ import MainWindow

__all__ = (
    "PlayEpisode",
    "PlayEpisodes",
    "UpdateAnimeEpisodes",
    "UpdateAnimeEpisodesLoop",
    "ConnectToAnilist",
    "UpdateAnimeLists",
    "AnimeUpdateSuccess",
    "StatusLabelUpdater",
    "UpdateChecker",
    "EditAnime",
    "StatusHelper",
    "SearchNyaa",
    "SearchAnilist",
)


class PlayEpisode(QThread):
    def __init__(self, anime: AnimeCollection, episode_number: int, window: MainWindow) -> None:
        super().__init__()

        self._anime = anime
        self._episode = episode_number
        self._window = window

    @Slot()  # type: ignore
    def run(self):
        status = StatusHelper(f"Playing episode {self._episode}")
        self._window.statuses.append(status)
        self._window.app.play_episode(self._anime, self._episode, self._window)
        self._window.statuses.remove(status)


class PlayEpisodes(QThread):
    def __init__(self, anime: AnimeCollection, starting_episode: int, window: MainWindow) -> None:
        super().__init__()

        self._anime = anime
        self._episode = starting_episode
        self._window = window

    @Slot()  # type: ignore
    def run(self):
        status = StatusHelper(f"Starting playlist from episode {self._episode}")
        self._window.statuses.append(status)
        self._window.app.play_episodes(self._anime, self._episode, self._window)
        self._window.statuses.remove(status)


class UpdateAnimeEpisodes(QThread):
    reload_anime_eps = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()  # type: ignore
    def run(self):
        try:
            status = StatusHelper("Checking anime folder...")
            self._window.statuses.append(status)
            self._window.app._refresh_anime_folder()
            self._window.statuses.remove(status)
            self.reload_anime_eps.emit()  # type: ignore
        except:
            traceback.print_exc()


class UpdateAnimeEpisodesLoop(QThread):
    reload_anime_eps = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()  # type: ignore
    def run(self):
        try:
            while True:
                status = StatusHelper("Checking anime folder...")
                self._window.statuses.append(status)
                self._window.app._refresh_anime_folder()
                self._window.statuses.remove(status)
                self.reload_anime_eps.emit()  # type: ignore
                sleep(120)
        except:
            traceback.print_exc()


class ConnectToAnilist(QThread):
    update_label = Signal(str)

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()  # type: ignore
    def run(self):
        try:
            status = StatusHelper("Connecting to anilist...")
            self._window.statuses.append(status)
            # Login with anilist
            self._window.app._anilist.verify()

            if self._window.app._anilist.authenticated:
                self.update_label.emit(f"Connected account: {self._window.app._anilist.name}")  # type: ignore
                # If we authenticated at all, refresh animes
                self._window.anime_updater.start()

            self._window.statuses.remove(status)
        except:
            traceback.print_exc()


class UpdateAnimeLists(QThread):
    handle_anime_updates = Signal()
    clear_table_signal = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()  # type: ignore
    def run(self):
        try:
            # Load the anilist tables
            if self._window.app._anilist.authenticated:
                status = StatusHelper("Refreshing data from anilist...")
                self._window.statuses.append(status)
                # First refresh from anilist
                self._window.app.refresh_from_anilist()

                self.handle_anime_updates.emit()  # type: ignore

                self._window.statuses.remove(status)
        except:
            traceback.print_exc()


class AnimeUpdateSuccess(QThread):
    toggle = Signal()

    def __init__(self) -> None:
        super().__init__()

    @Slot()  # type: ignore
    def run(self):
        try:
            self.toggle.emit()  # type: ignore
            sleep(2)
            self.toggle.emit()  # type: ignore
        except:
            traceback.print_exc()


class StatusLabelUpdater(QThread):
    update = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window

    @Slot()  # type: ignore
    def run(self):
        try:
            while True:
                self.update.emit()  # type: ignore
                sleep(0.1)
        except:
            traceback.print_exc()


class UpdateChecker(QThread):
    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window

    def download_helper(self, url: str):
        # Get the application path
        application_path = os.path.abspath(sys.executable)
        # Open tmp file, don't delete after
        with tempfile.NamedTemporaryFile(delete=False) as f:
            # Stream request to get update of download progress
            with requests.get(url, stream=True) as downloaded:
                # Setup bytes info
                total_size = int(downloaded.headers.get("content-length", 0))
                block_size = 1024
                total_downloaded = 0

                for block in downloaded.iter_content(block_size):
                    total_downloaded += len(block)

                    f.write(block)

                    yield f"Downloaded {total_downloaded/1000000:.2f}/{total_size/1000000:.2f} MB"

            # Done downloading, replace executable
            if sys.platform.startswith("linux"):
                os.replace(f.name, application_path)
                os.chmod(application_path, 0o775)
                exe_path = application_path
            # On windows, next reboot it will detect the file situation and replace it
            elif sys.platform.startswith("win32"):
                os.rename(application_path, f"{application_path}.bak")
                exe_path = f"{application_path}.bak"
            else:
                yield "Unsupported platform"
                return

            yield "Download finished! Restarting in 3 seconds"
            sleep(3)
            os.execv(exe_path, sys.argv)

    @Slot()  # type: ignore
    def run(self):
        try:
            # First make sure we can actually update this
            if not getattr(sys, "frozen", False):
                raise TypeError("Cannot update, not an executable")

            # Append checking to status bar
            status = StatusHelper("Checking for update")
            self._window.statuses.append(status)

            # Get latest version from URL
            with requests.get("https://github.com/Phxntxm/AniTracker/releases/latest") as r:
                version = r.url.rsplit("v")[1]

            from anitracker import __version__

            # There should only ever be the latest, so if they're not equal at all
            # then there should be an update
            if version != __version__:
                # Append running update to statuses
                status.status = "Preparing update"

                # Linux
                if sys.platform.startswith("linux"):
                    url = "https://github.com/Phxntxm/AniTracker/releases/latest/download/anitracker"
                # Windows
                else:
                    url = "https://github.com/Phxntxm/AniTracker/releases/latest/download/AniTrackerSetup.exe"

                webbrowser.open(url)

                # Let them know we're done
                sleep(5)
            else:
                status.status = "Already up to date!"
                sleep(2)

            # After all is said and done, remove our status
            self._window.statuses.remove(status)

        except:
            traceback.print_exc()


class EditAnime(QThread):
    def __init__(self, window: MainWindow, anime: Union[Anime, AnimeCollection], **kwargs):
        super().__init__()
        self._window = window
        self._anime = anime

        self._params = kwargs

    @Slot()  # type: ignore
    def run(self):
        try:
            status = StatusHelper("Updating anime lists")
            self._window.statuses.append(status)
            self._anime.edit(self._window.app._anilist, **self._params)
            self._window.statuses.remove(status)
        except:
            traceback.print_exc()


class SearchNyaa(QThread):
    nyaa_results = Signal(list)

    def __init__(self, window: MainWindow, query: str) -> None:
        super().__init__()
        self._window = window
        self._query = query

    @Slot()  # type: ignore
    def run(self):
        status = StatusHelper("Searching nyaa.si")
        self._window.statuses.append(status)
        results = list(self._window.app.search_nyaa(self._query))
        self.nyaa_results.emit(results)  # type: ignore
        self._window.statuses.remove(status)


class SearchAnilist(QThread):
    def __init__(self, window: MainWindow, query: str) -> None:
        super().__init__()
        self._window = window
        self._query = query

    @Slot()  # type: ignore
    def run(self):
        status = StatusHelper("Searching anilist")
        self._window.statuses.append(status)
        results = self._window.app._anilist.search_anime(self._query)
        for result in results:
            self._window.insert_row_signal.emit(self._window.ui.AnilistSearchResults, result)  # type: ignore
        self._window.statuses.remove(status)


class StatusHelper:
    def __init__(self, status: str, color: Optional[str] = "rgb(36, 255, 36);") -> None:
        self.status = status
        self.color = color
