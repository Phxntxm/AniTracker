from __future__ import annotations

from enum import Enum
import os
import pycountry
import shlex
import sys
import subprocess
import webbrowser
from typing import Callable, TYPE_CHECKING, List, Union, cast, Optional

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore

from anitracker import __version__
from anitracker.ui import Ui_About, Ui_Settings
from anitracker.media import Anime, AnimeCollection, UserStatus
from anitracker.background import PlayEpisode, EditAnime

if TYPE_CHECKING:
    from anitracker.__main__ import MainWindow


class HiddenProgressBarItem(QTableWidgetItem):
    def __init__(self, anime: Union[AnimeCollection, Anime]) -> None:
        super().__init__("")
        self.anime = anime

    @property
    def amount(self) -> float:
        if isinstance(self.anime, AnimeCollection):
            return (
                self.anime.progress / self.anime.episode_count
                if self.anime.episode_count
                else 0.0
            )
        else:
            return 0.0

    def __lt__(self, other):
        return self.amount < other.amount


class AnimeWidgetItem(QTableWidgetItem):
    def __init__(self, anime: Union[AnimeCollection, Anime]):
        super().__init__()

        self.anime = anime


class LinkWidgetItem(QTableWidgetItem):
    def __init__(self, link: str):
        super().__init__()

        self.link = link


class MouseFilter(QObject):
    def __init__(self, table: QTableWidget, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)

        self._table = table
        self._playing_episode: Union[PlayEpisode, None] = None

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        parent: MainWindow = self.parent()  # type: ignore

        if not isinstance(event, QMouseEvent):
            return False

        # Get the item at that position
        item = self._table.itemAt(event.pos())

        if isinstance(item, AnimeWidgetItem):
            # If we've pressed and released
            if event.type() is QEvent.MouseButtonDblClick:
                parent.open_anime_settings(item.anime)

            if (
                event.type() is QEvent.MouseButtonRelease
                and event.button() is Qt.MiddleButton
                and isinstance(item.anime, AnimeCollection)
            ):
                self._playing_episode = PlayEpisode(
                    item.anime, item.anime.progress + 1, parent
                )
                self._playing_episode.start()
        elif isinstance(item, LinkWidgetItem):
            if event.type() is QEvent.MouseButtonDblClick:
                if sys.platform.startswith("linux"):
                    cmd = shlex.split(f"xdg-open '{item.link}'")
                    subprocess.run(
                        cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                    )
                elif sys.platform.startswith("win32"):
                    cmd = shlex.split(f"start '{item.link}'")
                    subprocess.run(
                        cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
                    )

        return super().eventFilter(watched, event)


class SignalConnector:
    def __init__(self, window: MainWindow) -> None:
        self.window = window

    # Settings action was clicked
    def open_settings(self):
        # Settings menu stuff
        w = self.settings_widget = QTabWidget()
        s = self.settings_window = Ui_Settings()
        s.setupUi(w)

        s.SubtitleLanguage.clear()
        s.SubtitleLanguage.addItems(sorted([l.name for l in pycountry.languages]))

        # Setup initial settings info
        try:
            s.AnimeFolderLineEdit.setText(self.window.app._config["animedir"])
        except KeyError:
            pass
        try:
            s.SubtitleLanguage.setCurrentText(
                pycountry.languages.get(
                    alpha_3=self.window.app._config["subtitle"]
                ).name
            )
        except (KeyError, AttributeError):
            pass
        try:
            b = self.window.app._config["skip_songs_signs"]
            state = Qt.CheckState.Checked if b else Qt.CheckState.Unchecked
            s.IgnoreSongsSignsCheckbox.setCheckState(state)
        except KeyError:
            pass

        self.window.anilist_connector.update_label.connect(  # type: ignore
            s.AnilistConnectedAccountLabel.setText
        )
        s.AnilistConnectedAccountLabel.setText(
            f"Connected account: {self.window.app._anilist.name}"
        )
        s.AnilistConnect.clicked.connect(self.window.app._anilist.open_oauth)  # type: ignore
        s.AnilistCodeConfirm.clicked.connect(self.anilist_code_confirm)  # type: ignore
        s.AnimeFolderBrowse.clicked.connect(self.select_anime_path)  # type: ignore
        s.IgnoreSongsSignsCheckbox.stateChanged.connect(  # type: ignore
            self.update_songs_signs
        )
        s.SubtitleLanguage.currentIndexChanged.connect(  # type: ignore
            self.change_language
        )

        w.setFixedSize(w.size().width(), w.size().height())
        w.show()

    # Confirm anilist code
    def anilist_code_confirm(self):
        token = self.settings_window.AnilistCodeBox.toPlainText()
        self.window.app._anilist.store_access(token)

        # Store in settings
        self.window.app._config["access-token"] = token
        self.window.app._anilist.verify()

        # Update label
        if self.window.app._anilist.authenticated:
            self.settings_window.AnilistConnectedAccountLabel.setText(
                f"Connected account: {self.window.app._anilist.name}"
            )


    # Header context menu option selected
    def header_changed(self, table: QTableWidget, _action: QAction):
        # Loop through each column
        for index in range(table.columnCount()):
            # Get the text for this header
            text = table.horizontalHeaderItem(index).text()
            # If this is the text that matters
            if text == _action.text():
                table.setColumnHidden(index, not _action.isChecked())
                # Now set this option in the config
                self.window.app._config.set_option(
                    _action.text().lower().replace(" ", "_"),
                    _action.isChecked(),
                    section=table.objectName(),
                )
                return

    # Header was right clicked
    def open_header_menu(self, table: QTableWidget, point: QPoint):
        table.menu.exec_(self.window.ui.AnimeListTab.mapToGlobal(point))  # type: ignore

    # Anime in table was right clicked
    def open_anime_context_menu(self, table: QTableWidget, _: QPoint):
        # Get attrs that will be used a bit
        anime: Union[AnimeCollection, Anime] = cast(AnimeWidgetItem, table.selectedItems()[0]).anime

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

        # Just to shut up the linter
        remove = None
        folder = ""
        open_folder = None
        play_next = None
        play_opts = {}
        next_ep = 0

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
            if not self.window.app.get_episode(anime, next_ep):
                play_next.setEnabled(False)

            if eps := self.window.app.get_episodes(anime):
                folder = os.path.dirname(
                    sorted(eps, key=lambda k: k.episode_number)[0].file
                )
            elif self.window.app._config["animedir"] is not None:
                folder = self.window.app._config["animedir"]
            else:
                folder = None
                open_folder.setEnabled(False)

            for ep in sorted(
                self.window.app.get_episodes(anime), key=lambda k: k.episode_number
            ):
                act = play_menu.addAction(f"Episode {ep.episode_number}")
                play_opts[act] = ep.episode_number

            if not play_opts:
                play_menu.setEnabled(False)

        action = menu.exec_(QCursor.pos())

        if action == settings:
            self.window.open_anime_settings(anime)
        elif action == plan:
            anime.edit(self.window.app._anilist, status=UserStatus.PLANNING)
        elif action == complete:
            anime.edit(self.window.app._anilist, status=UserStatus.COMPLETED)
        elif action == watch:
            if (
                isinstance(anime, AnimeCollection)
                and anime.user_status == UserStatus.COMPLETED
            ):
                anime.edit(self.window.app._anilist, status=UserStatus.REPEATING)
            else:
                anime.edit(self.window.app._anilist, status=UserStatus.CURRENT)
        elif action == drop:
            anime.edit(self.window.app._anilist, status=UserStatus.DROPPED)

        # Anime Collection specific items
        if isinstance(anime, AnimeCollection):
            if action == remove:
                anime.delete(self.window.app._anilist)
                del self.window.app._animes[anime.id]
            elif action == open_folder and folder is not None:
                if sys.platform.startswith("win32"):
                    subprocess.Popen(["start", folder], shell=True)
                elif sys.platform.startswith("linux"):
                    subprocess.Popen(
                        ["xdg-open", folder],
                    )
            elif action == play_next:
                self._playing_episode = PlayEpisode(anime, next_ep, self.window)
                self._playing_episode.start()
            elif action in play_opts:
                self._playing_episode = PlayEpisode(
                    anime, play_opts[action], self.window
                )
                self._playing_episode.start()

        # If we've edited an Anime class directly, that means we modifed our list from
        # a non list-item... IE added it to it. So we need to refresh from anilist
        if not isinstance(anime, AnimeCollection):
            self.window.anime_updater.start()

        self.handle_anime_updates(list(self.window.app.animes.values()))

    # Browse for anime folder was clicked
    def select_anime_path(self):
        dir = QFileDialog.getExistingDirectory(
            None, "Choose Anime Path", "", QFileDialog.ShowDirsOnly # type: ignore
        )

        self.settings_window.AnimeFolderLineEdit.setText(dir)
        self.window.app._config["animedir"] = dir

    # Checkbox for songs/signs was changed
    def update_songs_signs(self):
        self.window.app._config["skip_songs_signs"] = (
            self.settings_window.IgnoreSongsSignsCheckbox.checkState()
            is Qt.CheckState.Checked
        )

    # Update all animes from anilist
    def handle_anime_updates(self, animes: List[AnimeCollection]):
        # First, handle any animes in the tables but not in the list of animes
        for table in self.window.tables:
            # Reverse through the range, so that removal of rows
            # doesn't mess up what we're looking at
            for row in range(table.rowCount() - 1, -1, -1):
                anime: AnimeCollection = table.item(row, 0).anime  # type: ignore

                # If the anime is not in the list, remove it from the table
                if anime not in animes:
                    table.removeRow(row)
                # Otherwise if this table doesn't match the anime's status, remove it
                elif self.window.get_table(anime.user_status) != table:
                    table.removeRow(row)

        # Now loop through the animes and handle all the updates
        for anime in animes:
            found = False
            table = self.window.get_table(anime.user_status)

            # Loop through every row in the table it should be in
            for row in range(table.rowCount()):
                # Found it
                if cast(AnimeWidgetItem, table.item(row, 0)).anime == anime:
                    found = True
                    self.window.update_row_signal.emit(table, row, anime)  # type: ignore

            # If we didn't find it, then insert it
            if not found:
                self.window.insert_row_signal.emit(table, anime)  # type: ignore

        # Make sure things are sorted properly
        for table in self.window.tables:
            if table.isSortingEnabled():
                # This will immediately trigger a sort based on the sort option
                # selected, so we just set it to True again, since as far as I can
                # tell there's no way to GET the current sort option
                table.setSortingEnabled(True)

    # Toggle visible success label
    def toggle_success(self):
        self.window.anime_window.AnimeUpdateSuccess.setVisible(
            not self.window.anime_window.AnimeUpdateSuccess.isVisible()
        )

    # Files were refreshed, update anime tooltip info
    def reload_anime_eps(self):
        self.handle_anime_updates(list(self.window.app.animes.values()))

    # Anime settings submit button was clicked
    def update_anime_from_settings(self, anime: AnimeCollection):
        notes = self.window.anime_window.AnimeNotes.toPlainText()
        score = self.window.anime_window.AnimeUserScore.value()

        self._anime_editing_thread = EditAnime(
            self.window, anime, notes=notes, score=score
        )
        self._anime_editing_thread.start()

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
        for table in self.window.tables:
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
            status = self.window.statuses[0]
        except IndexError:
            self.window.ui.StatusLabel.setText("")
        else:
            self.window.ui.StatusLabel.setText(status.status)
            self.window.ui.StatusLabel.setStyleSheet(f"color: {status.color}")

    # Language option was changed
    def change_language(self, index):
        lang = self.settings_window.SubtitleLanguage.itemText(index)
        alpha_3 = pycountry.languages.get(name=lang).alpha_3
        self.window.app._config["subtitle"] = alpha_3

    # Page was updated
    def change_page(self, row: int):
        self.window.ui.AnimePages.setCurrentIndex(row)

    # Change banner
    def change_banner(self, item: AnimeWidgetItem):
        self.window.ui.BannerViewer.setUrl(QUrl(item.anime.cover_image))

    # Search anilist
    def search_anime(self):
        results = self.window.app._anilist.search_anime(
            self.window.ui.AnilistSearchLineEdit.text()
        )

        for result in results:
            self.window.insert_row_signal.emit(  # type: ignore
                self.window.ui.AnilistSearchResults, result
            )

    # Search nyaa.si
    def search_nyaa(self):
        nyaa = self.window.ui.NyaaSearchResults
        nyaa.setRowCount(0)

        for result in self.window.app.search_nyaa(
            self.window.ui.NyaaSearchLineEdit.text()
        ):
            nyaa.insertRow(nyaa.rowCount())

            for i in range(nyaa.columnCount()):
                r = result[i]
                if r.isdigit():
                    r = int(r)

                item = LinkWidgetItem(result[len(result) - 1])
                item.setData(Qt.DisplayRole, r) # type: ignore
                item.setToolTip(result[i])
                nyaa.setItem(nyaa.rowCount() - 1, i, item)

    # Insert a row into the specified table
    def insert_row(self, table: QTableWidget, anime: Union[AnimeCollection, Anime]):
        row_pos = table.rowCount()
        table.insertRow(row_pos)

        if isinstance(anime, AnimeCollection):

            # Add the progress bar at position 0
            bar = QProgressBar()
            # bar.setMinimum(0)
            bar.setMaximum(anime.episode_count)
            # bar.setMaximumHeight(15)
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
            cell_widget.setLayout(layout)

            bar.setValue(anime.progress)
            bar.setFormat("%v/%m")
            # Don't show progress bar if there are no episodes
            if anime.episode_count == 0:
                bar.setVisible(False)

            if missing := self.window.app.missing_eps(anime):
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
            # Skip the progress, we handled that already
            if header == "progress":
                continue

            piece = getattr(anime, header, "")
            if isinstance(piece, Enum):
                piece = piece.name.title()
            else:
                piece = str(piece)
            if piece.isdigit():
                piece = int(piece)

            # Create our custom anime widget item
            item = AnimeWidgetItem(anime)
            item.setData(Qt.DisplayRole, piece) # type: ignore
            item.setToolTip(str(piece))
            table.setItem(row_pos, index, item)

        # # Make sure things are sorted properly
        if table.isSortingEnabled():
            # This will immediately trigger a sort based on the sort option
            # selected, so we just set it to True again, since as far as I can
            # tell there's no way to GET the current sort option
            table.setSortingEnabled(True)

    # Update a specific row to an anime
    def update_row(self, table: QTableWidget, row: int, anime: AnimeCollection):
        # Set the progress bar's data
        bar = cast(QProgressBar, table.cellWidget(row, 0).findChild(QProgressBar))
        bar.setMaximum(anime.episode_count)
        bar.setValue(anime.progress)
        if anime.episode_count:
            table.item(row, 0).setData(
                Qt.UserRole, anime.progress / anime.episode_count # type: ignore
            )

        if missing := self.window.app.missing_eps(anime):
            bar.setToolTip(f"Missing episodes: {missing}")
        else:
            bar.setToolTip("Found all episodes")

        # Now loop through the normal headers
        for index, attr in enumerate(self.window._header_labels, start=1):
            piece = getattr(anime, attr, "")

            # Skip the progress, we handled that already
            if attr == "progress":
                continue

            if isinstance(piece, Enum):
                piece = piece.name.title()
            else:
                piece = str(piece)
            if piece.isdigit():
                piece = int(piece)

            table.item(row, index).setData(Qt.DisplayRole, piece) # type: ignore
            table.item(row, index).setToolTip(str(piece))

    # Column was resized in a table
    def resized_column(self, table: QTableWidget, column: int, _: int, size: int):
        # This happens on initial startup
        if size == 0:
            return

        # Now set this option in the config
        self.window.app._config.set_option(
            str(column), size, section=table.objectName()
        )

    # This is simply here to facilitate easier handling of UI updates in threads
    def handle_ui_update(self, func: Callable[..., None]):
        func()
