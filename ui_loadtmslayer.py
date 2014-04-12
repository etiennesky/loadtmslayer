# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_loadtmslayer.ui'
#
# Created: Thu Apr 10 01:15:51 2014
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
        LoadTMSLayer.resize(419, 153)
        self.verticalLayout = QtGui.QVBoxLayout(LoadTMSLayer)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.checkBoxSetProjectCRS = QtGui.QCheckBox(LoadTMSLayer)
        self.checkBoxSetProjectCRS.setObjectName(_fromUtf8("checkBoxSetProjectCRS"))
        self.verticalLayout.addWidget(self.checkBoxSetProjectCRS)
        self.checkBoxUpdateScale = QtGui.QCheckBox(LoadTMSLayer)
        self.checkBoxUpdateScale.setObjectName(_fromUtf8("checkBoxUpdateScale"))
        self.verticalLayout.addWidget(self.checkBoxUpdateScale)
        self.checkBoxUseCache = QtGui.QCheckBox(LoadTMSLayer)
        self.checkBoxUseCache.setObjectName(_fromUtf8("checkBoxUseCache"))
        self.verticalLayout.addWidget(self.checkBoxUseCache)
        self.checkBoxClearCache = QtGui.QCheckBox(LoadTMSLayer)
        self.checkBoxClearCache.setObjectName(_fromUtf8("checkBoxClearCache"))
        self.verticalLayout.addWidget(self.checkBoxClearCache)
        self.buttonBox = QtGui.QDialogButtonBox(LoadTMSLayer)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(LoadTMSLayer)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), LoadTMSLayer.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), LoadTMSLayer.reject)
        QtCore.QMetaObject.connectSlotsByName(LoadTMSLayer)

    def retranslateUi(self, LoadTMSLayer):
        LoadTMSLayer.setWindowTitle(_translate("LoadTMSLayer", "LoadTMSLayer", None))
        self.checkBoxSetProjectCRS.setText(_translate("LoadTMSLayer", "Set project CRS to layer CRS when adding layer", None))
        self.checkBoxUpdateScale.setText(_translate("LoadTMSLayer", "Set canvas scale to closest matching tile scale when zooming", None))
        self.checkBoxUseCache.setText(_translate("LoadTMSLayer", "Enable local disk cache - allows for offline operation", None))
        self.checkBoxClearCache.setText(_translate("LoadTMSLayer", "Clear disk cache", None))

