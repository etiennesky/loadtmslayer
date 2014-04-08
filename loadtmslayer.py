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

import os.path, fnmatch, shutil
from xml.dom.minidom import parse

from osgeo import gdal, ogr, osr
from osgeo.gdalconst import *

class LoadTMSLayer:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.xml_dir = os.path.join(self.plugin_dir, 'xml')
        self.cache_dir = os.path.join(QgsApplication.qgisSettingsDirPath(), 'cache', 'gdalwmscache')

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
            u"Load TMS Layer settings", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        #self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"Load TMS Layer", self.action)

        # contruct display name / xmlfile list
        names = dict()
        for xmlfile in sorted(os.listdir(self.xml_dir)):
            if not fnmatch.fnmatch(xmlfile, '*.xml'):
                continue

            # display name
            # first try to get name as a comment in file (e.g. <!-- QGIS Name -->)
            name = None
            look = False
            for line in open(os.path.join(self.xml_dir,xmlfile)):              
                line = line.strip()
                if (look):
                    if line.startswith('<!-- QGIS'):
                        name = line[9:-3].strip()
                        break 
                    if line.startswith('<Service'):
                        break
                elif line.startswith('<GDAL_WMS>'):
                    look = True
            # if not found strip file prefix and suffix
            if not name:
                name = xmlfile
                if name.endswith('.xml'):
                    name = name[0:-4]
                if name.startswith('frmt_wms_'):
                    name = name[9:]
                elif name.startswith('frmt_twms_'):
                    name = name[10:]
            
            names[name] = xmlfile

        # sort names alphabetically, OSM/Google first
        nameKeys = sorted(names.iterkeys(), key=str.lower)
        nameKeys1 = []
        nameKeys2 = []
        for name in nameKeys:
            xmlfile = names[name]
            if xmlfile.startswith('frmt_wms_googlemaps') or xmlfile.startswith('frmt_wms_openstreetmap'):
                nameKeys1.append(name)
            else:
                nameKeys2.append(name)
        nameKeys = nameKeys1 + nameKeys2

        # loop over all xml files
        self.layerAddActions = []
        action = QAction('', self.iface.mainWindow())
        action.setSeparator(True)
        self.layerAddActions.append(action)
        self.iface.addPluginToMenu(u"Load TMS Layer", action)
        group = QActionGroup(self.iface.mainWindow())
        group.setExclusive(False)
        QObject.connect(group, SIGNAL("triggered( QAction* )"), self.addLayer)
        prevfile = None
        for name in nameKeys:
            xmlfile = names[name]

            # add separator after google/osm
            if prevfile is None:
                prevfile = xmlfile
            if ( prevfile.startswith('frmt_wms_googlemaps') and not xmlfile.startswith('frmt_wms_googlemaps') ) \
                    or ( prevfile.startswith('frmt_wms_openstreetmap') and not xmlfile.startswith('frmt_wms_openstreetmap') ):
                action = QAction('', self.iface.mainWindow())
                action.setSeparator(True)
                self.layerAddActions.append(action)
                self.iface.addPluginToMenu(u"Load TMS Layer", action)
            
            # icon
            icon = None
            if xmlfile.startswith('frmt_wms_googlemaps'):
                icon = 'google_icon.png'
            elif xmlfile.startswith('frmt_wms_openstreetmap'):
                icon = 'osm_icon.png'
            if icon:
                icon = os.path.join(self.plugin_dir, icon)
            actionName = 'Add %s layer' % name
            if icon and os.path.isfile(icon):
                action = QAction(QIcon(icon), actionName, group)
            else:
                action = QAction(actionName, group)
            action.setData([self.xml_dir, xmlfile, name])
            self.layerAddActions.append(action)
            # Add toolbar button and menu item
            self.iface.addPluginToMenu(u"Load TMS Layer", action)

            prevfile = xmlfile


    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"Load TMS Layer", self.action)
        #self.iface.removeToolBarIcon(self.action)
        for action in self.layerAddActions:
            self.iface.removePluginMenu(u"Load TMS Layer", action)


    # run method that performs all the real work
    def run(self):
        s = QSettings()
        # set dialog options
        self.dlg.checkBoxSetProjectCRS.setChecked( s.value('plugins/loadtmslayer/setProjectCRS', True, type=bool ) )
        self.dlg.checkBoxUseCache.setChecked( s.value('plugins/loadtmslayer/useCache', True, type=bool ) )
        self.dlg.checkBoxClearCache.setChecked( False )

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            s.setValue('plugins/loadtmslayer/setProjectCRS', self.dlg.checkBoxSetProjectCRS.isChecked())
            s.setValue('plugins/loadtmslayer/useCache', self.dlg.checkBoxUseCache.isChecked())
            if self.dlg.checkBoxClearCache.isChecked():
                reply = QMessageBox.question(self.iface.mainWindow(), 'Load TMS Layer', 
                                             'Are you sure you wish to delete directory %s ?' % self.cache_dir,
                                             QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes: 
                    print('deleting cache in %s' % self.cache_dir)
                    shutil.rmtree(self.cache_dir)
            pass


    def addLayer(self, action):
        s = QSettings()
        d = action.data()

        layerPath = d[0]
        fileName = d[1]
        layerName = d[2]
        fileName = os.path.join(layerPath, fileName)

        # if user requests cache use, setup xml file proper that setting and use that
        fileTemp = os.path.join(self.cache_dir, os.path.basename(fileName))
        if s.value('plugins/loadtmslayer/useCache', True, type=bool ):
            # if file exists don't write it again
            if not os.path.exists(fileTemp):
                doc = parse(fileName)
                node_gdal = doc.getElementsByTagName('GDAL_WMS')
                if node_gdal:
                    node_gdal = node_gdal[0]
                    node_cache = node_gdal.getElementsByTagName('Cache')
                    if node_cache:
                        node_gdal.removeChild(node_cache[0])
                    node_cache = doc.createElement('Cache')
                    node_gdal.appendChild(doc.createTextNode('    '))
                    node_gdal.appendChild(doc.createComment('document modified by QGIS loadtmslayer plugin'))
                    node_gdal.appendChild(doc.createTextNode('\n    '))
                    node_gdal.appendChild(node_cache)
                    node_path = doc.createElement('Path')
                    node_path.appendChild(doc.createTextNode(self.cache_dir))
                    node_cache.appendChild(node_path)
                    node_gdal.appendChild(doc.createTextNode('\n'))
                    
                    out = doc.toxml()
                    out = out.replace('<?xml version="1.0" ?>','') + '\n'

                    if not os.path.exists(self.cache_dir):
                        os.makedirs(self.cache_dir)
            
                    print('writing fileTemp %s' % fileTemp)
                    with open(fileTemp, 'w') as f:
                        f.write(out)
            fileName = os.path.join(layerPath, fileTemp)
                    
        if not os.path.exists(fileName):
            print('ERROR! file %s does not exits!' % fileName)
            return

        if s.value('plugins/loadtmslayer/setProjectCRS', True, type=bool ):
            self.setProjectCRS(self.getRasterCRS(fileName))

        rlayer = QgsRasterLayer(fileName, layerName)
        if not rlayer.isValid():
            print 'Layer failed to load!'
            return
        QgsMapLayerRegistry.instance().addMapLayer(rlayer)

        
    # get raster CRS if possible
    def getRasterCRS(self, fileName):
        ds = gdal.Open(fileName)
        if ds is None:
            return None
        proj = ds.GetProjectionRef()
        if proj is None:
            return None
        crs = QgsCoordinateReferenceSystem()
        if not crs.createFromWkt(proj):
            return None
        return crs


    # change project CRS and OTF reprojection
    # code taken from OpenLayers plugin
    def setProjectCRS(self, crs):
        if not crs:
            return
        mapCanvas = self.iface.mapCanvas()
        # On the fly
        if QGis.QGIS_VERSION_INT >= 20300:
            mapCanvas.mapSettings().setCrsTransformEnabled(True) 
        else:
            mapCanvas.mapRenderer().setProjectionsEnabled(True) 
        # CRS
        if QGis.QGIS_VERSION_INT >= 20300:
            theCRS = mapCanvas.mapSettings().destinationCrs()
        elif QGis.QGIS_VERSION_INT >= 10900:
            theCRS = mapCanvas.mapRenderer().destinationCrs()
        else:
            theCRS = mapCanvas.mapRenderer().destinationSrs()
        if theCRS != crs:
            if QGis.QGIS_VERSION_INT >= 20300:
                mapCanvas.setDestinationCrs(crs)
            elif QGis.QGIS_VERSION_INT >= 10900:
                mapCanvas.mapRenderer().setDestinationCrs(crs)
            else:
                mapCanvas.mapRenderer().setDestinationSrs(crs)
            mapCanvas.setMapUnits(crs.mapUnits())

