from __future__ import annotations

import functools
import os
import shutil
import sys
import tempfile
import traceback
from time import sleep
from typing import Any, TYPE_CHECKING, Optional, Union, Callable, Iterator, List

import requests
from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker import logger, frozen_path
from anitracker.media import AnimeCollection, Anime, AnimeFile
from anitracker.utilities import subprocess

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
    "generate_thumbnails",
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


def download_helper(url: str) -> Iterator[str]:
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

            # Now do the update
            yield "Download finished! Preparing update!"

            yield from do_update(f)


def do_update(f: tempfile._TemporaryFileWrapper[bytes]) -> Iterator[str]:
    if frozen_path is None:
        return
    # frozen_path is the path to the actual file installation. Not where it was untarred
    # the tar and installing scripts are one directory higher
    path = os.path.dirname(frozen_path)

    if sys.platform.startswith("linux"):

        # Untar
        subprocess.run(["tar", "xzf", f.name, "-C", path])
        # Run the finish setup
        subprocess.run([f"{path}/finish-setup.sh"], shell=True)
        yield "Installation prepared, restarting in 3 seconds"
        sleep(3)
        os.execv(f"{frozen_path}/anitracker", sys.argv)
    elif sys.platform.startswith("win32"):
        shutil.move(f.name, path)
        yield "Download finished, run installation file that has been downloaded"


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
            url = "https://github.com/Phxntxm/AniTracker/releases/latest/download/anitracker.tar.gz"
        # Windows
        else:
            url = "https://github.com/Phxntxm/AniTracker/releases/latest/download/AniTrackerSetup.exe"

        # Update status for each update in the download streamer
        for update in download_helper(url):
            status.status = update
    else:
        status.status = "Already up to date!"
        sleep(2)

    # After all is said and done, remove our status
    window.statuses.remove(status)


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
        window.reload_anime_eps.emit()  # type: ignore

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
        window.update_anilist_label.emit(  # type: ignore
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
        window.handle_anime_updates.emit()  # type: ignore
        window.statuses.remove(status)


def status_label(window: MainWindow):
    while True:
        window.update_label.emit()  # type: ignore
        sleep(0.1)


def edit_anime(window: MainWindow, anime: Union[Anime, AnimeCollection], **kwargs):
    status = StatusHelper("Updating anime lists")
    window.statuses.append(status)
    anime.edit(window.app._anilist, **kwargs)
    window.statuses.remove(status)


def search_nyaa(window: MainWindow, query: str):
    status = StatusHelper("Searching nyaa.si")
    window.statuses.append(status)
    results = list(window.app.search_nyaa(query))
    window.nyaa_results.emit(results)  # type: ignore
    window.statuses.remove(status)


def search_anilist(window: MainWindow, query: str):
    status = StatusHelper("Searching anilist")
    window.statuses.append(status)
    results = window.app._anilist.search_anime(query)

    for result in results:
        window.insert_row_signal.emit(window.ui.AnilistSearchResults, result)  # type: ignore
    window.statuses.remove(status)


def generate_thumbnails(
    window: MainWindow, episodes: List[AnimeFile], anime: AnimeCollection
):
    for ep in episodes:
        # The property handles caching thumbnails, just access to trigger it
        ep.thumbnail

    # Once we're done emit the update to add to scroll area
    window.add_episodes_to_widget.emit(episodes, anime)  # type: ignore


class StatusHelper:
    def __init__(self, status: str, color: Optional[str] = "rgb(36, 255, 36);") -> None:
        self.status = status
        self.color = color
