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
        Settings.resize(733, 522)
        Settings.setStyleSheet(u"background-color: rgb(68, 68, 68);")
        self.horizontalLayout = QHBoxLayout(Settings)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.SettingsTabWidget = QTabWidget(Settings)
        self.SettingsTabWidget.setObjectName(u"SettingsTabWidget")
        self.SettingsTabWidget.setStyleSheet(u"background-color: rgb(55, 55, 61);\n"
"color: rgb(212, 212, 212);")
        self.GeneralSettingsTab = QWidget()
        self.GeneralSettingsTab.setObjectName(u"GeneralSettingsTab")
        self.gridLayout_2 = QGridLayout(self.GeneralSettingsTab)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.AnimeFolderLineEdit = QLineEdit(self.GeneralSettingsTab)
        self.AnimeFolderLineEdit.setObjectName(u"AnimeFolderLineEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.AnimeFolderLineEdit.sizePolicy().hasHeightForWidth())
        self.AnimeFolderLineEdit.setSizePolicy(sizePolicy)
        self.AnimeFolderLineEdit.setReadOnly(True)

        self.gridLayout_2.addWidget(self.AnimeFolderLineEdit, 0, 0, 1, 1)

        self.AnimeFolderBrowse = QPushButton(self.GeneralSettingsTab)
        self.AnimeFolderBrowse.setObjectName(u"AnimeFolderBrowse")
        sizePolicy.setHeightForWidth(self.AnimeFolderBrowse.sizePolicy().hasHeightForWidth())
        self.AnimeFolderBrowse.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.AnimeFolderBrowse, 0, 1, 1, 1)

        self.AnimeFolderSettingsLabel = QLabel(self.GeneralSettingsTab)
        self.AnimeFolderSettingsLabel.setObjectName(u"AnimeFolderSettingsLabel")
        sizePolicy.setHeightForWidth(self.AnimeFolderSettingsLabel.sizePolicy().hasHeightForWidth())
        self.AnimeFolderSettingsLabel.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.AnimeFolderSettingsLabel, 0, 2, 1, 1)

        self.SubtitleLanguageLineEdit = QLineEdit(self.GeneralSettingsTab)
        self.SubtitleLanguageLineEdit.setObjectName(u"SubtitleLanguageLineEdit")
        sizePolicy.setHeightForWidth(self.SubtitleLanguageLineEdit.sizePolicy().hasHeightForWidth())
        self.SubtitleLanguageLineEdit.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.SubtitleLanguageLineEdit, 1, 0, 1, 2)

        self.SubtitleLanguageSettingsLabel = QLabel(self.GeneralSettingsTab)
        self.SubtitleLanguageSettingsLabel.setObjectName(u"SubtitleLanguageSettingsLabel")
        sizePolicy.setHeightForWidth(self.SubtitleLanguageSettingsLabel.sizePolicy().hasHeightForWidth())
        self.SubtitleLanguageSettingsLabel.setSizePolicy(sizePolicy)

        self.gridLayout_2.addWidget(self.SubtitleLanguageSettingsLabel, 1, 2, 1, 1)

        self.IgnoreSongsSignsCheckbox = QCheckBox(self.GeneralSettingsTab)
        self.IgnoreSongsSignsCheckbox.setObjectName(u"IgnoreSongsSignsCheckbox")

        self.gridLayout_2.addWidget(self.IgnoreSongsSignsCheckbox, 2, 0, 1, 3)

        self.SettingsTabWidget.addTab(self.GeneralSettingsTab, "")
        self.AnilistSettingsTab = QWidget()
        self.AnilistSettingsTab.setObjectName(u"AnilistSettingsTab")
        self.gridLayout_3 = QGridLayout(self.AnilistSettingsTab)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.AnilistInstructionsLabel = QLabel(self.AnilistSettingsTab)
        self.AnilistInstructionsLabel.setObjectName(u"AnilistInstructionsLabel")
        self.AnilistInstructionsLabel.setAlignment(Qt.AlignCenter)

        self.gridLayout_3.addWidget(self.AnilistInstructionsLabel, 0, 0, 1, 2)

        self.AnilistConnectedAccountLabel = QLabel(self.AnilistSettingsTab)
        self.AnilistConnectedAccountLabel.setObjectName(u"AnilistConnectedAccountLabel")
        self.AnilistConnectedAccountLabel.setAlignment(Qt.AlignCenter)

        self.gridLayout_3.addWidget(self.AnilistConnectedAccountLabel, 1, 0, 1, 2)

        self.AnilistConnect = QPushButton(self.AnilistSettingsTab)
        self.AnilistConnect.setObjectName(u"AnilistConnect")

        self.gridLayout_3.addWidget(self.AnilistConnect, 2, 0, 1, 1)

        self.AnilistCodeConfirm = QPushButton(self.AnilistSettingsTab)
        self.AnilistCodeConfirm.setObjectName(u"AnilistCodeConfirm")

        self.gridLayout_3.addWidget(self.AnilistCodeConfirm, 2, 1, 1, 1)

        self.AnilistCodeBox = QTextEdit(self.AnilistSettingsTab)
        self.AnilistCodeBox.setObjectName(u"AnilistCodeBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.AnilistCodeBox.sizePolicy().hasHeightForWidth())
        self.AnilistCodeBox.setSizePolicy(sizePolicy1)

        self.gridLayout_3.addWidget(self.AnilistCodeBox, 3, 0, 1, 2)

        self.SettingsTabWidget.addTab(self.AnilistSettingsTab, "")

        self.horizontalLayout.addWidget(self.SettingsTabWidget)


        self.retranslateUi(Settings)

        self.SettingsTabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(Settings)
    # setupUi

    def retranslateUi(self, Settings):
        Settings.setWindowTitle(QCoreApplication.translate("Settings", u"Form", None))
        self.AnimeFolderBrowse.setText(QCoreApplication.translate("Settings", u"Browse", None))
        self.AnimeFolderSettingsLabel.setText(QCoreApplication.translate("Settings", u"Anime Folder", None))
        self.SubtitleLanguageSettingsLabel.setText(QCoreApplication.translate("Settings", u"Subtitle Language", None))
        self.IgnoreSongsSignsCheckbox.setText(QCoreApplication.translate("Settings", u"Ignore Songs and Signs Subtitles", None))
        self.SettingsTabWidget.setTabText(self.SettingsTabWidget.indexOf(self.GeneralSettingsTab), QCoreApplication.translate("Settings", u"General", None))
        self.AnilistInstructionsLabel.setText(QCoreApplication.translate("Settings", u"<html><head/><body><p>To connect a new account, click Connect to anilist below</p><p>Login, then copy the code provided, enter it in the text box below</p><p>Then hit Confirm Code</p></body></html>", None))
        self.AnilistConnectedAccountLabel.setText(QCoreApplication.translate("Settings", u"Connected account: N/A", None))
        self.AnilistConnect.setText(QCoreApplication.translate("Settings", u"Connect to anilist", None))
        self.AnilistCodeConfirm.setText(QCoreApplication.translate("Settings", u"Confirm Code", None))
        self.SettingsTabWidget.setTabText(self.SettingsTabWidget.indexOf(self.AnilistSettingsTab), QCoreApplication.translate("Settings", u"Anilist", None))
    # retranslateUi

