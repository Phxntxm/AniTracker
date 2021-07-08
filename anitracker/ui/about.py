# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_About(object):
    def setupUi(self, About):
        if not About.objectName():
            About.setObjectName(u"About")
        About.resize(462, 300)
        About.setStyleSheet(u"background-color: rgb(68, 68, 68);\n"
"color: rgb(212, 212, 212);")
        self.label = QLabel(About)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(10, 10, 442, 241))
        self.label.setStyleSheet(u"")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setOpenExternalLinks(True)
        self.label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.VersionLabel = QLabel(About)
        self.VersionLabel.setObjectName(u"VersionLabel")
        self.VersionLabel.setGeometry(QRect(10, 270, 441, 20))
        self.VersionLabel.setAlignment(Qt.AlignCenter)

        self.retranslateUi(About)

        QMetaObject.connectSlotsByName(About)
    # setupUi

    def retranslateUi(self, About):
        About.setWindowTitle(QCoreApplication.translate("About", u"About AniTracker", None))
        self.label.setText(QCoreApplication.translate("About", u"<html><head/><body><p>AniTracker is a tool used to facilitate syncing of data<br/>between anime services, as well as tracking and playing files for your anime. Currently it is pretty barebones, but more and more features are planned as time goes on.</p><p><br/></p><p>Icons from: <a href=\"https://icons8.com/\"><span style=\" text-decoration: underline; color:#0000ff;\">https://icons8.com/</span></a></p></body></html>", None))
        self.VersionLabel.setText(QCoreApplication.translate("About", u"Version: 1", None))
    # retranslateUi

