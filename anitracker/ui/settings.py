# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
##
## Created by: Qt User Interface Compiler version 6.1.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_Settings(object):
    def setupUi(self, Settings):
        if not Settings.objectName():
            Settings.setObjectName(u"Settings")
        Settings.resize(694, 276)
        Settings.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"color: rgb(212, 212, 212);")
        self.horizontalLayout = QHBoxLayout(Settings)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.SettingsTabWidget = QTabWidget(Settings)
        self.SettingsTabWidget.setObjectName(u"SettingsTabWidget")
        self.SettingsTabWidget.setStyleSheet(u"QTabWidget::pane {\n"
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
        self.GeneralSettingsTab = QWidget()
        self.GeneralSettingsTab.setObjectName(u"GeneralSettingsTab")
        self.GeneralSettingsTab.setStyleSheet(u"")
        self.AnimeFolderLineEdit = QLineEdit(self.GeneralSettingsTab)
        self.AnimeFolderLineEdit.setObjectName(u"AnimeFolderLineEdit")
        self.AnimeFolderLineEdit.setGeometry(QRect(140, 10, 125, 23))
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.AnimeFolderLineEdit.sizePolicy().hasHeightForWidth())
        self.AnimeFolderLineEdit.setSizePolicy(sizePolicy)
        self.AnimeFolderLineEdit.setReadOnly(True)
        self.AnimeFolderBrowse = QPushButton(self.GeneralSettingsTab)
        self.AnimeFolderBrowse.setObjectName(u"AnimeFolderBrowse")
        self.AnimeFolderBrowse.setGeometry(QRect(280, 10, 80, 23))
        sizePolicy.setHeightForWidth(self.AnimeFolderBrowse.sizePolicy().hasHeightForWidth())
        self.AnimeFolderBrowse.setSizePolicy(sizePolicy)
        self.AnimeFolderSettingsLabel = QLabel(self.GeneralSettingsTab)
        self.AnimeFolderSettingsLabel.setObjectName(u"AnimeFolderSettingsLabel")
        self.AnimeFolderSettingsLabel.setGeometry(QRect(10, 10, 91, 16))
        sizePolicy.setHeightForWidth(self.AnimeFolderSettingsLabel.sizePolicy().hasHeightForWidth())
        self.AnimeFolderSettingsLabel.setSizePolicy(sizePolicy)
        self.SubtitleLanguageLineEdit = QLineEdit(self.GeneralSettingsTab)
        self.SubtitleLanguageLineEdit.setObjectName(u"SubtitleLanguageLineEdit")
        self.SubtitleLanguageLineEdit.setGeometry(QRect(140, 40, 125, 23))
        sizePolicy.setHeightForWidth(self.SubtitleLanguageLineEdit.sizePolicy().hasHeightForWidth())
        self.SubtitleLanguageLineEdit.setSizePolicy(sizePolicy)
        self.SubtitleLanguageSettingsLabel = QLabel(self.GeneralSettingsTab)
        self.SubtitleLanguageSettingsLabel.setObjectName(u"SubtitleLanguageSettingsLabel")
        self.SubtitleLanguageSettingsLabel.setGeometry(QRect(10, 40, 121, 16))
        sizePolicy.setHeightForWidth(self.SubtitleLanguageSettingsLabel.sizePolicy().hasHeightForWidth())
        self.SubtitleLanguageSettingsLabel.setSizePolicy(sizePolicy)
        self.IgnoreSongsSignsCheckbox = QCheckBox(self.GeneralSettingsTab)
        self.IgnoreSongsSignsCheckbox.setObjectName(u"IgnoreSongsSignsCheckbox")
        self.IgnoreSongsSignsCheckbox.setGeometry(QRect(10, 70, 223, 21))
        self.SettingsTabWidget.addTab(self.GeneralSettingsTab, "")
        self.AnilistSettingsTab = QWidget()
        self.AnilistSettingsTab.setObjectName(u"AnilistSettingsTab")
        self.AnilistInstructionsLabel = QLabel(self.AnilistSettingsTab)
        self.AnilistInstructionsLabel.setObjectName(u"AnilistInstructionsLabel")
        self.AnilistInstructionsLabel.setGeometry(QRect(130, 0, 395, 69))
        self.AnilistInstructionsLabel.setAlignment(Qt.AlignCenter)
        self.AnilistConnectedAccountLabel = QLabel(self.AnilistSettingsTab)
        self.AnilistConnectedAccountLabel.setObjectName(u"AnilistConnectedAccountLabel")
        self.AnilistConnectedAccountLabel.setGeometry(QRect(10, 80, 147, 16))
        self.AnilistConnectedAccountLabel.setAlignment(Qt.AlignCenter)
        self.AnilistConnect = QPushButton(self.AnilistSettingsTab)
        self.AnilistConnect.setObjectName(u"AnilistConnect")
        self.AnilistConnect.setGeometry(QRect(0, 30, 114, 23))
        self.AnilistCodeConfirm = QPushButton(self.AnilistSettingsTab)
        self.AnilistCodeConfirm.setObjectName(u"AnilistCodeConfirm")
        self.AnilistCodeConfirm.setGeometry(QRect(540, 30, 131, 23))
        self.AnilistCodeBox = QTextEdit(self.AnilistSettingsTab)
        self.AnilistCodeBox.setObjectName(u"AnilistCodeBox")
        self.AnilistCodeBox.setGeometry(QRect(250, 80, 411, 130))
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.AnilistCodeBox.sizePolicy().hasHeightForWidth())
        self.AnilistCodeBox.setSizePolicy(sizePolicy1)
        self.SettingsTabWidget.addTab(self.AnilistSettingsTab, "")

        self.horizontalLayout.addWidget(self.SettingsTabWidget)


        self.retranslateUi(Settings)

        self.SettingsTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Settings)
    # setupUi

    def retranslateUi(self, Settings):
        Settings.setWindowTitle(QCoreApplication.translate("Settings", u"Settings", None))
        self.AnimeFolderBrowse.setText(QCoreApplication.translate("Settings", u"Browse", None))
        self.AnimeFolderSettingsLabel.setText(QCoreApplication.translate("Settings", u"Anime Folder:", None))
        self.SubtitleLanguageSettingsLabel.setText(QCoreApplication.translate("Settings", u"Subtitle Language:", None))
        self.IgnoreSongsSignsCheckbox.setText(QCoreApplication.translate("Settings", u"Ignore Songs and Signs Subtitles", None))
        self.SettingsTabWidget.setTabText(self.SettingsTabWidget.indexOf(self.GeneralSettingsTab), QCoreApplication.translate("Settings", u"General", None))
        self.AnilistInstructionsLabel.setText(QCoreApplication.translate("Settings", u"<html><head/><body><p>To connect a new account, click Connect to anilist to the left</p><p>Login, then copy the code provided, enter it in the text box below</p><p>Then hit Confirm Code to the right</p></body></html>", None))
        self.AnilistConnectedAccountLabel.setText(QCoreApplication.translate("Settings", u"Connected account: N/A", None))
        self.AnilistConnect.setText(QCoreApplication.translate("Settings", u"Connect to anilist", None))
        self.AnilistCodeConfirm.setText(QCoreApplication.translate("Settings", u"Confirm Code", None))
        self.SettingsTabWidget.setTabText(self.SettingsTabWidget.indexOf(self.AnilistSettingsTab), QCoreApplication.translate("Settings", u"Anilist", None))
    # retranslateUi

