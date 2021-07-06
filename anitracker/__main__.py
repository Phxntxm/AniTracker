from __future__ import annotations

import functools
import os
import sys
from typing import Dict, List, Optional, Union, cast

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker import __version__
from anitracker.anitracker import AniTracker
from anitracker.background import *
from anitracker.media import Anime, AnimeCollection, UserStatus
from anitracker.signals import SignalConnector, MouseFilter
from anitracker.ui import Ui_AnimeApp, Ui_AnimeInfo


class MainWindow(QMainWindow):
    update_ui_signal = Signal(functools.partial)
    insert_row_signal = Signal(QTableWidget, Anime)
    update_row_signal = Signal(QTableWidget, int, Anime)

    # Setup stuff
    def __init__(self, qapp: QApplication):
        super().__init__()
        self._qapp = qapp
        self.setup()
        self.setup_threads()
        self.setup_tables()
        self.connect_signals()

    def setup(self):
        self.ui = Ui_AnimeApp()
        # The central app
        self.app = AniTracker()
        # Where all the signals lay
        self.signals = SignalConnector(self)
        # A list of the status helpers
        self.statuses: List[StatusHelper] = []
        # A dict of the headers to whether they're enabled by default
        # TODO: Figure out how to make the header not go away when all columns are hidden
        self._header_labels = {
            "id": False,
            "user_status": False,
            "score": False,
            "repeat": False,
            "updated_at": False,
            "romaji_title": False,
            "english_title": False,
            "native_title": False,
            "preferred_title": True,
            "anime_status": False,
            "description": False,
            "start_date": False,
            "end_date": False,
            "anime_start_date": False,
            "anime_end_date": False,
            "episode_count": True,
            "average_score": True,
        }
        # Setup the app UI
        self.ui.setupUi(self)

        # Add the filter line edit to the right of the tool box
        self.filter_anime = QLineEdit()
        self.filter_anime.setPlaceholderText("Filter anime")
        self.filter_anime.setStyleSheet(
            """
            margin-left: 500px;
            """
        )
        self.ui.toolBar.addWidget(self.filter_anime)
        # Ensure the pages/page chooser is set to the first index
        self.ui.AnimePages.setCurrentIndex(0)
        self.ui.AnimeListChooser.setCurrentRow(0)

    def setup_threads(self):
        # Setup background stuff
        self.threadpool = QThreadPool()
        # This will trigger the status label update
        self.status_update_worker = StatusLabelUpdater(self)
        self.status_update_worker.setTerminationEnabled(True)
        # Used for searching files in the background
        self.update_worker = UpdateAnimeEpisodes(self)
        self.update_worker.setTerminationEnabled(True)
        # This'll be the loop that automatically does so every 2 minutes
        self._update_anime_files_loop = UpdateAnimeEpisodesLoop(self)
        self._update_anime_files_loop.setTerminationEnabled(True)
        # Connecting to anilist
        self.anilist_connector = ConnectToAnilist(self)
        self.anilist_connector.setTerminationEnabled(True)
        # Anime updates
        self.anime_updater = UpdateAnimeLists(self)
        self.anime_updater.setTerminationEnabled(True)
        # The success update label
        self.update_success = AnimeUpdateSuccess()
        self.update_success.setTerminationEnabled(True)
        # Will check for update in the background
        self.update_checker = UpdateChecker(self)
        self.update_checker.setTerminationEnabled(True)

        # Start a few things in the background
        self.anilist_connector.start()
        self.status_update_worker.start()

    def setup_tables(self):
        def default_table_setup(_table: QTableWidget, skip_user_settings: bool = False):
            # Create a menu per table
            menu = _table.menu = QMenu(self.ui.AnimeListTab)  # type: ignore
            menu.setStyleSheet("QMenu::item:selected {background-color: #007fd4}")
            menu.triggered.connect(functools.partial(self.signals.header_changed, _table))  # type: ignore
            # Set the custom context menu on the *header*, this is how
            # we switch which columns are visible
            _table.horizontalHeader().setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            # Connect it to the modifying of the _table
            _table.horizontalHeader().customContextMenuRequested.connect(  # type: ignore
                functools.partial(self.signals.open_header_menu, _table)
            )
            _table.horizontalHeader().setMinimumSectionSize(50)
            # Now set the custom context menu on the _table itself
            _table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            _table.customContextMenuRequested.connect(functools.partial(self.signals.open_anime_context_menu, _table))  # type: ignore
            _table.viewport().installEventFilter(MouseFilter(_table, self))
            _table.itemClicked.connect(self.signals.change_banner)  # type: ignore
            _table.horizontalHeader().sectionResized.connect(  # type: ignore
                functools.partial(self.signals.resized_column, _table)
            )

            headers = []

            if not skip_user_settings:
                headers.append("Progress")

            for title, enabled in self.get_headers(_table).items():
                # Skip if this is a user setting
                if skip_user_settings and title in [
                    "user_status",
                    "score",
                    "progress",
                    "repeat",
                    "updated_at",
                    "start_date",
                    "end_date",
                ]:
                    continue
                # Get the pretty title for the action menu
                pretty_title = title.lower().replace("_", " ").title()
                headers.append(pretty_title)
                # Create the action menu entry
                action = QAction(pretty_title, _table.horizontalHeader())
                # Set them as checkable
                action.setCheckable(True)
                # Add column to _table
                _table.insertColumn(_table.columnCount())
                # If it's enabled, set action as true and don't hide row
                if enabled:
                    action.setChecked(True)
                    _table.setColumnHidden(_table.columnCount() - 1, False)
                else:
                    _table.setColumnHidden(_table.columnCount() - 1, True)

                menu.addAction(action)

            # This has to be done after due to the difference in the 0th column
            # in some of the tables
            for index in range(_table.columnCount()):
                size = self.app._config.get_option(
                    str(index), section=_table.objectName()
                )
                if size is not None:
                    _table.setColumnWidth(index, int(size))

            # Setting headers has to come after
            _table.setHorizontalHeaderLabels(headers)

        default_table_setup(self.ui.AnilistSearchResults, skip_user_settings=True)
        # https://bugreports.qt.io/browse/QTBUG-12889
        # Asanine
        self.ui.AnilistSearchResults.horizontalHeader().setVisible(True)
        self.ui.NyaaSearchResults.horizontalHeader().setVisible(True)

        for table in self.tables:
            # Insert the column for progress first
            table.insertColumn(0)
            table.setColumnWidth(0, 200)

            default_table_setup(table)

        # Nyaa search setup is a little different
        headers = ["title", "size", "date", "seeders", "leechers", "downloads"]
        nyaa = self.ui.NyaaSearchResults
        for _ in headers:
            nyaa.insertColumn(nyaa.columnCount())

        nyaa.setHorizontalHeaderLabels(headers)
        nyaa.viewport().installEventFilter(MouseFilter(nyaa, self))

    def connect_signals(self):
        self.insert_row_signal.connect(self.signals.insert_row)  # type: ignore
        self.update_row_signal.connect(self.signals.update_row)  # type: ignore
        self.filter_anime.textChanged.connect(self.signals.filter_row)  # type: ignore
        self.status_update_worker.update.connect(self.signals.update_status)  # type: ignore
        self.update_worker.reload_anime_eps.connect(self.signals.reload_anime_eps)  # type: ignore
        self._update_anime_files_loop.reload_anime_eps.connect(self.signals.reload_anime_eps)  # type: ignore
        self.update_ui_signal.connect(self.signals.handle_ui_update)  # type: ignore
        self.anime_updater.handle_anime_updates.connect(self.signals.handle_anime_updates)  # type: ignore
        self.update_success.toggle.connect(self.signals.toggle_success)  # type: ignore
        self.ui.AnilistSearchButton.clicked.connect(self.signals.search_anime)  # type: ignore
        self.ui.NyaaSearchButton.clicked.connect(self.signals.search_nyaa)  # type: ignore
        self.ui.AnimeListChooser.currentRowChanged.connect(self.signals.change_page)  # type: ignore
        self.ui.actionSettings.triggered.connect(self.signals.open_settings)  # type: ignore
        self.ui.actionRefresh.triggered.connect(self.anime_updater.start)  # type: ignore
        self.ui.actionReload_Videos.triggered.connect(self.update_worker.start)  # type: ignore
        self.ui.actionAbout.triggered.connect(self.signals.open_about)  # type: ignore
        self.ui.actionReport_bug.triggered.connect(self.signals.open_issue_tracker)  # type: ignore
        self.ui.actionSource_code.triggered.connect(self.signals.open_repo)  # type: ignore
        self.ui.actionUpdateCheck.triggered.connect(self.update_checker.start)  # type: ignore

    def stop_threads(self):
        for thread in [
            self.status_update_worker,
            self.update_worker,
            self._update_anime_files_loop,
            self.anilist_connector,
            self.anime_updater,
            self.update_checker,
            self.update_success,
        ]:
            if thread.isRunning():
                thread.terminate()
                thread.wait()

    # Misc methods
    @property
    def pretty_headers(self) -> List[str]:
        return [x.replace("_", " ").title() for x in self._header_labels.keys()]

    @property
    def tables(self) -> List[QTableWidget]:
        return [
            self.ui.CompletedTable,
            self.ui.WatchingTable,
            self.ui.PlanningTable,
            self.ui.DroppedTable,
            self.ui.PausedTable,
        ]

    def get_table(self, status: UserStatus) -> QTableWidget:
        if status is UserStatus.COMPLETED:
            return self.ui.CompletedTable
        elif status in (UserStatus.CURRENT, UserStatus.REPEATING):
            return self.ui.WatchingTable
        elif status is UserStatus.PLANNING:
            return self.ui.PlanningTable
        elif status is UserStatus.DROPPED:
            return self.ui.DroppedTable
        elif status is UserStatus.PAUSED:
            return self.ui.PausedTable

        raise TypeError(f"Cannot find table for {status}")

    def get_headers(self, table: QTableWidget) -> Dict[str, bool]:
        """Returns the headers specified for this table"""
        headers: Dict[str, bool] = {}

        # Loop through defaults
        for header, default in self._header_labels.items():
            # Get override from config
            opt = self.app._config.get_option(header, section=table.objectName())
            if opt is None:
                opt = default

            headers[header] = opt

        return headers

    def open_anime_settings(self, anime: Union[Anime, AnimeCollection]):
        # Anime settings stuff
        m = self.anime_menu = QTabWidget()
        s = self.anime_window = Ui_AnimeInfo()
        self.anime_window.setupUi(self.anime_menu)
        # Bro why is this modifable in the designer? Stupid
        s.AnimeUpdateSuccess.setVisible(False)

        # Pull up anime info
        s.AnimeTitleLabel.setText("\n".join(t for t in anime.titles if t))
        s.AnimeDescriptionLabel.setText(anime.description)
        s.AnimeGenresLabel.setText("\n".join(anime.genres))
        tags = sorted(anime.tags, key=lambda t: t[1], reverse=True)
        tagfmt = "\n".join(f"{tag[0]} {tag[1]}%" for tag in tags)
        s.AnimeTagsLabel.setText(tagfmt)
        s.AnimeStudioLabel.setText(anime.studio)
        s.AnimeSeasonLabel.setText(anime.season)
        s.AnimeAverageScoreLabel.setText(f"{anime.average_score}%")
        s.AnimeEpisodesLabel.setText(str(anime.episode_count))
        if isinstance(anime, AnimeCollection):
            s.AnimeNotes.setText(anime.notes)
            s.AnimeUserScore.setValue(anime.score)
            s.AnimeUpdateButton.clicked.connect(  # type: ignore
                functools.partial(self.signals.update_anime_from_settings, anime)
            )
        else:
            s.AnimeNotesLabel.setVisible(False)
            s.AnimeUserScoreLabel.setVisible(False)
            s.AnimeUserScore.setVisible(False)
            s.AnimeNotes.setVisible(False)
            s.AnimeUpdateButton.setVisible(False)
        m.setFixedSize(m.size())

        m.show()


def main():
    app = QApplication(sys.argv)

    window = MainWindow(app)
    window.setFixedSize(window.size())
    window.show()

    # First replace the file situation if it's there's been some partial/finished download
    if sys.platform.startswith("win32") and getattr(sys, "frozen", False):
        d = os.path.dirname(sys.executable)

        try:
            # We have a backup file
            os.stat(f"{d}\\anitracker.exe.bak")
            try:
                os.stat(f"{d}\\anitracker.exe")
            # Just a backup, download succeeded
            except FileNotFoundError:
                os.rename(f"{d}\\anitracker.exe.bak", f"{d}\\anitracker.exe")
            # We have a main and backup... download failed, remove partial download
            else:
                if not sys.executable.endswith(".bak"):
                    os.remove(f"{d}\\anitracker.exe.bak")
        # No backup file, no download happened, we don't care
        except FileNotFoundError:
            pass
    ret = app.exec_()
    window.stop_threads()
    sys.exit(ret)


if __name__ == "__main__":
    main()
