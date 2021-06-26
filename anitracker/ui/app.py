# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'app.ui'
##
## Created by: Qt User Interface Compiler version 6.1.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore

from anitracker import resources_rc

class Ui_AnimeApp(object):
    def setupUi(self, AnimeApp):
        if not AnimeApp.objectName():
            AnimeApp.setObjectName(u"AnimeApp")
        AnimeApp.resize(800, 600)
        AnimeApp.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"color: rgb(212, 212, 212);")
        self.actionSettings = QAction(AnimeApp)
        self.actionSettings.setObjectName(u"actionSettings")
        self.actionRefresh = QAction(AnimeApp)
        self.actionRefresh.setObjectName(u"actionRefresh")
        icon = QIcon()
        icon.addFile(u":/refresh/icons8-refresh-30.png", QSize(), QIcon.Normal, QIcon.Off)
        self.actionRefresh.setIcon(icon)
        self.actionReload_Videos = QAction(AnimeApp)
        self.actionReload_Videos.setObjectName(u"actionReload_Videos")
        icon1 = QIcon()
        icon1.addFile(u":/reload_videos/icons8-video-playlist-50.png", QSize(), QIcon.Normal, QIcon.Off)
        self.actionReload_Videos.setIcon(icon1)
        self.MainWidget = QWidget(AnimeApp)
        self.MainWidget.setObjectName(u"MainWidget")
        self.MainWidget.setStyleSheet(u"background-color: rgb(55, 55, 61);\n"
"alternate-background-color: rgb(84, 84, 93);\n"
"color: rgb(212, 212, 212);")
        self.gridLayout = QGridLayout(self.MainWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.AnimeListTab = QTabWidget(self.MainWidget)
        self.AnimeListTab.setObjectName(u"AnimeListTab")
        self.WatchingTab = QWidget()
        self.WatchingTab.setObjectName(u"WatchingTab")
        self.gridLayout_2 = QGridLayout(self.WatchingTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.WatchingTable = QTableWidget(self.WatchingTab)
        self.WatchingTable.setObjectName(u"WatchingTable")
        self.WatchingTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.WatchingTable.setAlternatingRowColors(True)
        self.WatchingTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.WatchingTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.WatchingTable.setShowGrid(True)
        self.WatchingTable.setGridStyle(Qt.SolidLine)
        self.WatchingTable.setSortingEnabled(True)
        self.WatchingTable.setWordWrap(False)
        self.WatchingTable.setCornerButtonEnabled(False)
        self.WatchingTable.setRowCount(0)
        self.WatchingTable.setColumnCount(0)
        self.WatchingTable.horizontalHeader().setHighlightSections(False)
        self.WatchingTable.verticalHeader().setVisible(False)
        self.WatchingTable.verticalHeader().setHighlightSections(False)

        self.gridLayout_2.addWidget(self.WatchingTable, 0, 0, 1, 1)

        self.AnimeListTab.addTab(self.WatchingTab, "")
        self.CompletedTab = QWidget()
        self.CompletedTab.setObjectName(u"CompletedTab")
        self.gridLayout_3 = QGridLayout(self.CompletedTab)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.CompletedTable = QTableWidget(self.CompletedTab)
        self.CompletedTable.setObjectName(u"CompletedTable")
        self.CompletedTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.CompletedTable.setAlternatingRowColors(True)
        self.CompletedTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.CompletedTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.CompletedTable.setSortingEnabled(True)
        self.CompletedTable.setWordWrap(False)
        self.CompletedTable.setCornerButtonEnabled(False)
        self.CompletedTable.horizontalHeader().setHighlightSections(False)
        self.CompletedTable.horizontalHeader().setStretchLastSection(False)
        self.CompletedTable.verticalHeader().setVisible(False)
        self.CompletedTable.verticalHeader().setHighlightSections(False)
        self.CompletedTable.verticalHeader().setStretchLastSection(True)

        self.gridLayout_3.addWidget(self.CompletedTable, 0, 0, 1, 1)

        self.AnimeListTab.addTab(self.CompletedTab, "")

        self.gridLayout.addWidget(self.AnimeListTab, 0, 0, 1, 1)

        AnimeApp.setCentralWidget(self.MainWidget)
        self.menubar = QMenuBar(AnimeApp)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 20))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        AnimeApp.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(AnimeApp)
        self.statusbar.setObjectName(u"statusbar")
        AnimeApp.setStatusBar(self.statusbar)
        self.toolBar = QToolBar(AnimeApp)
        self.toolBar.setObjectName(u"toolBar")
        self.toolBar.setMovable(False)
        self.toolBar.setFloatable(False)
        AnimeApp.addToolBar(Qt.TopToolBarArea, self.toolBar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionSettings)
        self.toolBar.addAction(self.actionRefresh)
        self.toolBar.addAction(self.actionReload_Videos)

        self.retranslateUi(AnimeApp)

        self.AnimeListTab.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AnimeApp)
    # setupUi

    def retranslateUi(self, AnimeApp):
        AnimeApp.setWindowTitle(QCoreApplication.translate("AnimeApp", u"MainWindow", None))
        self.actionSettings.setText(QCoreApplication.translate("AnimeApp", u"Settings", None))
        self.actionRefresh.setText(QCoreApplication.translate("AnimeApp", u"Refresh", None))
#if QT_CONFIG(tooltip)
        self.actionRefresh.setToolTip(QCoreApplication.translate("AnimeApp", u"Refresh data from connected account", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionRefresh.setShortcut(QCoreApplication.translate("AnimeApp", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
        self.actionReload_Videos.setText(QCoreApplication.translate("AnimeApp", u"Reload Videos", None))
#if QT_CONFIG(tooltip)
        self.actionReload_Videos.setToolTip(QCoreApplication.translate("AnimeApp", u"Reload videos from the anime folder", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionReload_Videos.setShortcut(QCoreApplication.translate("AnimeApp", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.WatchingTab), QCoreApplication.translate("AnimeApp", u"Watching", None))
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.CompletedTab), QCoreApplication.translate("AnimeApp", u"Completed", None))
        self.menuFile.setTitle(QCoreApplication.translate("AnimeApp", u"File", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("AnimeApp", u"toolBar", None))
    # retranslateUi

