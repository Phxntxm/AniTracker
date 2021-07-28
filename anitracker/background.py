from __future__ import annotations

import functools
import os
import sys
import tempfile
import traceback
from time import sleep
from typing import Any, TYPE_CHECKING, Optional, Union, List, Callable
import webbrowser

import requests
from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker import logger
from anitracker.media import AnimeCollection, Anime

if TYPE_CHECKING:
    from anitracker.__main__ import MainWindow

__all__ = (
    "BackgroundThread",
    "download_helper",
    "play_episode",
    "refresh_folder",
    "connect_to_anilist",
    "update_from_anilist",
    "status_label",
    "try_update",
    "edit_anime",
    "search_nyaa",
    "search_anilist",
    "StatusHelper",
)

# For some reason there doesn't seem to be a way to simply use a callable for a thread
# since that's all I need, this class solves that want
class BackgroundThread(QThread):
    def __init__(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        self.func = functools.partial(func, *args, **kwargs)
        self._orig = func

        super().__init__()

    @Slot()  # type: ignore
    def run(self):
        try:
            self.func()
        except Exception as e:
            logger.error(
                f"Exception thread for {self._orig}",
                exc_info=(type(e), e, e.__traceback__),
            )

            traceback.print_exc()


def download_helper(url: str):
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


def play_episode(
    anime: AnimeCollection,
    episode_number: int,
    window: MainWindow,
    *,
    start_playlist=True,
):
    if start_playlist:
        status = StatusHelper(f"Starting playlist at episode {episode_number}")
        window.statuses.append(status)
        window.app.start_playlist(anime, episode_number, window)
        window.statuses.remove(status)
    else:
        status = StatusHelper(f"Playing episode {episode_number}")
        window.statuses.append(status)
        window.app.play_episode(anime, episode_number, window)
        window.statuses.remove(status)


def refresh_folder(window: MainWindow, *, loop_forever=False):
    while True:
        status = StatusHelper("Checking anime folder...")
        window.statuses.append(status)
        window.app._refresh_anime_folder()
        window.statuses.remove(status)
        window.reload_anime_eps.emit()

        # Simply break if we're not meant to loop forever
        if not loop_forever:
            break

        sleep(120)


def connect_to_anilist(window: MainWindow):
    status = StatusHelper("Connecting to anilist...")
    window.statuses.append(status)
    # Login with anilist
    window.app._anilist.verify()

    if window.app._anilist.authenticated:
        window.update_anilist_label.emit(
            f"Connected account: {window.app._anilist.name}"
        )
        # If we authenticated at all, refresh animes
        window.anime_updater.start()

    window.statuses.remove(status)


def update_from_anilist(window: MainWindow):
    # Load the anilist tables
    if window.app._anilist.authenticated:
        status = StatusHelper("Refreshing data from anilist...")
        window.statuses.append(status)
        # First refresh from anilist
        window.app.refresh_from_anilist()

        window.handle_anime_updates.emit()

        window.statuses.remove(status)


def status_label(window: MainWindow):
    while True:
        window.update_label.emit()
        sleep(0.1)


def try_update(window: MainWindow):
    # First make sure we can actually update this
    if not getattr(sys, "frozen", False):
        raise TypeError("Cannot update, not an executable")

    # Append checking to status bar
    status = StatusHelper("Checking for update")
    window.statuses.append(status)

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
    window.statuses.remove(status)


def edit_anime(window: MainWindow, anime: Union[Anime, AnimeCollection], **kwargs):
    status = StatusHelper("Updating anime lists")
    window.statuses.append(status)
    anime.edit(window.app._anilist, **kwargs)
    window.statuses.remove(status)


def search_nyaa(window: MainWindow, query: str):
    status = StatusHelper("Searching nyaa.si")
    window.statuses.append(status)
    results = list(window.app.search_nyaa(query))
    window.nyaa_results.emit(results)
    window.statuses.remove(status)


def search_anilist(window: MainWindow, query: str):
    status = StatusHelper("Searching anilist")
    window.statuses.append(status)
    results = window.app._anilist.search_anime(query)

    for result in results:
        window.insert_row_signal.emit(window.ui.AnilistSearchResults, result)
    window.statuses.remove(status)


class StatusHelper:
    def __init__(self, status: str, color: Optional[str] = "rgb(36, 255, 36);") -> None:
        self.status = status
        self.color = color
