from __future__ import annotations

import functools
import os
import sys
from typing import Dict, List, Optional, Union

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker import __version__, logger
from anitracker.anitracker import AniTracker
from anitracker.background import *
from anitracker.media import Anime, AnimeCollection, UserStatus
from anitracker.signals import SignalConnector, MouseFilter
from anitracker.ui import Ui_AnimeApp, Ui_AnimeInfo


class MainWindow(QMainWindow):
    update_ui_signal = Signal(functools.partial)
    insert_row_signal = Signal(QTableWidget, Anime)
    update_row_signal = Signal(QTableWidget, int, Anime)
    reload_anime_eps = Signal()
    update_anilist_label = Signal(str)
    update_label = Signal()
    handle_anime_updates = Signal()
    nyaa_results = Signal(list)

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
            "progress": True,
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
        self._threads_to_terminate: List[BackgroundThread] = []
        # This will trigger the status label update
        self.status_update_worker = BackgroundThread(status_label, self)
        # Used for searching files in the background
        self.update_worker = BackgroundThread(refresh_folder, self)
        # This'll be the loop that automatically does so every 2 minutes
        self._update_anime_files_loop = BackgroundThread(
            refresh_folder, self, loop_forever=True
        )
        # Connecting to anilist
        self.anilist_connector = BackgroundThread(connect_to_anilist, self)
        # Anime updates
        self.anime_updater = BackgroundThread(update_from_anilist, self)
        # Will check for update in the background
        self.update_checker = BackgroundThread(try_update, self)

        # Add them all to the termintable threads
        self.status_update_worker.setTerminationEnabled(True)
        self.update_worker.setTerminationEnabled(True)
        self._update_anime_files_loop.setTerminationEnabled(True)
        self.anilist_connector.setTerminationEnabled(True)
        self.anime_updater.setTerminationEnabled(True)
        self.update_checker.setTerminationEnabled(True)
        self._threads_to_terminate.append(self.status_update_worker)
        self._threads_to_terminate.append(self.update_worker)
        self._threads_to_terminate.append(self._update_anime_files_loop)
        self._threads_to_terminate.append(self.anilist_connector)
        self._threads_to_terminate.append(self.anime_updater)
        self._threads_to_terminate.append(self.update_checker)

        # Start a few things in the background
        self._update_anime_files_loop.start()
        self.anilist_connector.start()
        self.status_update_worker.start()

    def setup_tables(self):
        def default_table_setup(_table: QTableWidget, _headers: Dict):
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

            for title, enabled in _headers.items():
                # Get the pretty title for the action menu
                pretty_title = title.lower().replace("_", " ").title()
                headers.append(pretty_title)
                # Create the action menu entry
                action = QAction(pretty_title, _table.horizontalHeader())
                # Set them as checkable
                action.setCheckable(True)
                # Add column to _table
                _table.insertColumn(_table.columnCount())
                index = _table.columnCount() - 1
                # If it's enabled, set action as true and don't hide row
                if enabled:
                    action.setChecked(True)
                    _table.setColumnHidden(index, False)
                else:
                    _table.setColumnHidden(index, True)

                menu.addAction(action)

                # Resize header
                size = self.app._config.get_option(
                    str(index), section=_table.objectName()
                )
                if size is not None:
                    _table.setColumnWidth(index, int(size))

            # Setting headers has to come after
            _table.setHorizontalHeaderLabels(headers)

        user_settings = [
            "user_status",
            "score",
            "progress",
            "repeat",
            "updated_at",
            "start_date",
            "end_date",
        ]
        _anilist_search_headers = {
            k: v
            for k, v in self.get_headers(self.ui.AnilistSearchResults).items()
            if k not in user_settings
        }

        default_table_setup(self.ui.AnilistSearchResults, _anilist_search_headers)
        # https://bugreports.qt.io/browse/QTBUG-12889
        # Asanine
        self.ui.AnilistSearchResults.horizontalHeader().setVisible(True)
        self.ui.NyaaSearchResults.horizontalHeader().setVisible(True)

        for table in self.tables:
            headers = self.get_headers(table)
            default_table_setup(table, headers)

        # Nyaa search setup is a little different
        nyaa = self.ui.NyaaSearchResults
        headers = self.get_headers(
            nyaa,
            _headers={
                "title": True,
                "size": True,
                "date": True,
                "seeders": True,
                "leechers": True,
                "downloads": True,
            },
        )
        default_table_setup(nyaa, headers)

    def connect_signals(self):
        self.insert_row_signal.connect(self.signals.insert_row)  # type: ignore
        self.update_row_signal.connect(self.signals.update_row)  # type: ignore
        self.filter_anime.textChanged.connect(self.signals.filter_row)  # type: ignore
        self.update_label.connect(self.signals.update_status)  # type: ignore
        self.reload_anime_eps.connect(self.signals.handle_anime_updates)  # type: ignore
        self.update_ui_signal.connect(self.signals.handle_ui_update)  # type: ignore
        self.handle_anime_updates.connect(self.signals.handle_anime_updates)  # type: ignore
        self.ui.AnilistSearchButton.clicked.connect(self.signals.search_anilist)  # type: ignore
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
        for thread in self._threads_to_terminate:
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

    def get_headers(
        self,
        table: QTableWidget,
        *,
        _headers: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, bool]:
        """Returns the headers specified for this table"""
        headers: Dict[str, bool] = {}

        if _headers is None:
            _headers = self._header_labels

        # Loop through defaults
        for header, default in _headers.items():
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


# Attach uncaught exceptions, so they can be logged
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


def main():
    app = QApplication(sys.argv)

    window = MainWindow(app)
    window.setFixedSize(window.size())
    window.show()

    ret = app.exec_()
    window.stop_threads()
    sys.exit(ret)


if __name__ == "__main__":
    main()
