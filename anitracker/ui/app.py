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
        self.actionAbout = QAction(AnimeApp)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionReport_bug = QAction(AnimeApp)
        self.actionReport_bug.setObjectName(u"actionReport_bug")
        self.actionSource_code = QAction(AnimeApp)
        self.actionSource_code.setObjectName(u"actionSource_code")
        self.MainWidget = QWidget(AnimeApp)
        self.MainWidget.setObjectName(u"MainWidget")
        self.MainWidget.setStyleSheet(u"background-color: rgb(55, 55, 61);\n"
"alternate-background-color: rgb(84, 84, 93);\n"
"color: rgb(212, 212, 212);")
        self.gridLayout = QGridLayout(self.MainWidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.AnimeListTab = QTabWidget(self.MainWidget)
        self.AnimeListTab.setObjectName(u"AnimeListTab")
        self.AnimeListTab.setStyleSheet(u"QHeaderView::section{\n"
"	background-color: rgb(68, 68, 68);\n"
"}\n"
"QTabWidget::pane {\n"
"	border: 2px solid #C2C7CB;\n"
"}\n"
"QTabWidget::tab-bar {\n"
"	left: 5px;\n"
"}\n"
"QTabBar::tab {\n"
"	background: rgb(68, 68, 68);\n"
"    border: 2px solid #C4C4C3;\n"
"    border-bottom-color: #C2C7CB;\n"
"    border-top-left-radius: 4px;\n"
"    border-top-right-radius: 4px;\n"
"    min-width: 8ex;\n"
"    padding: 2px;\n"
"}\n"
"QTabBar::tab:selected, QTabBar::tab:hover {\n"
"	background: rgb(95, 95, 95);\n"
"}\n"
"QTabBar::tab:selected {\n"
"	border-color: #9B9B9B;\n"
"	border-bottom-color: #C2C7CB;\n"
"}\n"
"QTabBar::tab:!selected {\n"
"	margin-top: 2px;\n"
"}")
        self.WatchingTab = QWidget()
        self.WatchingTab.setObjectName(u"WatchingTab")
        self.gridLayout_2 = QGridLayout(self.WatchingTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.WatchingTable = QTableWidget(self.WatchingTab)
        self.WatchingTable.setObjectName(u"WatchingTable")
        self.WatchingTable.setContextMenuPolicy(Qt.CustomContextMenu)
        self.WatchingTable.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"alternate-background-color: rgb(95, 95, 95);\n"
"color: rgb(212, 212, 212);")
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
        self.CompletedTable.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"alternate-background-color: rgb(95, 95, 95);\n"
"color: rgb(212, 212, 212);")
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
        self.CompletedTable.verticalHeader().setStretchLastSection(False)

        self.gridLayout_3.addWidget(self.CompletedTable, 0, 0, 1, 1)

        self.AnimeListTab.addTab(self.CompletedTab, "")
        self.PlanningTab = QWidget()
        self.PlanningTab.setObjectName(u"PlanningTab")
        self.gridLayout_4 = QGridLayout(self.PlanningTab)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.PlanningTable = QTableWidget(self.PlanningTab)
        self.PlanningTable.setObjectName(u"PlanningTable")
        self.PlanningTable.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"alternate-background-color: rgb(95, 95, 95);\n"
"color: rgb(212, 212, 212);")
        self.PlanningTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.PlanningTable.setAlternatingRowColors(True)
        self.PlanningTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.PlanningTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.PlanningTable.setSortingEnabled(True)
        self.PlanningTable.setWordWrap(False)
        self.PlanningTable.setCornerButtonEnabled(False)
        self.PlanningTable.horizontalHeader().setHighlightSections(False)
        self.PlanningTable.verticalHeader().setVisible(False)
        self.PlanningTable.verticalHeader().setHighlightSections(False)
        self.PlanningTable.verticalHeader().setStretchLastSection(False)

        self.gridLayout_4.addWidget(self.PlanningTable, 0, 0, 1, 1)

        self.AnimeListTab.addTab(self.PlanningTab, "")
        self.PausedTab = QWidget()
        self.PausedTab.setObjectName(u"PausedTab")
        self.gridLayout_5 = QGridLayout(self.PausedTab)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.PausedTable = QTableWidget(self.PausedTab)
        self.PausedTable.setObjectName(u"PausedTable")
        self.PausedTable.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"alternate-background-color: rgb(95, 95, 95);\n"
"color: rgb(212, 212, 212);")
        self.PausedTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.PausedTable.setAlternatingRowColors(True)
        self.PausedTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.PausedTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.PausedTable.setSortingEnabled(True)
        self.PausedTable.setWordWrap(False)
        self.PausedTable.setCornerButtonEnabled(False)
        self.PausedTable.horizontalHeader().setHighlightSections(False)
        self.PausedTable.horizontalHeader().setProperty("showSortIndicator", True)
        self.PausedTable.verticalHeader().setVisible(False)
        self.PausedTable.verticalHeader().setHighlightSections(False)
        self.PausedTable.verticalHeader().setStretchLastSection(False)

        self.gridLayout_5.addWidget(self.PausedTable, 0, 0, 1, 1)

        self.AnimeListTab.addTab(self.PausedTab, "")
        self.DroppedTab = QWidget()
        self.DroppedTab.setObjectName(u"DroppedTab")
        self.gridLayout_6 = QGridLayout(self.DroppedTab)
        self.gridLayout_6.setObjectName(u"gridLayout_6")
        self.DroppedTable = QTableWidget(self.DroppedTab)
        self.DroppedTable.setObjectName(u"DroppedTable")
        self.DroppedTable.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"alternate-background-color: rgb(95, 95, 95);\n"
"color: rgb(212, 212, 212);")
        self.DroppedTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.DroppedTable.setAlternatingRowColors(True)
        self.DroppedTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.DroppedTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.DroppedTable.setSortingEnabled(True)
        self.DroppedTable.setWordWrap(False)
        self.DroppedTable.setCornerButtonEnabled(False)
        self.DroppedTable.horizontalHeader().setHighlightSections(False)
        self.DroppedTable.verticalHeader().setVisible(False)
        self.DroppedTable.verticalHeader().setHighlightSections(False)
        self.DroppedTable.verticalHeader().setStretchLastSection(False)

        self.gridLayout_6.addWidget(self.DroppedTable, 0, 0, 1, 1)

        self.AnimeListTab.addTab(self.DroppedTab, "")

        self.gridLayout.addWidget(self.AnimeListTab, 0, 0, 1, 1)

        AnimeApp.setCentralWidget(self.MainWidget)
        self.menubar = QMenuBar(AnimeApp)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 20))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuFile.setStyleSheet(u"QMenu::item:selected {background-color: #007fd4} QWidget:disabled {color: #000000} QMenu {border: 1px solid black}")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        self.menuHelp.setStyleSheet(u"QMenu::item:selected {background-color: #007fd4} QWidget:disabled {color: #000000} QMenu {border: 1px solid black}")
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
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionSettings)
        self.menuHelp.addAction(self.actionAbout)
        self.menuHelp.addAction(self.actionReport_bug)
        self.menuHelp.addAction(self.actionSource_code)
        self.toolBar.addAction(self.actionRefresh)
        self.toolBar.addAction(self.actionReload_Videos)

        self.retranslateUi(AnimeApp)

        self.AnimeListTab.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AnimeApp)
    # setupUi

    def retranslateUi(self, AnimeApp):
        AnimeApp.setWindowTitle(QCoreApplication.translate("AnimeApp", u"AniTracker", None))
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
        self.actionAbout.setText(QCoreApplication.translate("AnimeApp", u"About", None))
        self.actionReport_bug.setText(QCoreApplication.translate("AnimeApp", u"Report bug", None))
        self.actionSource_code.setText(QCoreApplication.translate("AnimeApp", u"Source code", None))
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.WatchingTab), QCoreApplication.translate("AnimeApp", u"Watching", None))
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.CompletedTab), QCoreApplication.translate("AnimeApp", u"Completed", None))
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.PlanningTab), QCoreApplication.translate("AnimeApp", u"Planning", None))
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.PausedTab), QCoreApplication.translate("AnimeApp", u"Paused", None))
        self.AnimeListTab.setTabText(self.AnimeListTab.indexOf(self.DroppedTab), QCoreApplication.translate("AnimeApp", u"Dropped", None))
        self.menuFile.setTitle(QCoreApplication.translate("AnimeApp", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("AnimeApp", u"Help", None))
        self.toolBar.setWindowTitle(QCoreApplication.translate("AnimeApp", u"toolBar", None))
    # retranslateUi

