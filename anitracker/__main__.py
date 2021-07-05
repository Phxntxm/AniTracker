from __future__ import annotations

import functools
import os
import pycountry
import subprocess
import sys
import webbrowser
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Union, cast

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker import __version__
from anitracker.anitracker import AniTracker
from anitracker.background import *
from anitracker.media import AnimeCollection, Anime, UserStatus
from anitracker.ui import Ui_About, Ui_AnimeApp, Ui_AnimeInfo, Ui_Settings


class MouseFilter(QObject):
    def __init__(self, table: QTableWidget, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)

        self._table = table
        self._playing_episode: Union[PlayEpisode, None] = None

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        parent = cast(MainWindow, self.parent())

        if not isinstance(event, QMouseEvent):
            return False

        # If we've pressed and released
        if event.type() is QEvent.MouseButtonDblClick:
            # Get the item at that position
            point = event.pos()
            item = cast(AnimeWidgetItem, self._table.itemAt(point))
            parent.open_anime_settings(item.anime)

        if event.type() is QEvent.MouseButtonRelease:
            # Get the item at that position
            item = cast(AnimeWidgetItem, self._table.itemAt(event.pos()))

            # If we found one, then do the things
            if item is not None:
                # Middle click plays the episode
                if event.button() is Qt.MiddleButton:
                    self._playing_episode = PlayEpisode(
                        item.anime, item.anime.progress + 1, parent
                    )
                    self._playing_episode.start()
        return super().eventFilter(watched, event)


class HiddenProgressBarItem(QTableWidgetItem):
    def __init__(self, anime: Union[AnimeCollection, Anime]) -> None:
        super().__init__("")
        self.anime = anime

    @property
    def amount(self):
        return (
            self.anime.progress / self.anime.episode_count
            if self.anime.episode_count
            else 0
        )

    def __lt__(self, other):
        return self.amount < other.amount


class AnimeWidgetItem(QTableWidgetItem):
    def __init__(self, anime: Union[AnimeCollection, Anime]):
        super().__init__()

        self.anime = anime


class MainWindow(QMainWindow):
    # Setup stuff
    def __init__(self, qapp: QApplication):
        super().__init__()
        self._qapp = qapp
        self.setup()
        self.connect_signals()

    def setup(self):
        self.ui = Ui_AnimeApp()
        # The central app
        self.app = AniTracker()
        # A list of the status helpers
        self.statuses: List[StatusHelper] = []
        # Settings menu stuff
        self.settings_widget = QTabWidget()
        self.settings_window = Ui_Settings()
        self.settings_window.setupUi(self.settings_widget)
        # Anime settings stuff
        self.anime_menu = QTabWidget()
        self.anime_window = Ui_AnimeInfo()
        self.anime_window.setupUi(self.anime_menu)
        # Bro why is this modifable in the designer? Stupid
        self.anime_window.AnimeUpdateSuccess.setVisible(False)
        # A dict of the headers to whether they're enabled by default
        # TODO: pull enabled/disabled from config
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
        # Setup our custom UI stuff
        self.custom_ui()

        # Add the filter line edit to the right of the tool box
        self.filter_anime = QLineEdit()
        self.filter_anime.setPlaceholderText("Filter anime")
        self.filter_anime.setStyleSheet(
            """
            margin-left: 500px;
            """
        )
        self.ui.toolBar.addWidget(self.filter_anime)
        self.ui.AnimePages.setCurrentIndex(0)
        self.ui.AnimeListChooser.setCurrentRow(0)

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
        self._update_anime_files_loop.start()
        self.status_update_worker.start()

        # Setup the settings stuff

        self.settings_window.SubtitleLanguage.addItems(
            sorted([l.name for l in pycountry.languages])
        )

        # Setup initial settings info
        try:
            self.settings_window.AnimeFolderLineEdit.setText(
                self.app._config["animedir"]
            )
        except KeyError:
            pass
        try:
            self.settings_window.SubtitleLanguage.setCurrentText(
                pycountry.languages.get(alpha_3=self.app._config["subtitle"]).name
            )
        except KeyError:
            pass
        try:
            b = self.app._config["skip_songs_signs"]
            state = Qt.CheckState.Checked if b else Qt.CheckState.Unchecked
            self.settings_window.IgnoreSongsSignsCheckbox.setCheckState(state)
        except KeyError:
            pass

    def custom_ui(self):
        def default_table_setup(_table: QTableWidget, skip_user_settings: bool = False):
            # Create a menu per table
            menu = _table.menu = QMenu(self.ui.AnimeListTab)  # type: ignore
            menu.setStyleSheet("QMenu::item:selected {background-color: #007fd4}")
            menu.triggered.connect(self.header_changed)  # type: ignore
            # Set the custom context menu on the *header*, this is how
            # we switch which columns are visible
            _table.horizontalHeader().setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            # Connect it to the modifying of the _table
            _table.horizontalHeader().customContextMenuRequested.connect(  # type: ignore
                functools.partial(self.open_header_menu, _table)
            )
            _table.horizontalHeader().setMinimumSectionSize(50)
            # Now set the custom context menu on the _table itself
            _table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            _table.customContextMenuRequested.connect(functools.partial(self.open_anime_context_menu, _table))  # type: ignore
            _table.viewport().installEventFilter(MouseFilter(_table, self))
            _table.itemClicked.connect(self.change_banner)  # type: ignore

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

            # Setting headers has to come after
            _table.setHorizontalHeaderLabels(headers)

        default_table_setup(self.ui.AnilistSearchResults, skip_user_settings=True)
        # https://bugreports.qt.io/browse/QTBUG-12889
        # Asanine
        self.ui.AnilistSearchResults.horizontalHeader().setVisible(True)

        for table in self.tables:
            # Insert the column for progress first
            table.insertColumn(0)
            table.setColumnWidth(0, 200)

            default_table_setup(table)

    def connect_signals(self):
        self.filter_anime.textChanged.connect(self.filter_row)  # type: ignore
        self.status_update_worker.update.connect(self.update_status)  # type: ignore
        self.update_worker.reload_anime_eps.connect(self.reload_anime_eps)  # type: ignore
        self._update_anime_files_loop.reload_anime_eps.connect(self.reload_anime_eps)  # type: ignore
        self.anilist_connector.update_label.connect(  # type: ignore
            self.settings_window.AnilistConnectedAccountLabel.setText
        )
        self.anime_updater.handle_anime_updates.connect(self.handle_anime_updates)  # type: ignore
        self.update_success.toggle.connect(self.toggle_success)  # type: ignore
        self.settings_window.AnilistConnect.clicked.connect(  # type: ignore
            self.app._anilist.open_oauth
        )
        self.settings_window.AnilistCodeConfirm.clicked.connect(  # type: ignore
            self.anilist_code_confirm
        )
        self.settings_window.AnimeFolderBrowse.clicked.connect(self.select_anime_path)  # type: ignore
        self.settings_window.IgnoreSongsSignsCheckbox.stateChanged.connect(  # type: ignore
            self.update_songs_signs
        )
        self.settings_window.SubtitleLanguage.currentIndexChanged.connect(  # type: ignore
            self.change_language
        )

        self.ui.AnilistSearchButton.clicked.connect(self.search_anime)  # type: ignore
        self.ui.AnimeListChooser.currentRowChanged.connect(self.change_page)  # type: ignore
        # Menu actions
        self.ui.actionSettings.triggered.connect(self.open_settings)  # type: ignore
        self.ui.actionRefresh.triggered.connect(self.anime_updater.start)  # type: ignore
        self.ui.actionReload_Videos.triggered.connect(self.update_worker.start)  # type: ignore
        self.ui.actionAbout.triggered.connect(self.open_about)  # type: ignore
        self.ui.actionReport_bug.triggered.connect(self.open_issue_tracker)  # type: ignore
        self.ui.actionSource_code.triggered.connect(self.open_repo)  # type: ignore
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
    def current_table(self) -> QTableWidget:
        return cast(
            QTableWidget, self.ui.AnimeListTab.currentWidget().findChild(QTableWidget)
        )

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

    def update_anilist_acc_label(self):
        # Only do this if we verified
        if self.app._anilist.authenticated:
            self.settings_window.AnilistConnectedAccountLabel.setText(
                f"Connected account: {self.app._anilist.name}"
            )

    def insert_row(self, table: QTableWidget, anime: Union[AnimeCollection, Anime]):
        row_pos = table.rowCount()
        table.insertRow(row_pos)

        if isinstance(anime, AnimeCollection):

            # Add the progress bar at position 0
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(anime.episode_count)
            bar.setMaximumHeight(15)
            bar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid grey;
                    border-radius: 5px;
                    background-color: rgb(68, 68, 68);
                    vertical-align: middle;
                }
                QProgressBar:horizontal {
                    text-align: right;
                    margin-right: 8ex;
                    padding: 1px;
                }
                QProgressBar::chunk {
                    background-color: #05B8CC;
                    width: 1px;
                }
                """
            )
            cell_widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(bar)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            cell_widget.setLayout(layout)

            bar.setValue(anime.progress)
            bar.setFormat("%v/%m")
            # Don't show progress bar if there are no episodes
            if anime.episode_count == 0:
                bar.setVisible(False)

            if missing := self.app.missing_eps(anime):
                tt = f"Missing episodes: {missing}"
            else:
                tt = "Found all episodes"

            bar.setToolTip(tt)
            table.setCellWidget(row_pos, 0, cell_widget)
            # Add an item along with the progressbar to enable sorting
            item = HiddenProgressBarItem(anime)
            table.setItem(row_pos, 0, item)

        for index in range(table.columnCount()):
            header = table.horizontalHeaderItem(index).text().lower().replace(" ", "_")

            piece = getattr(anime, header, "")
            if isinstance(piece, Enum):
                piece = piece.name.title()
            else:
                piece = str(piece)

            # Create our custom anime widget item
            item = AnimeWidgetItem(anime)
            item.setData(Qt.DisplayRole, piece)
            item.setToolTip(piece)
            table.setItem(row_pos, index, item)

        # Make sure things are sorted properly
        if table.isSortingEnabled():
            # This will immediately trigger a sort based on the sort option
            # selected, so we just set it to True again, since as far as I can
            # tell there's no way to GET the current sort option
            table.setSortingEnabled(True)

    def update_row(self, table: QTableWidget, row: int, anime: AnimeCollection):
        # Set the progress bar's data
        bar = cast(QProgressBar, table.cellWidget(row, 0).findChild(QProgressBar))
        bar.setMaximum(anime.episode_count)
        bar.setValue(anime.progress)
        if anime.episode_count:
            table.item(row, 0).setData(
                Qt.UserRole, anime.progress / anime.episode_count
            )

        if missing := self.app.missing_eps(anime):
            tt = f"Missing episodes: {missing}"
        else:
            tt = "Found all episodes"

        bar.setToolTip(tt)

        # Now loop through the normal headers
        for index, attr in enumerate(self._header_labels, start=1):
            piece = getattr(anime, attr, "")
            if isinstance(piece, Enum):
                piece = piece.name.title()
            elif isinstance(piece, date):
                piece = str(piece)

            table.item(row, index).setData(Qt.DisplayRole, piece)
            table.item(row, index).setToolTip(tt)

    def open_anime_settings(self, anime: Union[Anime, AnimeCollection]):
        # Pull up anime info
        s = self.anime_window
        m = self.anime_menu
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
                functools.partial(self.update_anime_from_settings, anime)
            )
        else:
            s.AnimeNotesLabel.setVisible(False)
            s.AnimeUserScoreLabel.setVisible(False)
            s.AnimeUserScore.setVisible(False)
            s.AnimeNotes.setVisible(False)
            s.AnimeUpdateButton.setVisible(False)
        m.setFixedSize(m.size())
        m.show()

    ### Signals

    # Settings action was clicked
    def open_settings(self):
        self.settings_widget.setFixedSize(self.settings_widget.size())
        self.settings_widget.show()

    # Confirm anilist code
    def anilist_code_confirm(self):
        token = self.settings_window.AnilistCodeBox.toPlainText()
        self.app._anilist.store_access(token)

        # Store in settings
        self.app._config["access-token"] = token
        self.app._anilist.verify()

        self.update_anilist_acc_label()

    # Header context menu option selected
    # TODO: Fix!
    def header_changed(self, _action: QAction):
        # Get the index of this header, it will match up with the table
        index = self.pretty_headers.index(_action.text())
        # Set the column hidden based on the action's checked status
        self.current_table.setColumnHidden(index + 1, not _action.isChecked())

        # Now save in config
        self.app._config.set_option(
            list(self._header_labels.keys())[index],
            _action.isChecked(),
            section=self.current_table.objectName(),
        )

    # Header was right clicked
    def open_header_menu(self, table: QTableWidget, point: QPoint):
        table.menu.exec_(self.ui.AnimeListTab.mapToGlobal(point))  # type: ignore

    # Anime in table was right clicked
    def open_anime_context_menu(self, table: QTableWidget, _: QPoint):
        # Get attrs that will be used a bit
        anime: Union[AnimeCollection, Anime] = table.selectedItems()[0].anime  # type: ignore

        # Setup the menu settings
        menu = QMenu(table)
        menu.setStyleSheet(
            "QMenu::item:selected {background-color: #007fd4}"
            "QWidget:disabled {color: #000000}"
            "QMenu {border: 1px solid black}"
        )
        menu.setToolTipsVisible(True)

        # Add misc actions
        settings = menu.addAction("Anime info")

        menu.addSeparator()

        # Add status changing options
        plan = menu.addAction("Planning")
        complete = menu.addAction("Completed")
        watch = menu.addAction("Watching")
        drop = menu.addAction("Dropped")

        if isinstance(anime, AnimeCollection):
            remove = menu.addAction("Remove from list")

        menu.addSeparator()

        if isinstance(anime, AnimeCollection):
            # Add episode options
            open_folder = menu.addAction("Open anime folder")
            open_folder.setToolTip(
                "This will open the folder that the first episode is detected in\n"
                "If episodes are in different folders then this may seem strange.\n"
                "If no episodes are found for this, it will open the anime folder.\n"
            )
            play_next = menu.addAction("Play next episode")
            play_menu = menu.addMenu("Play episode...")
            play_opts = {}
            next_ep = anime.progress + 1

            # Followup setting changes
            if not self.app.get_episode(anime, next_ep):
                play_next.setEnabled(False)

            if eps := self.app.get_episodes(anime):
                folder = os.path.dirname(
                    sorted(eps, key=lambda k: k.episode_number)[0].file
                )
            elif self.app._config["animedir"] is not None:
                folder = self.app._config["animedir"]
            else:
                folder = None
                open_folder.setEnabled(False)

            for ep in sorted(
                self.app.get_episodes(anime), key=lambda k: k.episode_number
            ):
                act = play_menu.addAction(f"Episode {ep.episode_number}")
                play_opts[act] = ep.episode_number

            if not play_opts:
                play_menu.setEnabled(False)

        action = menu.exec_(QCursor.pos())

        if action == settings:
            self.open_anime_settings(anime)
        elif action == plan:
            anime.edit(self.app._anilist, status=UserStatus.PLANNING)
        elif action == complete:
            anime.edit(self.app._anilist, status=UserStatus.COMPLETED)
        elif action == watch:
            if (
                isinstance(anime, AnimeCollection)
                and anime.user_status == UserStatus.COMPLETED
            ):
                anime.edit(self.app._anilist, status=UserStatus.REPEATING)
            else:
                anime.edit(self.app._anilist, status=UserStatus.CURRENT)
        elif action == drop:
            anime.edit(self.app._anilist, status=UserStatus.DROPPED)

        # Anime Collection specific items
        if isinstance(anime, AnimeCollection):
            if action == remove:
                anime.delete(self.app._anilist)
                del self.app._animes[anime.id]
            elif action == open_folder and folder is not None:
                if sys.platform.startswith("win32"):
                    subprocess.Popen(["start", folder], shell=True)
                elif sys.platform.startswith("linux"):
                    subprocess.Popen(
                        ["xdg-open", folder],
                    )
            elif action == play_next:
                self._playing_episode = PlayEpisode(anime, next_ep, self)
                self._playing_episode.start()
            elif action in play_opts:
                self._playing_episode = PlayEpisode(anime, play_opts[action], self)
                self._playing_episode.start()

        # If we've edited an Anime class directly, that means we modifed our list from
        # a non list-item... IE added it to it. So we need to refresh from anilist
        if not isinstance(anime, AnimeCollection):
            self.anime_updater.start()

        self.handle_anime_updates(list(self.app.animes.values()))

    # Browse for anime folder was clicked
    def select_anime_path(self):
        dir = QFileDialog.getExistingDirectory(
            None, "Choose Anime Path", "", QFileDialog.ShowDirsOnly
        )

        self.settings_window.AnimeFolderLineEdit.setText(dir)
        self.app._config["animedir"] = dir

    # Checkbox for songs/signs was changed
    def update_songs_signs(self):
        self.app._config["skip_songs_signs"] = (
            self.settings_window.IgnoreSongsSignsCheckbox.checkState()
            is Qt.CheckState.Checked
        )

    # Clear tables signal was emitted
    def clear_tables(self):
        for table in self.tables:
            table.setRowCount(0)

    # Update all animes from anilist
    def handle_anime_updates(self, animes: List[AnimeCollection]):
        # First, handle any animes in the tables but not in the list of animes
        for table in self.tables:
            # Reverse through the range, so that removal of rows
            # doesn't mess up what we're looking at
            for row in range(table.rowCount() - 1, -1, -1):
                anime: AnimeCollection = table.item(row, 0).anime  # type: ignore

                # If the anime is not in the list, remove it from the table
                if anime not in animes:
                    table.removeRow(row)
                # Otherwise if this table doesn't match the anime's status, remove it
                elif self.get_table(anime.user_status) != table:
                    table.removeRow(row)

        # Now loop through the animes and handle all the updates
        for anime in animes:
            found = False
            table = self.get_table(anime.user_status)

            # Loop through every row in the table it should be in
            for row in range(table.rowCount()):
                # Found it
                if cast(AnimeWidgetItem, table.item(row, 0)).anime == anime:
                    found = True
                    self.update_row(table, row, anime)

            # If we didn't find it, then insert it
            if not found:
                self.insert_row(table, anime)

        # Make sure things are sorted properly
        for table in self.tables:
            if table.isSortingEnabled():
                # This will immediately trigger a sort based on the sort option
                # selected, so we just set it to True again, since as far as I can
                # tell there's no way to GET the current sort option
                table.setSortingEnabled(True)

    # Toggle visible success label
    def toggle_success(self):
        self.anime_window.AnimeUpdateSuccess.setVisible(
            not self.anime_window.AnimeUpdateSuccess.isVisible()
        )

    # Files were refreshed, update anime tooltip info
    def reload_anime_eps(self):
        self.handle_anime_updates(list(self.app.animes.values()))

    # Anime settings submit button was clicked
    def update_anime_from_settings(self, anime: AnimeCollection):
        notes = self.anime_window.AnimeNotes.toPlainText()
        score = self.anime_window.AnimeUserScore.value()

        anime.edit(self.app._anilist, score=score, notes=notes)

    # About was clicked
    def open_about(self):
        widget = self.about_widget = QWidget()
        about = Ui_About()
        about.setupUi(widget)
        about.VersionLabel.setText(f"Version: {__version__}")
        about.label.linkActivated.connect(webbrowser.open)  # type: ignore
        widget.setFixedSize(widget.size())
        widget.show()

    # Report bug was clicked
    def open_issue_tracker(self):
        webbrowser.open("https://github.com/Phxntxm/AniTracker/issues")

    # Source code was clicked
    def open_repo(self):
        webbrowser.open("https://github.com/Phxntxm/AniTracker")

    # Filter anime was typed in
    def filter_row(self, text: str):
        for table in self.tables:
            for row in range(table.rowCount()):
                anime = cast(AnimeWidgetItem, table.item(row, 0)).anime
                if (
                    text.lower() in anime.english_title.lower()
                    or text.lower() in anime.romaji_title.lower()
                    or text.lower() in anime.native_title.lower()
                ):
                    table.setRowHidden(row, False)
                else:
                    table.setRowHidden(row, True)

    # Status update needs to be triggered
    def update_status(self):
        try:
            status = self.statuses[0]
        except IndexError:
            self.ui.StatusLabel.setText("")
        else:
            self.ui.StatusLabel.setText(status.status)
            self.ui.StatusLabel.setStyleSheet(f"color: {status.color}")

    # Language option was changed
    def change_language(self, index):
        lang = self.settings_window.SubtitleLanguage.itemText(index)
        alpha_3 = pycountry.languages.get(name=lang).alpha_3

        self.app._config["subtitle"] = alpha_3

    # Page was updated
    def change_page(self, row: int):
        self.ui.AnimePages.setCurrentIndex(row)

    # Change banner
    def change_banner(self, item: AnimeWidgetItem):
        self.ui.BannerViewer.setUrl(item.anime.cover_image)

    # Search anilist
    def search_anime(self):
        results = self.app._anilist.search_anime(self.ui.AnilistSearchLineEdit.text())

        for result in results:
            self.insert_row(self.ui.AnilistSearchResults, result)


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
