# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.1.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_About(object):
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName(u"About")
        About.resize(426, 300)
        About.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"color: rgb(212, 212, 212);")
        self.verticalLayout = QVBoxLayout(About)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(About)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setTextInteractionFlags(Qt.TextBrowserInteraction)

        self.verticalLayout.addWidget(self.label)

        self.VersionLabel = QLabel(About)
        self.VersionLabel.setObjectName(u"VersionLabel")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.VersionLabel.sizePolicy().hasHeightForWidth())
        self.VersionLabel.setSizePolicy(sizePolicy)
        self.VersionLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.VersionLabel)


        self.retranslateUi(About)

        QMetaObject.connectSlotsByName(About)
    # setupUi

    def retranslateUi(self, About):
        About.setWindowTitle(QCoreApplication.translate("About", u"About AniTracker", None))
        self.label.setText(QCoreApplication.translate("About", u"<html><head/><body><p>AniTracker is a tool used to facilitate syncing of data<br/>between anime services, as well as tracking and playing files</p><p>for your anime. Currently it is pretty barebones, but more and more</p><p>features are planned as time goes on.</p><p><br/></p><p>Icons from: <a href=\"https://icons8.com/\"><span style=\" text-decoration: underline; color:#0000ff;\">https://icons8.com/</span></a></p></body></html>", None))
        self.VersionLabel.setText(QCoreApplication.translate("About", u"Version: ", None))
    # retranslateUi

