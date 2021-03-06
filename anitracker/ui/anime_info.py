# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'anime_info.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_AnimeInfo(object):
    def setupUi(self, AnimeInfo):
        if not AnimeInfo.objectName():
            AnimeInfo.setObjectName(u"AnimeInfo")
        AnimeInfo.resize(751, 543)
        AnimeInfo.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"color: rgb(212, 212, 212);")
        self.gridLayout = QGridLayout(AnimeInfo)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget = QTabWidget(AnimeInfo)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setStyleSheet(u"QTabWidget::pane {\n"
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
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tab.sizePolicy().hasHeightForWidth())
        self.tab.setSizePolicy(sizePolicy)
        self.AnimeTitleLabelHeader = QLabel(self.tab)
        self.AnimeTitleLabelHeader.setObjectName(u"AnimeTitleLabelHeader")
        self.AnimeTitleLabelHeader.setGeometry(QRect(10, 18, 36, 18))
        self.AnimeTitleLabelHeader.setMaximumSize(QSize(16777215, 16777215))
        self.AnimeTitleLabelHeader.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.AnimeDescriptionLabelHeader = QLabel(self.tab)
        self.AnimeDescriptionLabelHeader.setObjectName(u"AnimeDescriptionLabelHeader")
        self.AnimeDescriptionLabelHeader.setGeometry(QRect(10, 89, 73, 16))
        self.AnimeDescriptionLabelHeader.setMaximumSize(QSize(16777215, 16777215))
        self.AnimeDescriptionLabelHeader.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.scrollArea = QScrollArea(self.tab)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setGeometry(QRect(90, 80, 631, 101))
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 629, 99))
        self.horizontalLayout = QHBoxLayout(self.scrollAreaWidgetContents)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.AnimeDescriptionLabel = QLabel(self.scrollAreaWidgetContents)
        self.AnimeDescriptionLabel.setObjectName(u"AnimeDescriptionLabel")
        self.AnimeDescriptionLabel.setEnabled(True)
        sizePolicy.setHeightForWidth(self.AnimeDescriptionLabel.sizePolicy().hasHeightForWidth())
        self.AnimeDescriptionLabel.setSizePolicy(sizePolicy)
        self.AnimeDescriptionLabel.setMaximumSize(QSize(16777215, 16777215))
        self.AnimeDescriptionLabel.setAutoFillBackground(False)
        self.AnimeDescriptionLabel.setFrameShape(QFrame.NoFrame)
        self.AnimeDescriptionLabel.setTextFormat(Qt.AutoText)
        self.AnimeDescriptionLabel.setScaledContents(False)
        self.AnimeDescriptionLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.AnimeDescriptionLabel.setWordWrap(True)
        self.AnimeDescriptionLabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.horizontalLayout.addWidget(self.AnimeDescriptionLabel)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.scrollArea_2 = QScrollArea(self.tab)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setGeometry(QRect(90, 9, 631, 61))
        sizePolicy.setHeightForWidth(self.scrollArea_2.sizePolicy().hasHeightForWidth())
        self.scrollArea_2.setSizePolicy(sizePolicy)
        self.scrollArea_2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_2.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, 0, 629, 59))
        self.horizontalLayout_2 = QHBoxLayout(self.scrollAreaWidgetContents_2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.AnimeTitleLabel = QLabel(self.scrollAreaWidgetContents_2)
        self.AnimeTitleLabel.setObjectName(u"AnimeTitleLabel")
        self.AnimeTitleLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.AnimeTitleLabel.setWordWrap(True)
        self.AnimeTitleLabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.horizontalLayout_2.addWidget(self.AnimeTitleLabel)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.AnimeEpisodesLabelHeader = QLabel(self.tab)
        self.AnimeEpisodesLabelHeader.setObjectName(u"AnimeEpisodesLabelHeader")
        self.AnimeEpisodesLabelHeader.setGeometry(QRect(10, 470, 58, 16))
        self.AnimeEpisodesLabelHeader.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.AnimeEpisodesLabel = QLabel(self.tab)
        self.AnimeEpisodesLabel.setObjectName(u"AnimeEpisodesLabel")
        self.AnimeEpisodesLabel.setGeometry(QRect(90, 470, 631, 16))
        self.AnimeEpisodesLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.AnimeEpisodesLabel.setWordWrap(True)
        self.AnimeEpisodesLabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)
        self.AnimeGenresLabelHeader = QLabel(self.tab)
        self.AnimeGenresLabelHeader.setObjectName(u"AnimeGenresLabelHeader")
        self.AnimeGenresLabelHeader.setGeometry(QRect(10, 199, 57, 15))
        self.AnimeStudioLabelHeader = QLabel(self.tab)
        self.AnimeStudioLabelHeader.setObjectName(u"AnimeStudioLabelHeader")
        self.AnimeStudioLabelHeader.setGeometry(QRect(10, 410, 57, 15))
        self.AnimeSeasonLabelHeader = QLabel(self.tab)
        self.AnimeSeasonLabelHeader.setObjectName(u"AnimeSeasonLabelHeader")
        self.AnimeSeasonLabelHeader.setGeometry(QRect(10, 430, 57, 15))
        self.AnimeAverageScoreLabelHeader = QLabel(self.tab)
        self.AnimeAverageScoreLabelHeader.setObjectName(u"AnimeAverageScoreLabelHeader")
        self.AnimeAverageScoreLabelHeader.setGeometry(QRect(10, 450, 57, 15))
        self.AnimeStudioLabel = QLabel(self.tab)
        self.AnimeStudioLabel.setObjectName(u"AnimeStudioLabel")
        self.AnimeStudioLabel.setGeometry(QRect(90, 410, 631, 16))
        self.AnimeSeasonLabel = QLabel(self.tab)
        self.AnimeSeasonLabel.setObjectName(u"AnimeSeasonLabel")
        self.AnimeSeasonLabel.setGeometry(QRect(90, 430, 631, 16))
        self.AnimeAverageScoreLabel = QLabel(self.tab)
        self.AnimeAverageScoreLabel.setObjectName(u"AnimeAverageScoreLabel")
        self.AnimeAverageScoreLabel.setGeometry(QRect(90, 450, 631, 16))
        self.AnimeTagsLabelHeader = QLabel(self.tab)
        self.AnimeTagsLabelHeader.setObjectName(u"AnimeTagsLabelHeader")
        self.AnimeTagsLabelHeader.setGeometry(QRect(10, 299, 57, 15))
        self.scrollArea_3 = QScrollArea(self.tab)
        self.scrollArea_3.setObjectName(u"scrollArea_3")
        self.scrollArea_3.setGeometry(QRect(90, 190, 631, 91))
        self.scrollArea_3.setLineWidth(0)
        self.scrollArea_3.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_3.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_3.setWidgetResizable(True)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 629, 89))
        self.horizontalLayout_3 = QHBoxLayout(self.scrollAreaWidgetContents_3)
        self.horizontalLayout_3.setSpacing(6)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(9, 9, 9, 9)
        self.AnimeGenresLabel = QLabel(self.scrollAreaWidgetContents_3)
        self.AnimeGenresLabel.setObjectName(u"AnimeGenresLabel")
        self.AnimeGenresLabel.setLineWidth(1)
        self.AnimeGenresLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.AnimeGenresLabel.setWordWrap(True)
        self.AnimeGenresLabel.setIndent(-1)
        self.AnimeGenresLabel.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.horizontalLayout_3.addWidget(self.AnimeGenresLabel)

        self.scrollArea_3.setWidget(self.scrollAreaWidgetContents_3)
        self.scrollArea_4 = QScrollArea(self.tab)
        self.scrollArea_4.setObjectName(u"scrollArea_4")
        self.scrollArea_4.setGeometry(QRect(90, 290, 631, 111))
        self.scrollArea_4.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_4.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea_4.setWidgetResizable(True)
        self.scrollAreaWidgetContents_4 = QWidget()
        self.scrollAreaWidgetContents_4.setObjectName(u"scrollAreaWidgetContents_4")
        self.scrollAreaWidgetContents_4.setGeometry(QRect(0, 0, 629, 109))
        self.horizontalLayout_4 = QHBoxLayout(self.scrollAreaWidgetContents_4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.AnimeTagsLabel = QLabel(self.scrollAreaWidgetContents_4)
        self.AnimeTagsLabel.setObjectName(u"AnimeTagsLabel")
        self.AnimeTagsLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.horizontalLayout_4.addWidget(self.AnimeTagsLabel)

        self.scrollArea_4.setWidget(self.scrollAreaWidgetContents_4)
        self.AnimeUserScoreLabel = QLabel(self.tab)
        self.AnimeUserScoreLabel.setObjectName(u"AnimeUserScoreLabel")
        self.AnimeUserScoreLabel.setGeometry(QRect(300, 410, 57, 15))
        self.AnimeNotesLabel = QLabel(self.tab)
        self.AnimeNotesLabel.setObjectName(u"AnimeNotesLabel")
        self.AnimeNotesLabel.setGeometry(QRect(300, 440, 57, 15))
        self.AnimeNotes = QTextEdit(self.tab)
        self.AnimeNotes.setObjectName(u"AnimeNotes")
        self.AnimeNotes.setGeometry(QRect(350, 440, 371, 41))
        self.AnimeUpdateButton = QPushButton(self.tab)
        self.AnimeUpdateButton.setObjectName(u"AnimeUpdateButton")
        self.AnimeUpdateButton.setGeometry(QRect(640, 410, 80, 23))
        self.AnimeUserScore = QDoubleSpinBox(self.tab)
        self.AnimeUserScore.setObjectName(u"AnimeUserScore")
        self.AnimeUserScore.setGeometry(QRect(350, 410, 62, 24))
        self.AnimeUserScore.setDecimals(1)
        self.AnimeUserScore.setSingleStep(0.500000000000000)
        self.AnimeUpdateSuccess = QLabel(self.tab)
        self.AnimeUpdateSuccess.setObjectName(u"AnimeUpdateSuccess")
        self.AnimeUpdateSuccess.setEnabled(True)
        self.AnimeUpdateSuccess.setGeometry(QRect(570, 414, 57, 15))
        self.AnimeUpdateSuccess.setStyleSheet(u"color: rgb(71, 255, 15);")
        self.tabWidget.addTab(self.tab, "")

        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)


        self.retranslateUi(AnimeInfo)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(AnimeInfo)
    # setupUi

    def retranslateUi(self, AnimeInfo):
        AnimeInfo.setWindowTitle(QCoreApplication.translate("AnimeInfo", u"Anime Settings", None))
        self.AnimeTitleLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Titles:", None))
        self.AnimeDescriptionLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Description:", None))
        self.AnimeDescriptionLabel.setText(QCoreApplication.translate("AnimeInfo", u"Description", None))
        self.AnimeTitleLabel.setText(QCoreApplication.translate("AnimeInfo", u"Title", None))
        self.AnimeEpisodesLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Episodes:", None))
        self.AnimeEpisodesLabel.setText(QCoreApplication.translate("AnimeInfo", u"0", None))
        self.AnimeGenresLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Genres:", None))
        self.AnimeStudioLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Studio:", None))
        self.AnimeSeasonLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Season:", None))
        self.AnimeAverageScoreLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Score:", None))
        self.AnimeStudioLabel.setText(QCoreApplication.translate("AnimeInfo", u"Studio", None))
        self.AnimeSeasonLabel.setText(QCoreApplication.translate("AnimeInfo", u"Season", None))
        self.AnimeAverageScoreLabel.setText(QCoreApplication.translate("AnimeInfo", u"Score", None))
        self.AnimeTagsLabelHeader.setText(QCoreApplication.translate("AnimeInfo", u"Tags:", None))
        self.AnimeGenresLabel.setText(QCoreApplication.translate("AnimeInfo", u"Genres", None))
        self.AnimeTagsLabel.setText(QCoreApplication.translate("AnimeInfo", u"Tags", None))
        self.AnimeUserScoreLabel.setText(QCoreApplication.translate("AnimeInfo", u"Score:", None))
        self.AnimeNotesLabel.setText(QCoreApplication.translate("AnimeInfo", u"Notes:", None))
        self.AnimeNotes.setHtml(QCoreApplication.translate("AnimeInfo", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Sans Serif'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Notes</p></body></html>", None))
        self.AnimeUpdateButton.setText(QCoreApplication.translate("AnimeInfo", u"Update", None))
        self.AnimeUpdateSuccess.setText(QCoreApplication.translate("AnimeInfo", u"Updated!", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("AnimeInfo", u"Anime Information", None))
    # retranslateUi

