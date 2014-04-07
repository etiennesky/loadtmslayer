# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_loadtmslayer.ui'
#
# Created: Mon Apr  7 11:53:18 2014
#      by: PyQt4 UI code generator 4.10
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_LoadTMSLayer(object):
    def setupUi(self, LoadTMSLayer):
        LoadTMSLayer.setObjectName(_fromUtf8("LoadTMSLayer"))
        LoadTMSLayer.resize(400, 300)
        self.buttonBox = QtGui.QDialogButtonBox(LoadTMSLayer)
        self.buttonBox.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))

        self.retranslateUi(LoadTMSLayer)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), LoadTMSLayer.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), LoadTMSLayer.reject)
        QtCore.QMetaObject.connectSlotsByName(LoadTMSLayer)

    def retranslateUi(self, LoadTMSLayer):
        LoadTMSLayer.setWindowTitle(_translate("LoadTMSLayer", "LoadTMSLayer", None))

