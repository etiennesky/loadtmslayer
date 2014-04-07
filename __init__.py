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
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    # load LoadTMSLayer class from file LoadTMSLayer
    from loadtmslayer import LoadTMSLayer
    return LoadTMSLayer(iface)
