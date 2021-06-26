from __future__ import annotations

import sys
import time
from datetime import date
from enum import Enum
from typing import Dict, List, Optional, Union


from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from anitracker.anitracker import AniTracker
from anitracker.background import *
from anitracker.media import AnimeCollection, UserStatus, AnimeFile
from anitracker.ui import Ui_AnimeApp, Ui_AnimeInfo, Ui_Settings


class MouseFilter(QObject):
    def __init__(self, table: QTableWidget, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)

        self._table = table
        self._cur_anime: Union[AnimeCollection, None] = None
        self._playing_episode: Union[AnimeFile, None] = None

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # If we've pressed and released
        if event.type() is QEvent.MouseButtonDblClick:
            # Get the item at that position
            item = self._table.itemAt(event.position().toPoint())
            # # If it's not an item, it's a widget
            # if item is None:
            #     # The only way to get a widget is by row column
            #     # so we have to do that first
            #     index = self._table.indexAt(event.position().toPoint())
            #     item = self._table.cellWidget(index.row(), index.column())
            # Pull up anime info
            s = self.parent().anime_window
            m = self.parent().anime_menu
            a: AnimeCollection = item.anime
            self._cur_anime = a
            s.AnimeTitleLabel.setText("\n".join(a.titles))
            s.AnimeDescriptionLabel.setText(a.description)
            s.AnimeGenresLabel.setText("\n".join(a.genres))
            tags = sorted(a.tags, key=lambda t: t[1], reverse=True)
            tagfmt = "\n".join(f"{tag[0]} {tag[1]}%" for tag in tags)
            s.AnimeTagsLabel.setText(tagfmt)
            s.AnimeStudioLabel.setText(a.studio)
            s.AnimeSeasonLabel.setText(a.season)
            s.AnimeAverageScoreLabel.setText(f"{a.average_score}%")
            s.AnimeEpisodesLabel.setText(str(a.episode_count))
            s.AnimeNotes.setText(a.notes)
            s.AnimeUserScore.setValue(a.score)
            s.AnimeUpdateButton.clicked.connect(self.update_anime)
            m.show()
            m.setFixedSize(m.size())

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

    def update_anime(self):
        notes = self.parent().anime_window.AnimeNotes.toPlainText()
        score = self.parent().anime_window.AnimeUserScore.value()

        self._cur_anime.edit(self.parent().app._anilist, score=score, notes=notes)
        self.parent().update_success.start()


class SortableProgressBar(QTableWidgetItem):
    def __lt__(self, other):
        print("Calling less than")
        return self.value() / self.maximum() < other.value() / other.maximum()

    def __lte__(self, other):
        print("Calling less than or equal to")
        return self.value() / self.maximum() <= other.value() / other.maximum()

    def __gt__(self, other):
        print("Calling greater than")
        return self.value() / self.maximum() > other.value() / other.maximum()

    def __gte__(self, other):
        print("Calling greater than or equal to")
        return self.value() / self.maximum() >= other.value() / other.maximum()


class MainWindow(QMainWindow):
    # Setup stuff
    def __init__(self):
        super().__init__()
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

        for table in [self.ui.WatchingTable, self.ui.CompletedTable]:
            # Createa menu per table
            menu = table.menu = QMenu(self.ui.AnimeListTab)
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
            table.viewport().installEventFilter(MouseFilter(table, self))
            # table.cellClicked.connect(self.test)
            # table.cellDoubleClicked.connect(self.test)
            # table.cellActivated.connect(self.test)
            # table.cellChanged.connect(self.test)
            # table.cellEntered.connect(self.test)
            # table.cellPressed.connect(self.test)
            # table.cellWidget.connect(self.test)

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

    def get_cur_table(self) -> Union[QTableWidget, None]:
        if (
            anime.user_status is UserStatus.CURRENT
            or anime.user_status is UserStatus.REPEATING
        ):
            return self.ui.WatchingTable
        elif anime.user_status is UserStatus.COMPLETED:
            return self.ui.CompletedTable
        else:
            return

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
        item.setData(Qt.DisplayRole, anime.progress / anime.episode_count)
        item.anime = anime
        table.setItem(row_pos, 0, item)

        for index, attr in enumerate(self._header_labels, start=1):
            piece = getattr(anime, attr, "")
            if isinstance(piece, Enum):
                piece = piece.name.title()
            elif isinstance(piece, date):
                piece = str(piece)

            item = QTableWidgetItem()
            item.setData(Qt.DisplayRole, piece)
            # Attach the anime object to it so we can use it later
            item.anime = anime
            item.setToolTip(tt)
            table.setItem(row_pos, index, item)

    def update_row(self, table: QTableWidget, row: int, anime: AnimeCollection):
        # Set the progress bar's data
        bar = table.cellWidget(row, 0)
        bar.setMaximum(anime.episode_count)
        bar.setValue(anime.progress)
        table.item(row, 0).setData(Qt.DisplayRole, anime.progress / anime.episode_count)

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
        # Get the table widget
        table = self.ui.AnimeListTab.currentWidget().findChild(QTableWidget)
        # Set the column hidden based on the action's checked status
        table.setColumnHidden(index + 1, not _action.isChecked())

        # Now save in config
        self.app._config.set_option(
            list(self._header_labels.keys())[index],
            _action.isChecked(),
            section=table.objectName(),
        )

    # Header was right clicked
    def open_header_menu(self, point: QPoint):
        self.ui.AnimeListTab.currentWidget().findChild(QTableWidget).menu.exec(
            self.ui.AnimeListTab.mapToGlobal(point)
        )

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
        self.ui.WatchingTable.setRowCount(0)
        self.ui.CompletedTable.setRowCount(0)

    # Update all animes from anilist
    def handle_anime_updates(self, animes: List[AnimeCollection]):
        wtable = self.ui.WatchingTable
        ctable = self.ui.CompletedTable
        wtablecount = wtable.rowCount()
        ctablecount = ctable.rowCount()

        # We want to remove any unhandled rows, as they must have been
        # completely removed from
        unhandled_rows = {
            wtable: list(range(wtablecount)),
            ctable: list(range(ctablecount)),
        }

        # Now loop through the animes and handle all the updates
        for anime in animes:
            found = False
            if anime.user_status is UserStatus.COMPLETED:
                table = ctable
                count = ctablecount
            elif anime.user_status in [UserStatus.REPEATING, UserStatus.CURRENT]:
                table = wtable
                count = wtablecount
            else:
                continue

            # Loop through every row in the table it should be in
            for row in range(count):
                # Found it
                if table.item(row, 0).anime == anime:
                    unhandled_rows[table].remove(row)
                    found = True
                    self.update_row(table, row, anime)

            # If we didn't find it, then insert it
            if not found:
                self.insert_row(table, anime)

        # Now that we're done, loop through all the unhandled rows and remove them
        for table in unhandled_rows:
            for row in unhandled_rows[table]:
                table.removeRow(row)

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


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    window.setFixedSize(window.size())

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
