from __future__ import annotations

from time import sleep
from typing import List, TYPE_CHECKING

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from anitracker.media import AnimeCollection


if TYPE_CHECKING:
    from anitracker import AniTracker
    from anitracker.media import AnimeFile

__all__ = (
    "PlayEpisode",
    "UpdateAnimeEpisodes",
    "UpdateAnimeEpisodesLoop",
    "ConnectToAnilist",
    "UpdateAnimeLists",
    "AnimeUpdateSuccess",
)


class PlayEpisode(QThread):
    def __init__(self, episode: AnimeFile, window) -> None:
        super().__init__()

        self._episode = episode
        self._window = window

    @Slot()
    def run(self):
        try:
            if self._window.app.play_episode(self._episode):
                self._window.anime_updater.start()
        except Exception as e:
            print("Exception in thread PlayEpisode")
            print(e)


class UpdateAnimeEpisodes(QThread):
    reload_anime_eps = Signal()

    def __init__(self, app: AniTracker) -> None:
        super().__init__()

        self._app = app

    @Slot()
    def run(self):
        try:
            self._app._refresh_anime_folder()
            self.reload_anime_eps.emit()
        except Exception as e:
            print("Exception in thread UpdateAnimeEpisodes")
            print(e)


class UpdateAnimeEpisodesLoop(QThread):
    reload_anime_eps = Signal()

    def __init__(self, app: AniTracker) -> None:
        super().__init__()

        self._app = app

    @Slot()
    def run(self):
        try:
            while True:
                self._app._refresh_anime_folder()
                self.reload_anime_eps.emit()
                sleep(120)
        except Exception as e:
            print("Exception in thread UpdateAnimeEpisodes")
            print(e)


class ConnectToAnilist(QThread):
    update_label = Signal(str)
    first_run = True

    def __init__(self, window) -> None:
        super().__init__()

        self._window = window

    @Slot()
    def run(self):
        try:
            # Login with anilist
            self._window.app._anilist.verify()

            if self._window.app._anilist.verify:
                self.update_label.emit(
                    f"Connected account: {self._window.app._anilist.name}"
                )

                if self.first_run:
                    self.first_run = False
                    self._window.anime_updater.start()
        except Exception as e:
            print("Exception in thread ConnectToAnilist")
            print(e)


class UpdateAnimeLists(QThread):
    handle_anime_updates = Signal(list)
    clear_table_signal = Signal()
    first_run = True

    def __init__(self, window) -> None:
        super().__init__()

        self._window = window

    @Slot()
    def run(self):
        try:
            # Load the anilist tables
            if self._window.app._anilist.authenticated:
                # First refresh from anilist
                self._window.app.refresh_from_anilist()
                # Now send all the animes
                self.handle_anime_updates.emit(list(self._window.app.animes.values()))

                if self.first_run:
                    self.first_run = False
                    self._window.update_worker.start()
        except Exception as e:
            print("Exception in thread UpdateAnimeLists")
            print(e)


class AnimeUpdateSuccess(QThread):
    toggle = Signal()

    def __init__(self, window) -> None:
        super().__init__()
        self._window = window

    @Slot()
    def run(self):
        try:
            self.toggle.emit()
            sleep(2)
            self.toggle.emit()
        except Exception as e:
            print("Exception in thread AnimeUpdateSuccess")
            print(e)
