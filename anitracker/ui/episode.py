# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'episode.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_animeEpisode(object):
    def setupUi(self, animeEpisode):
        if not animeEpisode.objectName():
            animeEpisode.setObjectName(u"animeEpisode")
        animeEpisode.resize(260, 178)
        animeEpisode.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"color: rgb(212, 212, 212);")
        self.verticalLayout = QVBoxLayout(animeEpisode)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.animeEpisodeLabel = QLabel(animeEpisode)
        self.animeEpisodeLabel.setObjectName(u"animeEpisodeLabel")
        self.animeEpisodeLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.animeEpisodeLabel)

        self.animeThumbnail = QLabel(animeEpisode)
        self.animeThumbnail.setObjectName(u"animeThumbnail")
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.animeThumbnail.sizePolicy().hasHeightForWidth())
        self.animeThumbnail.setSizePolicy(sizePolicy)
        self.animeThumbnail.setMaximumSize(QSize(240, 135))
        self.animeThumbnail.setAutoFillBackground(False)
        self.animeThumbnail.setTextFormat(Qt.MarkdownText)
        self.animeThumbnail.setPixmap(QPixmap(u"../../resources/1476044.jpg"))
        self.animeThumbnail.setScaledContents(True)

        self.verticalLayout.addWidget(self.animeThumbnail)


        self.retranslateUi(animeEpisode)

        QMetaObject.connectSlotsByName(animeEpisode)
    # setupUi

    def retranslateUi(self, animeEpisode):
        animeEpisode.setWindowTitle(QCoreApplication.translate("animeEpisode", u"Form", None))
        self.animeEpisodeLabel.setText(QCoreApplication.translate("animeEpisode", u"Episode 1", None))
        self.animeThumbnail.setText("")
    # retranslateUi

