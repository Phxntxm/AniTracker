from __future__ import annotations

import functools
import math
import os
import subprocess
import sys
import webbrowser
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Union

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from anitracker.anitracker import AniTracker
from anitracker.background import *
from anitracker.media import AnimeCollection, AnimeFile, UserStatus, anime
from anitracker.ui import Ui_AnimeApp, Ui_AnimeInfo, Ui_Settings, Ui_About


class MouseFilter(QObject):
    def __init__(self, table: QTableWidget, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)

        self._table = table
        self._playing_episode: Union[AnimeFile, None] = None

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # If we've pressed and released
        if event.type() is QEvent.MouseButtonDblClick:
            # Get the item at that position
            point = event.position().toPoint()
            self.parent().open_anime_settings(self._table.itemAt(point).anime)

        if event.type() is QEvent.MouseButtonRelease:
            # Get the item at that position
            item = self._table.itemAt(event.position().toPoint())

            # If we found one, then do the things
            if item is not None:
                # Middle click plays the episode
                if event.button() is Qt.MiddleButton:
                    self._playing_episode = PlayEpisode(
                        item.anime.episodes[item.anime.progress + 1], self.parent()
                    )
                    self._playing_episode.start()
        return super().eventFilter(watched, event)


class MainWindow(QMainWindow):
    # Setup stuff
    def __init__(self, qapp: QApplication):
        super().__init__()
        self._qapp = qapp
        self.setup()

    def setup(self):
        self.ui = Ui_AnimeApp()
        # The central app
        self.app = AniTracker()
        # Settings menu stuff
        self.settings_menu = QTabWidget()
        self.settings_window = Ui_Settings()
        self.settings_window.setupUi(self.settings_menu)
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
            "progress": False,
            "repeat": False,
            "updated_at": False,
            "romaji_title": False,
            "english_title": True,
            "native_title": False,
            "preferred_title": False,
            "anime_status": False,
            "description": False,
            "start_date": False,
            "end_date": False,
            "episode_count": True,
            "average_score": True,
        }
        # Setup the app UI
        self.ui.setupUi(self)
        # Setup our custom UI stuff
        self.custom_ui()

        # Setup background stuff
        self.threadpool = QThreadPool()
        # Used for searching files in the background
        self.update_worker = UpdateAnimeEpisodes(self.app)
        self.update_worker.reload_anime_eps.connect(self.reload_anime_eps)
        # This'll be the loop that automatically does so every 2 minutes
        self._update_anime_files_loop = UpdateAnimeEpisodesLoop(self.app)
        self._update_anime_files_loop.reload_anime_eps.connect(self.reload_anime_eps)
        # Connecting to anilist
        self.anilist_connector = ConnectToAnilist(self)
        self.anilist_connector.update_label.connect(
            self.settings_window.AnilistConnectedAccountLabel.setText
        )
        # Anime updates
        self.anime_updater = UpdateAnimeLists(self)
        self.anime_updater.handle_anime_updates.connect(self.handle_anime_updates)
        # The success update label
        self.update_success = AnimeUpdateSuccess(self.anime_window)
        self.update_success.toggle.connect(self.toggle_success)

        # Connect quitting calls
        self._qapp.aboutToQuit.connect(self.update_worker.quit)
        self._qapp.aboutToQuit.connect(self._update_anime_files_loop.quit)
        self._qapp.aboutToQuit.connect(self.anilist_connector.quit)
        self._qapp.aboutToQuit.connect(self.anime_updater.quit)
        self._qapp.aboutToQuit.connect(self.update_success.quit)

        # Start a few things in the background
        self.anilist_connector.start()
        self._update_anime_files_loop.start()

        # Setup the settings stuff
        self.settings_window.AnilistConnect.clicked.connect(
            self.app._anilist.open_oauth
        )
        self.settings_window.AnilistCodeConfirm.clicked.connect(
            self.anilist_code_confirm
        )
        self.settings_window.AnimeFolderBrowse.clicked.connect(self.select_anime_path)
        self.settings_window.SubtitleLanguageLineEdit.textChanged.connect(
            self.update_subtitles
        )
        self.settings_window.IgnoreSongsSignsCheckbox.stateChanged.connect(
            self.update_songs_signs
        )
        self.ui.actionSettings.triggered.connect(self.open_settings)
        self.ui.actionRefresh.triggered.connect(self.anime_updater.start)
        self.ui.actionReload_Videos.triggered.connect(self.update_worker.start)
        self.ui.actionAbout.triggered.connect(self.open_about)
        self.ui.actionReport_bug.triggered.connect(self.open_issue_tracker)
        self.ui.actionSource_code.triggered.connect(self.open_repo)
        # Setup initial settings info
        try:
            self.settings_window.AnimeFolderLineEdit.setText(
                self.app._config["animedir"]
            )
        except KeyError:
            pass
        try:
            self.settings_window.SubtitleLanguageLineEdit.setText(
                self.app._config["subtitle"]
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
        pretty_headers = self.pretty_headers

        for table in self.tables:
            # Createa menu per table
            menu = table.menu = QMenu(self.ui.AnimeListTab)
            menu.setStyleSheet("QMenu::item:selected {background-color: #007fd4}")
            menu.triggered.connect(self.header_changed)
            # Set the custom context menu on the *header*, this is how
            # we switch which columns are visible
            table.horizontalHeader().setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            # Connect it to the modifying of the table
            table.horizontalHeader().customContextMenuRequested.connect(
                self.open_header_menu
            )
            # Now set the custom context menu on the table itself
            table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            table.customContextMenuRequested.connect(self.open_anime_context_menu)
            table.viewport().installEventFilter(MouseFilter(table, self))

            # Insert the column for progress first
            table.insertColumn(0)

            for index, enabled in enumerate(self.get_headers(table).values(), start=1):
                # Get the pretty title for the action menu
                pretty_title = pretty_headers[index - 1]
                # Create the action menu entry
                action = QAction(pretty_title, table.horizontalHeader())
                # Set them as checkable
                action.setCheckable(True)
                # Add column to table
                table.insertColumn(index)
                # If it's enabled, set action as true and don't hide row
                if enabled:
                    action.setChecked(True)
                    table.setColumnHidden(index, False)
                else:
                    table.setColumnHidden(index, True)

                menu.addAction(action)

            # Setting headers has to come after
            table.setHorizontalHeaderLabels(["Progress"] + pretty_headers)

    # Misc methods
    @property
    def pretty_headers(self) -> List[str]:
        return [x.replace("_", " ").title() for x in self._header_labels.keys()]

    @property
    def current_table(self) -> QTableWidget:
        return self.ui.AnimeListTab.currentWidget().findChild(QTableWidget)

    @property
    def tables(self) -> List[QTableWidget]:
        return [
            self.ui.CompletedTable,
            self.ui.WatchingTable,
            self.ui.PlanningTable,
            self.ui.DroppedTable,
            self.ui.PausedTable,
        ]

    def get_table(self, status: UserStatus):
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

    def insert_row(self, table: QTableWidget, anime: AnimeCollection):
        row_pos = table.rowCount()

        table.insertRow(row_pos)

        # Add the progress bar at position 0
        bar = QProgressBar()
        bar.setMinimum(0)
        bar.setMaximum(anime.episode_count)
        bar.setValue(anime.progress)
        bar.setFormat("%v/%m")
        if anime.missing_eps:
            tt = f"Missing episodes: {anime.missing_eps}"
        else:
            tt = "Found all episodes"

        bar.setToolTip(tt)
        table.setCellWidget(row_pos, 0, bar)
        # Add an item along with the progressbar to enable sorting
        item = QTableWidgetItem()
        if anime.episode_count:
            item.setData(Qt.DisplayRole, anime.progress / anime.episode_count)
        else:
            item.setData(Qt.DisplayRole, 0)
        item.anime = anime
        # item.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # item.customContextMenuRequested.connect(self.open_anime_context_menu)
        table.setItem(row_pos, 0, item)

        for index, attr in enumerate(self._header_labels, start=1):
            piece = getattr(anime, attr, "")
            if isinstance(piece, Enum):
                piece = piece.name.title()
            elif isinstance(piece, date):
                piece = str(piece)

            item = QTableWidgetItem()
            # item.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            # item.customContextMenuRequested.connect(self.open_anime_context_menu)
            item.setData(Qt.DisplayRole, piece)
            # Attach the anime object to it so we can use it later
            item.anime = anime
            item.setToolTip(tt)
            table.setItem(row_pos, index, item)

        # Make sure things are sorted properly
        if table.isSortingEnabled():
            # This will immediately trigger a sort based on the sort option
            # selected, so we just set it to True again, since as far as I can
            # tell there's no way to GET the current sort option
            table.setSortingEnabled(True)

    def update_row(self, table: QTableWidget, row: int, anime: AnimeCollection):
        # Set the progress bar's data
        bar = table.cellWidget(row, 0)
        bar.setMaximum(anime.episode_count)
        bar.setValue(anime.progress)
        if anime.episode_count:
            table.item(row, 0).setData(
                Qt.DisplayRole, anime.progress / anime.episode_count
            )

        if anime.missing_eps:
            tt = f"Missing episodes: {anime.missing_eps}"
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

    def open_anime_settings(
        self, anime: AnimeCollection
    ):  # Get the item at that position
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
        s.AnimeNotes.setText(anime.notes)
        s.AnimeUserScore.setValue(anime.score)
        s.AnimeUpdateButton.clicked.connect(
            functools.partial(self.update_anime_from_settings, anime)
        )
        m.show()
        m.setFixedSize(m.size())

    ### Signals

    # Settings action was clicked
    def open_settings(self):
        self.settings_menu.show()
        self.settings_menu.setFixedSize(self.settings_menu.size())

    # Confirm anilist code
    def anilist_code_confirm(self):
        token = self.settings_window.AnilistCodeBox.toPlainText()
        self.app._anilist.store_access(token)

        # Store in settings
        self.app._config["access-token"] = token
        self.app._anilist.verify()

        self.update_anilist_acc_label()

    # Header context menu option selected
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
    def open_header_menu(self, point: QPoint):
        self.current_table.menu.exec(self.ui.AnimeListTab.mapToGlobal(point))

    # Anime in table was right clicked
    def open_anime_context_menu(self, point: QPoint):
        # Get attrs that will be used a bit
        anime: AnimeCollection = self.current_table.selectedItems()[0].anime

        # Setup the menu settings
        menu = QMenu(self.current_table)
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
        remove = menu.addAction("Remove from list")

        menu.addSeparator()

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
        if next_ep not in anime.episodes:
            play_next.setEnabled(False)

        if anime.episodes:
            folder = os.path.dirname(anime.episodes[sorted(anime.episodes)[0]].file)
        elif self.app._config["animedir"] is not None:
            folder = self.app._config["animedir"]
        else:
            folder = None
            open_folder.setEnabled(False)

        if anime.episodes:
            for count in sorted(anime.episodes):
                ep = anime.episodes[count]
                act = play_menu.addAction(f"Episode {count}")
                play_opts[act] = ep
        else:
            play_menu.setEnabled(False)

        action = menu.exec(QCursor.pos())

        if action == settings:
            self.open_anime_settings(anime)
        elif action == plan:
            anime.edit(self.app._anilist, status=UserStatus.PLANNING)
        elif action == complete:
            anime.edit(self.app._anilist, status=UserStatus.COMPLETED)
        elif action == watch:
            if anime.user_status == UserStatus.COMPLETED:
                anime.edit(self.app._anilist, status=UserStatus.REPEATING)
            else:
                anime.edit(self.app._anilist, status=UserStatus.CURRENT)
        elif action == drop:
            anime.edit(self.app._anilist, status=UserStatus.DROPPED)
        elif action == remove:
            anime.delete(self.app._anilist)
            del self.app._animes[anime.id]
        elif action == open_folder:
            if sys.platform.startswith("win32"):
                subprocess.Popen(["start", folder], shell=True)
            elif sys.platform.startswith("linux"):
                subprocess.Popen(
                    ["xdg-open", folder],
                )
        elif action == play_next:
            self._playing_episode = PlayEpisode(anime.episodes[next_ep], self)
            self._playing_episode.start()
        elif action in play_opts:
            self._playing_episode = PlayEpisode(play_opts[action], self)
            self._playing_episode.start()

        self.handle_anime_updates(list(self.app.animes.values()))

    # Browse for anime folder was clicked
    def select_anime_path(self):
        dir = QFileDialog.getExistingDirectory(
            None, "Choose Anime Path", "", QFileDialog.ShowDirsOnly
        )

        self.settings_window.AnimeFolderLineEdit.setText(dir)
        self.app._config["animedir"] = dir

    # Line edit for subtitle language was changed
    def update_subtitles(self):
        self.app._config[
            "subtitle"
        ] = self.settings_window.SubtitleLanguageLineEdit.text()

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
                anime = table.item(row, 0).anime

                # If the anime is not in the list, remove it from the table
                if anime not in animes:
                    table.removeRow(row)

        # Now loop through the animes and handle all the updates
        for anime in animes:
            found = False
            table = self.get_table(anime.user_status)

            # Loop through every row in the table it should be in
            for row in range(table.rowCount()):
                # Found it
                if table.item(row, 0).anime == anime:
                    found = True
                    self.update_row(table, row, anime)

            # If we didn't find it, then insert it
            if not found:
                self.insert_row(table, anime)

        # Make sure things are sorted properly
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
        self.handle_anime_updates(self.app.animes.values())

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
        about.label.linkActivated.connect(webbrowser.open)
        widget.show()
        widget.setFixedSize(widget.size())

    # Report bug was clicked
    def open_issue_tracker(self):
        webbrowser.open("https://github.com/Phxntxm/AniTracker/issues")

    # Source code was clicked
    def open_repo(self):
        webbrowser.open("https://github.com/Phxntxm/AniTracker")


def main():
    app = QApplication(sys.argv)

    window = MainWindow(app)
    window.show()
    window.setFixedSize(window.size())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
