from __future__ import annotations

import functools
import os
import sys
import tempfile
import traceback
from time import sleep
from typing import TYPE_CHECKING, Optional, Union, List

import requests
from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker.media import AnimeCollection, Anime

if TYPE_CHECKING:
    from anitracker.__main__ import MainWindow

__all__ = (
    "PlayEpisode",
    "UpdateAnimeEpisodes",
    "UpdateAnimeEpisodesLoop",
    "ConnectToAnilist",
    "UpdateAnimeLists",
    "AnimeUpdateSuccess",
    "StatusLabelUpdater",
    "UpdateChecker",
    "EditAnime",
    "StatusHelper",
)


class PlayEpisode(QThread):
    def __init__(
        self, anime: AnimeCollection, episode_number: int, window: MainWindow
    ) -> None:
        super().__init__()

        self._anime = anime
        self._episode = episode_number
        self._window = window

    @Slot()
    def run(self):
        try:
            if self._window.app.play_episode(self._anime, self._episode):
                self._window.anime_updater.start()
        except:
            traceback.print_exc()


class UpdateAnimeEpisodes(QThread):
    reload_anime_eps = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()
    def run(self):
        try:
            status = StatusHelper("Checking anime folder...")
            self._window.statuses.append(status)
            self._window.app._refresh_anime_folder()
            self._window.statuses.remove(status)
            self.reload_anime_eps.emit()
        except:
            traceback.print_exc()


class UpdateAnimeEpisodesLoop(QThread):
    reload_anime_eps = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()
    def run(self):
        try:
            while True:
                status = StatusHelper("Checking anime folder...")
                self._window.statuses.append(status)
                self._window.app._refresh_anime_folder()
                self._window.statuses.remove(status)
                self.reload_anime_eps.emit()
                sleep(120)
        except:
            traceback.print_exc()


class ConnectToAnilist(QThread):
    update_label = Signal(str)
    first_run = True

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()
    def run(self):
        try:
            status = StatusHelper("Connecting to anilist...")
            self._window.statuses.append(status)
            # Login with anilist
            self._window.app._anilist.verify()

            if self._window.app._anilist.verify:
                self.update_label.emit(
                    f"Connected account: {self._window.app._anilist.name}"
                )

                if self.first_run:
                    self.first_run = False
                    self._window.anime_updater.start()
                    self._window._update_anime_files_loop.start()
            self._window.statuses.remove(status)
        except:
            traceback.print_exc()


class UpdateAnimeLists(QThread):
    handle_anime_updates = Signal(list)
    clear_table_signal = Signal()
    first_run = True

    def __init__(self, window: MainWindow) -> None:
        super().__init__()

        self._window = window

    @Slot()
    def run(self):
        try:
            # Load the anilist tables
            if self._window.app._anilist.authenticated:
                status = StatusHelper("Refreshing data from anilist...")
                self._window.statuses.append(status)
                # First refresh from anilist
                self._window.app.refresh_from_anilist()

                if self.first_run:
                    self.first_run = False
                    self._window.update_worker.start()

                self._window.statuses.remove(status)
        except:
            traceback.print_exc()


class AnimeUpdateSuccess(QThread):
    toggle = Signal()

    def __init__(self) -> None:
        super().__init__()

    @Slot()
    def run(self):
        try:
            self.toggle.emit()
            sleep(2)
            self.toggle.emit()
        except:
            traceback.print_exc()


class StatusLabelUpdater(QThread):
    update = Signal()

    def __init__(self, window: MainWindow) -> None:
        super().__init__()
        self._window = window

    @Slot()
    def run(self):
        try:
            while True:
                self.update.emit()
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

            yield "Download finished! Restarting in 3 seconds"
            sleep(3)
            os.execv(exe_path, sys.argv)

    @Slot()
    def run(self):
        try:
            # First make sure we can actually update this
            if not getattr(sys, "frozen", False):
                raise TypeError("Cannot update, not an executable")

            # Append checking to status bar
            status = StatusHelper("Checking for update")
            self._window.statuses.append(status)

            # Get latest version from URL
            with requests.get(
                "https://github.com/Phxntxm/AniTracker/releases/latest"
            ) as r:
                version = r.url.rsplit("v")[1]

            from anitracker import __version__

            # There should only ever be the latest, so if they're not equal at all
            # then there should be an update
            if version != __version__:
                # Append running update to statuses
                status.status = "Preparing update"

                # On linux, write to temp file then replace once it's done
                if sys.platform.startswith("linux"):
                    url = "https://github.com/Phxntxm/AniTracker/releases/latest/download/anitracker"
                # On windows
                else:
                    url = "https://github.com/Phxntxm/AniTracker/releases/latest/download/anitracker.exe"

                # Update status for each update in the download streamer
                for update in self.download_helper(url):
                    status.status = update

                # Let them know we're done
                status.status = "Update successful! You can restart now"
                sleep(5)
            else:
                status.status = "Already up to date!"
                sleep(2)

            # After all is said and done, remove our status
            self._window.statuses.remove(status)

        except:
            traceback.print_exc()


class EditAnime(QThread):
    def __init__(
        self, window: MainWindow, anime: Union[Anime, AnimeCollection], **kwargs
    ):
        super().__init__()
        self._window = window
        self._anime = anime

        self._params = kwargs

    @Slot()
    def run(self):
        try:
            status = StatusHelper("Updating anime lists")
            self._window.statuses.append(status)
            self._anime.edit(self._window.app._anilist, **self._params)
            self._window.statuses.remove(status)
        except:
            traceback.print_exc()


class UpdateTablesForAnimes(QThread):
    def __init__(self, window: MainWindow, animes: List[AnimeCollection]):
        self._window = window
        self._animes = animes

    @Slot()
    def run(self):
        # First, handle any animes in the tables but not in the list of animes
        for table in self._window.tables:
            # Reverse through the range, so that removal of rows
            # doesn't mess up what we're looking at
            for row in range(table.rowCount() - 1, -1, -1):
                anime: AnimeCollection = table.item(row, 0).anime  # type: ignore

                # If the anime is not in the list, remove it from the table
                if anime not in self._animes:
                    self._window.update_ui_signal.emit(
                        functools.partial(table.removeRow, row)
                    )
                # Otherwise if this table doesn't match the anime's status, remove it
                elif self._window.get_table(anime.user_status) != table:
                    self._window.update_ui_signal.emit(
                        functools.partial(table.removeRow, row)
                    )

        # Now loop through the animes and handle all the updates
        for anime in self._animes:
            found = False
            table = self._window.get_table(anime.user_status)

            # Loop through every row in the table it should be in
            for row in range(table.rowCount()):
                # Found it
                if table.item(row, 0).anime == anime:
                    found = True
                    self._window.update_row_signal.emit(table, row, anime)  # type: ignore

            # If we didn't find it, then insert it
            if not found:
                self._window.insert_row_signal.emit(table, anime)  # type: ignore

        # Make sure things are sorted properly
        for table in self._window.tables:
            if table.isSortingEnabled():
                # This will immediately trigger a sort based on the sort option
                # selected, so we just set it to True again, since as far as I can
                # tell there's no way to GET the current sort option
                table.setSortingEnabled(True)


class StatusHelper:
    def __init__(self, status: str, color: Optional[str] = "rgb(36, 255, 36);") -> None:
        self.status = status
        self.color = color
