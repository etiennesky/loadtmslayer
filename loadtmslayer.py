# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LoadTMSLayer
                                 A QGIS plugin
 This plugin load a TMS layer using the GDAL TMS mini-driver
                              -------------------
        begin                : 2014-04-07
        copyright            : (C) 2014 by Etienne Tourigny
        email                : etourigny.dev@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from loadtmslayerdialog import LoadTMSLayerDialog

import os.path
#import glob
import fnmatch, re

class LoadTMSLayer:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'loadtmslayer_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = LoadTMSLayerDialog()

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/loadtmslayer/icon.png"),
            u"Load TMS Layer", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        #self.iface.addToolBarIcon(self.action)
        #self.iface.addPluginToMenu(u"Load TMS Layer", self.action)

        self.xmlDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'xml')
        #print(self.xmlDir)
        #print(os.listdir(self.xmlDir))
        group = QActionGroup(self.iface.mainWindow())
        group.setExclusive(False)
        QObject.connect(group, SIGNAL("triggered( QAction* )"), self.addLayer)

        self.layerAddActions = []
        for xmlfile in sorted(os.listdir(self.xmlDir)):
            if not fnmatch.fnmatch(xmlfile, '*.xml'):
                continue
            name = xmlfile
            if name.endswith('.xml'):
                name = name[0:-4]
            if name.startswith('frmt_wms_'):
                name = name[9:]
            elif name.startswith('frmt_twms_'):
                name = name[10:]

            action = QAction(name, group)
            action.setData([xmlfile,self.xmlDir])
            self.layerAddActions.append(action)
            # Add toolbar button and menu item
            self.iface.addPluginToMenu(u"Load TMS Layer", action)

    def unload(self):
        # Remove the plugin menu item and icon
        #self.iface.removePluginMenu(u"Load TMS Layer", self.action)
        #self.iface.removeToolBarIcon(self.action)
        for action in self.layerAddActions:
            self.iface.removePluginMenu(u"Load TMS Layer", action)

    # run method that performs all the real work
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code)
            pass


    def addLayer(self, action):
        d = action.data()
        fileName = os.path.join(d[1], d[0])
        fileInfo = QFileInfo(fileName)
        if not fileInfo.exists():
            print('ERROR! file %s does not exits!' % fileName)
            return
        baseName = fileInfo.baseName()
        rlayer = QgsRasterLayer(fileName, baseName)
        if not rlayer.isValid():
            print 'Layer failed to load!'
            return
        QgsMapLayerRegistry.instance().addMapLayer(rlayer)
