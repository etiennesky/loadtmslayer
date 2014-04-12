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

from tilemapscalelevels import TileMapScaleLevels

import os.path, fnmatch, shutil, csv, re
from xml.dom.minidom import parse

from osgeo import gdal, ogr, osr
from osgeo.gdalconst import *


#-----------------------------------------------
# TODO fix scaleChanged when changing CRS
# TODO fix scaleChanged when using EPSG:4326 (if possible)
# TODO add options min/max zoom level, dpi, zoom UI
#-----------------------------------------------

class LoadTMSLayer:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

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
        self.layerAddActions = []
        self.scaleCalculator = TileMapScaleLevels(maxZoomlevel=18, minZoomlevel=0, dpi=self.iface.mainWindow().physicalDpiX())
        self.canvas.scaleChanged.connect(self.scaleChanged)

        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/loadtmslayer/icon.png"),
            u"Load TMS Layer settings", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        #self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"Load TMS Layer", self.action)

        # read defs in xml/xmldefs.csv
        xmldefs = dict()
        xmlfiles = []
        with open(os.path.join(self.xml_dir, 'xmldefs.csv'), 'rb') as csvfile:
            for row in csv.DictReader(csvfile, delimiter=',', ):
                if os.path.exists(os.path.join(self.xml_dir,row['file'])):
                    xmldefs[row['file']] = row
                    xmlfiles.append(row['file'])

        # list all files in xml dir
        for xmlfile in sorted(os.listdir(self.xml_dir)):
            if not fnmatch.fnmatch(xmlfile, '*.xml'):
                continue

            # if this file is not in xmldefs add an empty entry
            if not xmlfile in xmldefs:
                tmpdef = xmldefs[list(xmldefs.keys())[0]]
                xmldefs[xmlfile] = dict()
                for key in tmpdef.iterkeys():
                    xmldefs[xmlfile][key] = ''
                xmldefs[xmlfile]['file'] = xmlfile
                xmldefs[xmlfile]['category'] = '_user_'
                xmlfiles.append(xmlfile)

            # if display name empty get it from file name (strip file prefix and suffix)
            if not xmldefs[xmlfile]['name']:
                name = xmlfile
                if name.endswith('.xml'):
                    name = name[0:-4]
                if name.startswith('frmt_wms_'):
                    name = name[9:]
                elif name.startswith('frmt_twms_'):
                    name = name[10:]
                xmldefs[xmlfile]['name'] = name

        # add menu actions
        group = QActionGroup(self.iface.mainWindow())
        group.setExclusive(False)
        QObject.connect(group, SIGNAL("triggered( QAction* )"), self.addLayer)
        prevfile = ''
        # loop over all xml files
        for xmlfile in xmlfiles:
            name = xmldefs[xmlfile]['name']

            # add separator between categories
            if (prevfile != xmlfile) and (not prevfile or (xmldefs[prevfile]['category'] != xmldefs[xmlfile]['category'])):
                cat = xmldefs[xmlfile]['category']
                if cat == '_user_':
                    cat = ''
                action = QAction(cat, self.iface.mainWindow())
                action.setSeparator(True)
                self.layerAddActions.append(action)
                self.iface.addPluginToMenu(u"Load TMS Layer", action)
            
            # icon
            icon = os.path.join(self.xml_dir, xmldefs[xmlfile]['icon']) if xmlfile in xmldefs else None
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
        self.dlg.checkBoxUpdateScale.setChecked( s.value('plugins/loadtmslayer/updateScale', False, type=bool ) )
        self.dlg.checkBoxUseCache.setChecked( s.value('plugins/loadtmslayer/useCache', True, type=bool ) )
        self.dlg.checkBoxClearCache.setChecked( False )

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            s.setValue('plugins/loadtmslayer/setProjectCRS', self.dlg.checkBoxSetProjectCRS.isChecked())
            s.setValue('plugins/loadtmslayer/updateScale', self.dlg.checkBoxUpdateScale.isChecked())
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

        # read xml file
        if not os.path.exists(fileName):
            print('ERROR! file %s does not exits!' % fileName)
        doc = parse(fileName)
        node_gdal = doc.getElementsByTagName('GDAL_WMS')
        if not node_gdal:
            print('ERROR! file %s does not containt GDAL_WMS node!' % fileName)
            return

        # edit Cache node
        node_gdal = node_gdal[0]
        node_cache = node_gdal.getElementsByTagName('Cache')
        # remove Cache node so we ca either disable Cache or set the proper Cache options
        if node_cache:
            node_gdal.removeChild(node_cache[0])
        if s.value('plugins/loadtmslayer/useCache', True, type=bool ):
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            node_cache = doc.createElement('Cache')
            node_gdal.appendChild(node_cache)
            node_path = doc.createElement('Path')
            node_path.appendChild(doc.createTextNode(self.cache_dir))
            node_cache.appendChild(node_path)
                    
        # convert xml doc to a string
        uri = doc.toxml()
        uri = uri.replace('<?xml version="1.0" ?>','')
        uri = ' '.join(uri.split())

        if s.value('plugins/loadtmslayer/setProjectCRS', True, type=bool ):
            self.setProjectCRS(self.getRasterCRS(fileName))

        # load string as gdal layer
        #rlayer = QgsRasterLayer(fileName, layerName)
        rlayer = QgsRasterLayer(uri, layerName, 'gdal')
        if not rlayer.isValid():
            print('Layer failed to load: [%s]' %uri)
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
        mapCanvas = self.canvas
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

    # this code and TileMapScaleLevels taken from TileMapScalePlugin
    def scaleChanged(self, scale):
        #if self.dock.checkBoxIsActive.isChecked():
        if QSettings().value('plugins/loadtmslayer/updateScale', False, type=bool ):
            ## Disconnect to prevent infinite scaling loop
            self.canvas.scaleChanged.disconnect(self.scaleChanged)

            zoomlevel = self.scaleCalculator.getZoomlevel(scale)
            if zoomlevel:
                newScale = self.scaleCalculator.getScale(zoomlevel)
                if abs(scale-newScale)>0.00000001:
                    self.canvas.zoomScale(newScale)
                    #print('scaleChanged from %f to %f diff=%f' % (scale,newScale,scale-newScale))

            self.canvas.scaleChanged.connect(self.scaleChanged)

